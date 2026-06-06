# BloodBridge AI — Deep-Dive Feature & Architecture Document

> NGO edition (Blood Warriors). Matching today = **ABO+Rh + Geography + Engagement**.
> Antigen phenotyping (Kell/Duffy/Kidd/MNS) is **Phase 2** (columns exist, flagged unused).
> This document explains every feature in depth — how the agents work, how the AI is
> autonomous, and the end-to-end data flows.

---

## 0. How "Agentic AI" Actually Works Here (the foundation)

BloodBridge is not a chatbot with if/else. It is an **autonomous multi-agent system** built on
**LangGraph** — a stateful graph where each node is an independent "agent" that reads and writes
a shared, typed `AgentState`. The graph itself decides what runs next based on state, not a fixed
script. That is what makes it *agentic*.

### The three things that make it autonomous

1. **Shared typed state (`AgentState`)** — one object flows through all 14 nodes. Each agent reads
   what it needs, does its job, and writes results back. No agent needs to know who runs next.
2. **Conditional routing (the graph decides)** — `route_after_neo4j_match()` and
   `route_after_monitor()` are pure functions that look at the state and return the next node name.
   Example: if `confirmed >= target` → `outcome`; if `stale_nodes` exist → `voice`; if `declined`
   → `repair`. The system self-navigates.
3. **Self-driving loops + scheduled triggers** — the `chain_monitor` node loops back on itself via
   APScheduler every 5 minutes with zero human input. It re-enters the graph, re-evaluates, and
   repairs broken chains automatically. This is the "no human in the loop" property.

### LLM tiering (Amazon Bedrock via `core/llm_provider.py`)
| Tier | Model | Used by |
|---|---|---|
| Fast / high-volume | **Nova Lite** | Telegram replies, outreach message generation |
| Reasoning | **Claude 3.5 Haiku** | planner, conflict resolver, demand-forecast insight, failure classification |
| Quality | **Claude 3.5 Sonnet** | impact-story generation |

Every agent imports `get_fast_llm()` / `get_reasoning_llm()` / `get_quality_llm()` — swapping a
provider is a one-file change. The agents themselves never know which model they use.

---

# 🩸 PILLAR A — SMART MATCHING

## Feature 1 — Geo Radius-Tier Matching (`services/matching_engine.py`)

### What it does
Finds compatible donors by searching outward in 3 concentric geographic rings, instead of a single
flat "same city" query.

### How it works (in depth)
1. **Fetch patient locations** — a patient can register 1–5 locations (`patient_locations`). The
   matcher considers ALL of them and uses each donor's *best* (smallest) distance across them.
2. **Geohash bucketing** — every donor/patient has a precision-6 geohash (~1.2km cell). This
   replaces fragile string matching ("Hyderabad" vs "hyderabad" vs "Secunderabad") with coordinate
   math.
3. **Haversine ring classification** — for each candidate donor, compute great-circle distance:
   - Ring 1 (R1): ≤ 5 km — neighbourhood
   - Ring 2 (R2): ≤ 15 km — city zone
   - Ring 3 (R3): ≤ 30 km — wide net
4. **Expand-only-when-needed** — search R1 first. Only widen to R2, then R3, if the eligible pool
   is below the target chain size (default 8). This keeps donors close to the patient.
5. **Wide-net separation** — donors found ONLY in R3 are put on a separate `wide_net` list and
   carry a distance penalty in scoring. They are last-resort backups, not first responders.

### Eligibility filters applied inside the matcher
- 56-day donation gap (iron recovery) — skipped if too recent
- `medical_hold` flag — skipped if on hold
- ABO+Rh compatibility (NGO model — no antigen phenotyping yet)

### Data flow
```
patient_id
   ↓ fetch patient + patient_locations (1–5)
   ↓ compute compatible donor blood types (ABO+Rh matrix)
   ↓ fetch active donors of those types
   ↓ for each donor:
        best_distance = min(haversine(donor, each patient location))
        if best_distance > 30km: skip
        ring = 1 if ≤5  / 2 if ≤15 / 3 if ≤30
   ↓ score every donor (Feature 2)
   ↓ split → primary (ring 1–2) + wide_net (ring 3)
   ↓ backfill primary from wide_net if short of target
RETURN { primary: [...], wide_net: [...] }   each donor carries ring + match_score
```

### Solves
Finds the nearest compatible donors first; only widens the net when necessary; keeps far donors
as clearly-labelled backups.

---

## Feature 2 — Weighted Multi-Criteria Scoring (`WEIGHTS` dict)

### What it does
Ranks donors with a transparent, tunable formula — "weighted greedy done right" — instead of a
naive sort.

### The formula
```
score =  w1 · blood_match            (ABO+Rh exact = 1.0, partial = 0.8)
       + w2 · proximity              (1 − distance/30)
       + w3 · engagement             (real NGO signals, see below)
       + w4 · eligibility_freshness  (peaks at 56 days post-donation, decays to 365)
       + w5 · (1 − churn_score)      (avoid donors likely to drop)
       + w6 · bridge_bonus           (donors already committed to THIS patient's bridge)
       − w7 · radius_penalty         (ring 3 penalised, ring 2 half, ring 1 none)
```

### Engagement score (real NGO signals from the Blood Warriors dataset)
```
engagement = 0.4 · ratio_score        (calls_to_donations_ratio inverted — fewer calls = better)
           + 0.4 · response_rate      (confirmed / alerted history)
           + 0.2 · donation_score     (donations_till_date, capped at 20)
```

### Why it matters
The weights live in a single `WEIGHTS` dict at the top of the file, so the NGO can tune behaviour
(e.g. prioritise proximity in dense cities, engagement in sparse ones) without touching logic.
**Bridge Donors** committed to a patient get a fixed bonus — they are the natural first responders.

### Solves
Prioritises the *right* donor (close, reliable, engaged, unlikely to churn), not just any
compatible one.

---

## Feature 3 — Hungarian Multi-Patient Optimizer (`services/assignment_optimizer.py`)

### What it does
When 2+ active patients compete for the same nearby donors, it computes the **globally optimal**
donor→patient assignment — not a greedy first-come grab.

### The problem it fixes
Greedy matching: Patient A grabs the best donor, Patient B grabs the next, and Patient C (who only
had those two as options) gets nothing. Globally this is sub-optimal.

### How it works (in depth)
1. **Build a cost matrix** — rows = patients, cols = the union of all candidate donors.
   `cost[i][j] = 1 − match_score(donor j for patient i)`. Donors out of a patient's range get a
   prohibitive cost (1000) so they're never assigned there.
2. **Solve with the Hungarian algorithm** — `scipy.optimize.linear_sum_assignment` (Kuhn–Munkres)
   finds the minimum-total-cost perfect assignment in polynomial time.
3. **Round-robin for N donors per patient** — each patient needs up to 8 donors, so it solves in
   rounds: assign 1 best donor per patient, remove assigned donors, repeat until chains fill.
4. **Safe fallback** — if scipy is unavailable or there's only 1 patient, it falls back to greedy
   ranking. The single-emergency pipeline is never blocked by the optimizer.

### Where it runs
Exposed at `GET/POST /api/admin/optimize-assignments` as a **read-only preview** for coordinators —
it shows the optimal plan across all IN_PROGRESS requests without auto-alerting. Logged to
`agent_traces`.

### Solves
The PRD's "conflict resolver" gap — the genuinely advanced, mathematically optimal piece.

---

## Feature 4 — Multi-Location Model (`schema_v4_locations.sql` + M4 APIs + M6 UI)

### What it does
Patients register 1–5 search locations (home, work, hostel, hospital). Donors register N backup
areas they can travel to.

### Schema
- `patient_locations` — location_id, patient_id, label, lat, lng, geohash(6), is_primary,
  priority_order (1–5, CHECK-constrained)
- `donor_locations` — same shape, soft-limit 10, no priority cap
- `donors` + `patients` get `lat`, `lng`, `geohash` columns (these were missing before — geo
  matching was silently broken)
- `blood_chains` gains `ring` and `match_score` columns so the UI can show why a donor was chosen

### APIs (M4)
- Patient: `POST/GET/DELETE/PATCH /api/patients/{id}/locations` (max 5, can't delete last)
- Donor: `POST/GET/DELETE/PATCH /api/donors/{id}/locations` (soft-limit 10; updating a primary
  rebuilds the donor's geo + triggers graph edge rebuild)

### UI (M6 — `LocationManager.tsx`)
- Card on Patient Dashboard and Donor Portal: add/list/delete locations, set-primary, geohash
  shown, animated list (framer-motion)

### Solves
Brittle city-string matching; lets the matcher search from any of a patient's locations and
consider donors who can reach any of them.

---

# 🔗 PILLAR B — COORDINATION

## Feature 5 — 14-Node LangGraph Pipeline (`agents/graph.py`)

### The graph
```
intake
  → eligibility
  → [antigen_score  ∥  urgency_score]   (parallel branches)
  → neo4j_match
  → (conflict?)  → planner
  → outreach
  → monitor ──→ (complete) → outcome → gamification → END
       │
       ├──→ (stale)     → voice    → back to monitor
       ├──→ (declined)  → repair   → back to outreach
       └──→ (exhausted) → inventory → outcome
```

### Each node = one autonomous agent

| Node | Agent role | Key action |
|---|---|---|
| **intake** | Request parser | Fetch patient + context, init AgentState, create request row |
| **eligibility** | Rule engine | WHO/NBTC filter: 56-day gap, medical hold, active, consent |
| **antigen_score** | Compatibility scorer | ABO+Rh now; antigen weights ready for Phase 2 |
| **urgency_score** | XGBoost model | Score patient urgency 0–10 → CRITICAL/HIGH/ROUTINE; ntfy on CRITICAL |
| **neo4j_match** | Matching engine | Calls `matching_engine.rank_donors()` → builds chain, ring + score |
| **conflict** | Gemini/Claude reasoner | Resolves 2-patients-1-donor; Hungarian preview available |
| **planner** | Strategy LLM | Picks channel + tone + timing per donor (reads protocol stats) |
| **outreach** | Parallel dispatcher | Groq/Nova generates message → Telegram send to each donor |
| **monitor** | Scheduled watcher | Every 5 min: detect stale/declined, route to repair/voice |
| **repair** | Chain fixer | Pull next-best donor from backup pool, re-alert |
| **voice** | Voice agent | Bolna.ai call in donor's language; SMS fallback |
| **inventory** | Fallback agent | e-RaktKosh blood bank lookup when chain exhausted |
| **gamification** | Reward engine | Badge checks + leaderboard update |
| **outcome** | Closer | Records result, updates donor stats, schedules impact story |

### Why this is autonomous
- **Parallelism:** antigen + urgency scoring run simultaneously (graph fan-out/fan-in).
- **Self-routing:** `route_after_monitor()` decides repair vs voice vs complete from state alone.
- **Self-looping:** monitor re-enters itself on a timer until success or escalation.
- **No human required** for the happy path; humans only get pulled in via ntfy on escalation.

### Solves
End-to-end autonomous coordination — the core differentiator.

---

## Feature 6 — Chain Monitor + Auto-Repair (`agents/monitor.py`, `agents/repair.py`)

### Flow
```
APScheduler (every 5 min)
   ↓ query chains: status=ALERTED and alerted_at > 7 min ago  → STALE
   ↓ query chains: status=DECLINED / UNREACHABLE              → BROKEN
   ↓ STALE  → voice agent (escalate channel)
   ↓ BROKEN → repair agent:
        find next-best donor (prefer wide_net backup pool)
        mark old position DECLINED in Neo4j + Supabase
        alert replacement → status ALERTED
        WebSocket: old node RED, new node ORANGE
   ↓ 3 consecutive fails → inventory agent → escalate (ntfy staff)
```

### Solves
Chains of 8–10 donors no longer collapse silently — the system self-heals in seconds.

---

## Feature 7 — Donor Health Self-Update + Auto-Repair (M5)

### What it does
A donor can declare themselves temporarily unfit (illness, hospitalization, checkup) and the system
instantly removes them from active chains and repairs.

### Flow (in depth)
```
Donor → "I'm sick this week" (Telegram)  OR  Donor Portal "Report Unavailable"
   ↓ Telegram tool report_medical_hold  →  routes through M5 endpoint
   ↓ POST /api/donors/{id}/health-status { available:false, reason, hold_until }
   ↓ set medical_hold=true, is_active=false, log to donor_health_log
   ↓ find this donor's ACTIVE chain rows (ALERTED/PENDING/CONFIRMED)
        for each: mark DECLINED ("donor_medical_hold")
                  update Neo4j edge
                  trigger chain_repair_agent (pull next-best backup)
   ↓ notify staff via ntfy + Telegram ("Donor X unavailable, auto-repaired with Donor Y")
   ↓ WebSocket broadcast "donor_unavailable" → dashboards update live
   ↓ DPDP-safe: patient sees anonymized "your chain was updated" (no medical detail)
```

### Solves
Real-world donor unavailability + replacement, with staff and patient kept informed in real time.

---

## Feature 8 — AI Voice Calling + SMS Fallback (`agents/voice.py`, B3)

### Flow
```
stale donor (no Telegram response in 7 min)
   ↓ Claude/Gemini generates 30-sec script in donor's language
   ↓ Bolna.ai outbound call (Sarvam AI Indian voice)
   ↓ TRAI safe hours enforced (8 AM – 9 PM IST)
   ↓ donor speaks → keyword NLU (haan/nahi/kal) → chain update
   ↓ IF no answer / webhook lost (>12 min, attempt 2):
        Twilio SMS fallback with request + YES/NO  → mark FALLBACK_SMS_SENT
   ↓ webhook idempotent (HMAC verified; dup call_id ignored)
```

### Solves
Non-responsive donors are reached by voice, then SMS — no donor is left in limbo.

---

## Feature 9 — Demand Forecasting Agent (`agents/demand_forecast_agent.py`)

### What it does
A standalone 5-node LangGraph agent that predicts weekly blood demand and flags shortages BEFORE
emergencies happen. This is the "anticipate need" requirement.

### 5-node pipeline (in depth)
```
NODE 1 data_collector   → pull bridges due in next 28 days (recurring transfusion cycles)
                          + last 90 days emergency history
                          + count eligible donors per blood type = SUPPLY
NODE 2 schedule_analyzer→ expand bridge recurrence into weekly needed-units per blood type
                          (deterministic baseline); flag any week > 5 units
NODE 3 supply_gap_node  → demand vs supply per blood type per week → gap + confidence
                          + historical multiplier (e.g. O+ historically +20%)
NODE 4 bedrock_insight  → Claude Haiku turns numbers into plain-English 30-day summary
                          + specific shortage risks + one action per under-supplied type
NODE 5 persist_node     → write demand_forecasts table + system_cache
                          + ntfy alert if any week shows a deficit
```
Runs daily 6 AM IST (APScheduler) + manual `POST /api/admin/forecast/run`. Surfaced in Admin UI
(`DemandForecastPanel.tsx`) as a grouped bar chart + AI summary + shortage banners.

### Solves
Proactive (not reactive) supply planning — for an NGO this is driven by recurring bridge cycles.

---

# 💚 PILLAR C — ENGAGEMENT

## Feature 10 — Churn Prediction on Real Labels (`ml/train_churn.py`, A4)

### What it does
XGBoost predicts which donors will go inactive, trained on **real labels** from the Blood Warriors
dataset (`user_donation_active_status` + `inactive_trigger_comment`).

### Features (real signals)
calls_to_donations_ratio (primary), donation_count, response_rate, days_since_donation,
is_one_time_donor, serves_active_bridge, total_calls. Class imbalance handled with
`scale_pos_weight`. Atomic save: only replaces the model if validation AUC > 0.70.

### 4 risk tiers → tiered interventions
```
0.0–0.3 LOW       → no action
0.3–0.6 MEDIUM    → send impact story
0.6–0.8 HIGH      → re-engagement badge challenge   ("not donated in 1 year" pattern)
0.8–1.0 CRITICAL  → AI voice call                   ("limited activity despite calls" pattern)
```
Monthly retrain cron + batch-scores all donors into `churn_score`/`churn_risk`.

### Solves
Anticipate willingness; re-engage at-risk donors before they go silent.

---

## Feature 11 — Gamification (`agents/gamification.py`)

### NGO engagement badges
First Drop (1), Lifeline (5), Bridge Hero (12), Rapid Responder (confirm <2h),
Streak Keeper (3+ on-cycle in a row), City Champion (top-3 city). Plus a monthly city leaderboard.

### Flow
On donation confirmation, the gamification node fetches the donor, runs all badge rules against
updated counts, awards new badges, updates the leaderboard, and notifies via Telegram.

### Solves
Continued participation; donors see their impact and rank.

---

## Feature 12 — Failure-Learning Loop (`services/donor_memory.py`, B4)

### What it does
The system learns from every non-confirmation and self-adjusts its outreach protocol — the PRD's
"self-manage improvement via failure learning."

### Flow (in depth)
```
on every confirm/decline/no-response:
   ↓ capture signals: response_time, outcome, channel, time_of_day, message_text
   ↓ analyze_response_and_update() → Claude Haiku returns JSON:
        updated tone_profile, new emotional_anchor, optimal_contact_window,
        best_channel, failure_reason (wrong_channel / wrong_time / fatigue_from_calls ...)
   ↓ write back to donor_memory (append anchors only if new)
   ↓ aggregate into outreach_protocol_stats by (channel, time_of_day, blood_type, role)
   ↓ planner READS these stats → picks the highest-success channel+time per segment
   ↓ if a channel's success < 25% over last 20 attempts → planner deprioritises it
   ↓ every protocol change logged to agent_traces (visible system learning)
```

### Solves
The system measurably improves channel/timing decisions over time without human tuning.

---

## Feature 13 — Agentic Telegram Bot (`services/telegram_bot.py`)

### What it does
Every message (command OR natural language) runs through a Bedrock tool-calling loop with memory.

### Flow
```
donor message
   ↓ fetch donor_memory → build context (language, tone, badges, streak, bridge)
   ↓ Nova Lite + 10 tool schemas + context
   ↓ model picks tool → execute locally → feed result back → loop until plain text
   ↓ ensure reply in donor's language (translate pass if needed)
   ↓ send + update last_interaction
```
**10+ tools:** get_donor_profile, check_eligibility, get_donation_history, toggle_availability,
get_badges, get_leaderboard, get_impact_story, get_next_donation_date, report_medical_hold,
get_my_bridge. Photo → Textract OCR onboarding. `/start` → DPDP consent gate.

### Solves
Conversational AI with memory, multilingual, fully agentic (no rigid command tree).

---

# 🌍 PILLAR D — SCALE & RESPONSIBLE AI

## Feature 14 — Amazon Bedrock LLMs (`core/llm_provider.py`)
One adapter, three tiers (Nova Lite / Claude Haiku / Sonnet), region ap-south-1. Swappable in one
file. Cost-tiered to stretch $30 of credits.

## Feature 15 — DPDP 2023 Compliance (`SECURITY.md`)
Consent gate before any bot tool; Row Level Security on sensitive tables (consent_records,
donor_memory, donor_verifications = service-role only); `donors_public` view hides phone/lat-lng/
churn; dedicated `JWT_SECRET` (not the Supabase key). No clinical data over Telegram.

## Feature 16 — Demand Forecast UI + Location UI (A5 / M6)
`DemandForecastPanel.tsx` (admin demand chart + AI summary + shortage actions);
`LocationManager.tsx` + `HealthStatusControl.tsx` (patient/donor location + health management),
all additive with framer-motion animation.

## Feature 17 — AWS Deployment
Dockerfile + .dockerignore, nginx HTTPS reverse proxy, S3 + CloudFront frontend, S3 model loading,
hardened /health (Bedrock/S3/Comprehend checks), SMOKE_TEST.md runbook.

---

# 🔬 PHASE 2 — Antigen Phenotyping (Planned, Not Yet Active)

### Why it's Phase 2
The real Blood Warriors dataset has **no antigen columns** — only ABO+Rh blood group. So the live
matcher uses ABO+Rh + geo + engagement. The clinical antigen layer is designed and the columns
exist, but it stays OFF until phenotype data is available.

### What's already in place (ready to switch on)
- Schema columns retained: `kell_negative`, `duffy_negative`, `kidd_negative`, `rh_e_negative`,
  `rh_c_negative`, `mns_negative` (donors); `antibody_kell`, `antibody_duffy`, ... (patients)
- `antigen_score` field carried through the chain (currently constant 1.0 placeholder)
- A scoring agent slot in the pipeline (`antigen_score` node)

### Phase 2 design (when phenotype data arrives)
```
For each compatible donor:
   score starts at 1.0
   if patient needs Kell-neg  AND donor not Kell-neg  → −0.35  (most immunogenic)
   if patient needs Duffy-neg AND donor not Duffy-neg → −0.25
   if patient needs Kidd-safe AND donor not Kidd-safe → −0.20
   + Rh-E (−0.15), Rh-C (−0.10), MNS (−0.05)
   keep donors with score ≥ 0.60
```
This blends into the existing weighted score as an additional term and is stored as a Neo4j
`COMPATIBLE_WITH.antigen_score` edge for sub-100ms graph re-ranking. **Goal:** prevent Delayed
Hemolytic Transfusion Reactions for poly-transfused patients — a clinical-grade upgrade once
phenotype data is collected (OCR blood cards, lab confirmation via `donor_verifications`).

---

# Summary Table — Pillars, Features, Status

| Pillar | Feature | Agent/File | Status |
|---|---|---|---|
| A Matching | Geo radius-tier | matching_engine.py | ✅ |
| A Matching | Weighted scoring | matching_engine.py (WEIGHTS) | ✅ |
| A Matching | Hungarian optimizer | assignment_optimizer.py | ✅ |
| A Matching | Multi-location | schema_v4_locations.sql + M4 + M6 | ✅ |
| B Coordination | 14-node pipeline | agents/graph.py | ✅ |
| B Coordination | Monitor + auto-repair | monitor.py, repair.py | ✅ |
| B Coordination | Donor health self-update | api/donors.py (M5) + telegram_bot.py | ✅ |
| B Coordination | Voice + SMS fallback | voice.py, B3 | ✅ |
| B Coordination | Demand forecasting | demand_forecast_agent.py | ✅ |
| C Engagement | Churn ML (real labels) | ml/train_churn.py | ✅ |
| C Engagement | Gamification | gamification.py | ✅ |
| C Engagement | Failure-learning loop | donor_memory.py, planner.py | ✅ |
| C Engagement | Agentic Telegram bot | telegram_bot.py | ✅ |
| D Scale | Bedrock LLMs | llm_provider.py | ✅ |
| D Scale | DPDP compliance | SECURITY.md, RLS, JWT | ✅ |
| D Scale | Forecast + Location UI | DemandForecastPanel, LocationManager | ✅ |
| D Scale | AWS deployment | Dockerfile, nginx, S3/CloudFront | ✅ docs |
| — | Framer-motion polish (existing pages) | B5 | 🔵 Partial |
| — | Antigen phenotyping | (Phase 2) | ⏳ Planned |

---

*BloodBridge AI · Team Inqilab · NGO Edition · Matching = ABO+Rh + Geo + Engagement · Antigen = Phase 2*
