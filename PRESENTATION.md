# BloodBridge AI — Presentation Document

> **Team Inqilab · DNR College of Engineering & Technology · Blend360 Hackathon**
> *Autonomous, AI-powered blood support network for the Blood Warriors NGO.*
> Use this as your slide deck script. Each "SLIDE" = one screen. Speaker notes in *italics*.

---

## SLIDE 1 — Title

# 🩸 BloodBridge AI
### Autonomous AI for Blood Donor Coordination

**Tagline:** *"We don't just notify donors — we coordinate, learn, and self-heal an entire blood support network, autonomously."*

Built for: **Blood Warriors NGO** (Thalassemia patients, India)
Stack: FastAPI · LangGraph · Neo4j · Supabase · Amazon Bedrock · Telegram · Bolna.ai
Cost: **₹0 / free-tier-first**

*Speaker: "Most blood apps are a contact list with a send button. We built an autonomous AI operations team that runs the whole coordination lifecycle."*

---

## SLIDE 2 — The Problem (what the NGO actually faces)

Blood Warriors coordinates **voluntary donors** for **Thalassemia patients** who need a transfusion
**every 15–28 days, for life** (500–700 lifetime transfusions).

**Four operational failures today:**

| # | Failure | Pain |
|---|---|---|
| 1 | **Matching** | Manual lookup, no prioritization, no way to resolve when 2 patients need 1 rare donor |
| 2 | **Coordination** | 8–10 donor "bridge" chains collapse when one says no; **80% of staff time** lost to manual follow-up calls |
| 3 | **Engagement** | ~60% donors go inactive; generic reminders get only **15% response** |
| 4 | **Scale** | 36 states, 22+ languages, patchy rural internet, strict DPDP 2023 data law |

*Speaker: "These are operational, not just technical, failures. A human team literally cannot call hundreds of donors fast enough."*

---

## SLIDE 3 — What the Problem Statement Asked For

The Blend360 brief asked for a system that can:
- Handle multiple workflows through **one intelligent AI layer**
- Automate **outreach, follow-ups, escalations**
- **Track & interpret** donor responses to guide next steps
- React to **real-time events**
- Enable **conversational interactions with memory**
- **Self-manage improvement via failure learning**
- Give admins **dashboards & insights** (incl. demand forecasting)
- Be **consent-aware & compliant**
- Operate at **scale, across languages & infrastructure**

*Speaker: "We mapped every one of these to a concrete agent or feature. Nothing is hand-wavy."*

---

## SLIDE 4 — Our Solution in One Line

> **An autonomous multi-agent AI platform** that takes a blood request from intake → matching →
> outreach → monitoring → self-repair → confirmation → engagement — **with zero human intervention
> on the happy path**, accessible via a zero-install Telegram bot and a live staff dashboard.

The brain: a **14-node LangGraph state machine** where each node is an autonomous agent sharing one
typed state. The graph *decides* what runs next — it is not a fixed script.

---

## SLIDE 5 — The 4 Pillars (our solution map)

| Pillar | Solves | Our Answer |
|---|---|---|
| 🩸 **A. Smart Matching** | Right donor, right time | Geo radius-tier + weighted scoring + Hungarian optimizer |
| 🔗 **B. Autonomous Coordination** | Chains collapsing, staff overload | 14-node LangGraph pipeline + self-healing chains + voice/SMS |
| 💚 **C. Engagement** | Donor drop-off | Churn ML + gamification + failure-learning + impact stories |
| 🌍 **D. Scale & Responsible AI** | Reach + privacy | Telegram + 10 languages + Bedrock + DPDP compliance + AWS |

*Speaker: "Four pillars, one for each operational failure."*

---

## SLIDE 6 — Pillar A: Smart Matching (the parameters we consider)

**We don't match on blood type alone. Every donor is scored on a transparent, weighted formula:**

```
match_score =  w1·blood_match        (ABO + Rh compatibility — exact = 1.0)
             + w2·proximity          (geo distance, haversine)
             + w3·engagement         (calls-to-donation ratio, response rate, history)
             + w4·eligibility_freshness  (peaks at 56 days post-donation)
             + w5·(1 − churn_score)  (avoid donors about to drop off)
             + w6·bridge_bonus       (donors already committed to this patient)
             − w7·radius_penalty     (farther rings penalised)
```

**Parameters we consider (this is the "intelligence"):**
1. **Blood compatibility** — ABO + Rh matrix (8 blood groups)
2. **Geography** — 3 expanding rings: R1 ≤5km → R2 ≤15km → R3 ≤30km (wide-net backups)
3. **Engagement** — how reliably a donor responds (real NGO data)
4. **Eligibility** — 56-day donation gap, medical hold, active status
5. **Churn risk** — likelihood the donor goes silent
6. **Bridge commitment** — is this donor already this patient's dedicated donor?

> **Phase 2 (clinical upgrade):** 8-antigen phenotyping (Kell, Duffy, Kidd, Rh-E/C, MNS) to prevent
> Delayed Hemolytic Transfusion Reactions. Schema + scorer are built and ready; activates once
> phenotype data is collected.

*Speaker: "Weighted scoring means the NGO can tune priorities — proximity in dense cities, engagement in sparse ones — without rewriting code."*

---

## SLIDE 7 — Pillar A: The Advanced Bit (Hungarian Optimizer)

**Problem:** When 2+ patients need the same nearby donors, greedy matching is globally sub-optimal
(Patient A and B fight over one donor; Patient C gets none).

**Our answer:** the **Hungarian algorithm** (`scipy.linear_sum_assignment`) computes the
**globally optimal** donor→patient assignment minimizing total cost across all active patients.

```
cost[patient][donor] = 1 − match_score   → Hungarian solve → optimal global plan
```

*Speaker: "This is operations-research-grade allocation, not first-come-first-served. It's our genuinely advanced piece."*

---

## SLIDE 8 — Pillar B: Autonomous Coordination (the agent pipeline)

**14-node LangGraph state machine:**

```
intake → eligibility → [antigen ∥ urgency]  → neo4j_match
   → (conflict?) → planner → outreach → monitor
        ├─ confirmed  → outcome → gamification → END
        ├─ stale      → voice  → back to monitor
        ├─ declined   → repair → re-outreach
        └─ exhausted  → inventory (blood bank fallback) → escalate
```

**Why this is autonomous (3 properties):**
1. **Shared typed state** — all 14 agents read/write one `AgentState`
2. **Conditional routing** — the graph picks the next node from state (`route_after_monitor`)
3. **Self-looping** — the monitor re-enters itself every 5 min (APScheduler) until success/escalation

*Speaker: "No human types anything after the request. The graph drives itself."*

---

## SLIDE 9 — Pillar B: Self-Healing Chains (the wow moment)

**A donor chain has 8 positions. When one fails, the system repairs itself in seconds.**

```
chain_monitor (every 5 min)
   ↓ donor ALERTED >7 min, no reply  → escalate to AI voice call
   ↓ donor DECLINED / unreachable    → chain_repair pulls next-best backup donor
   ↓ 3 consecutive fails             → inventory fallback (nearest blood banks) → alert staff (ntfy)
   ↓ donor reports "sick"            → auto-remove from chain + pull replacement + notify
```

Every status change broadcasts live over **WebSocket** to the staff dashboard.

*Speaker: "This is the difference between AI chat and AI coordination — the chain never silently dies."*

---

## SLIDE 10 — Pillar B: Proactive, Not Just Reactive

- **Proactive Scheduler** (runs daily 7 AM): Thalassemia cycles are predictable (every ~21–28 days).
  We start *warm* outreach **5–7 days before** a patient is due — preventing the emergency.
- **Demand Forecasting Agent** (5-node LangGraph): predicts next-28-day blood demand from recurring
  bridge cycles **vs eligible-donor supply**, and flags shortages to admins with an AI action plan.

*Speaker: "We don't wait for the crisis. We forecast it and act early."*

---

## SLIDE 11 — Pillar C: Engagement (keeping donors active)

| Feature | What it does |
|---|---|
| **Churn Prediction (XGBoost)** | Scores every donor's drop-off risk → 4 tiers → tiered action (LOW=none, MEDIUM=impact story, HIGH=challenge, CRITICAL=AI voice call) |
| **Gamification** | Badges (First Drop, Lifeline, Bridge Hero, Rapid Responder, Streak Keeper, City Champion) + city leaderboard |
| **Impact Stories** | 2 hrs after donation, AI writes a warm, anonymized 3-line story → "Because of you, a child went home today" |
| **Failure-Learning Loop** | Every non-response is classified (wrong channel/time/fatigue) → planner self-adjusts future outreach |

**Parameters for engagement:** calls-to-donation ratio, response rate, donation count, days since
last donation, time-of-day responsiveness, preferred channel.

*Speaker: "We move response rates from a generic 15% toward personalized outreach — by remembering each donor and learning from every failure."*

---

## SLIDE 12 — Pillar D: Scale, Access & Responsible AI

- **Zero-install Telegram bot** — donors use what they already have (no app download)
- **Agentic conversation** — natural language → tool-calling → memory-aware, **10 Indian languages**
- **Amazon Bedrock LLMs** — Nova Lite (fast) + Claude Haiku (reasoning) + Sonnet (stories)
- **Voice** — Bolna.ai AI calls in Indian languages (TRAI safe hours) → Twilio SMS fallback
- **OCR onboarding** — snap a blood card photo → auto-extract blood group (Amazon Textract)
- **DPDP 2023 compliance** — consent gate, Row-Level Security, right-to-erasure, audit hashes,
  no clinical data over Telegram
- **LoRa offline bridge** *(concept)* — rural areas without 4G

*Speaker: "Built for India's reality — language, connectivity, and the new data-privacy law."*

---

## SLIDE 13 — AI & Data Services Used

| Layer | Service | Role |
|---|---|---|
| Fast LLM | **Bedrock Nova Lite** | Telegram replies, outreach messages |
| Reasoning LLM | **Bedrock Claude Haiku** | planning, conflict resolution, forecast insight, failure analysis |
| Quality LLM | **Bedrock Claude Sonnet** | emotional impact stories |
| ML | **XGBoost** | churn prediction + urgency scoring |
| Recommender | **scikit-learn SVD** | personalized donor challenges |
| Optimizer | **scipy Hungarian** | multi-patient optimal assignment |
| Voice | **Bolna.ai** (Sarvam TTS) | AI voice calls in Indian languages |
| OCR | **Amazon Textract** | blood card extraction |
| Language | **Amazon Comprehend** | language detection |

---

## SLIDE 14 — Neo4j: The Coordination Engine (not just a DB)

Neo4j models the network as a **graph**, which makes coordination queries trivial that would be
painful in SQL:

- **`COMPATIBLE_WITH` edges** — donor↔patient compatibility stored as weighted edges
- **`IN_CHAIN` edges** — the live 8-donor chain (position, status, alerted_at) — *stateful*
- **`SERVES_BRIDGE` edges** — recurring donor↔patient commitments
- **Geo-proximity** — point.distance ranking inside the query

**Result:** "find the 8 best, closest donors" or "detect broken chain links" = **one fast Cypher
query**, feeding the live `react-force-graph-2d` dashboard (node color = status, in real time).

---

## SLIDE 15 — End-to-End Flow (the demo path)

```
1. REQUEST   Staff (Telegram/dashboard): "B+ needed, Patient P-101, Hyderabad"
2. INTAKE    Fetch patient + context, create request, init AgentState
3. ELIGIBLE  Filter donors: 56-day gap, medical hold, active, consent
4. SCORE     Parallel: urgency (XGBoost) + compatibility (ABO+Rh; antigen Phase 2)
5. MATCH     Geo radius-tier + weighted score → top 8 donors + backup pool (Neo4j)
6. CONFLICT  If 2 patients share donors → Hungarian optimal assignment
7. PLAN      Per donor: best channel + language + tone (learned from history)
8. OUTREACH  Parallel Telegram messages in each donor's language (Bedrock)
9. MONITOR   Every 5 min: stale → voice; declined → repair (next backup)
10. CONFIRM  Donor replies "yes" → chain node turns GREEN live on dashboard
11. OUTCOME  Update stats, award badges, schedule 2-hr impact story
12. LEARN    Classify any failures → planner self-improves next time
```

*Speaker: walk this exact path live in the demo.*

---

## SLIDE 16 — Data We Use (parameters / schema essentials)

**Donor:** donor_id, blood_type, lat/lng + geohash, locations[], role (Bridge/Emergency/Volunteer),
last_donation_date, next_eligible_date, donation_count, response_rate, calls_to_donations_ratio,
churn_score, preferred_language, telegram_chat_id, medical_hold

**Patient / Bridge:** patient_id, blood_type, locations[] (1–5), expected_next_transfusion_date,
frequency_in_days, cycle_of_donations, urgency_score, status

**Graph:** COMPATIBLE_WITH (weighted), IN_CHAIN (live status), SERVES_BRIDGE (commitment)

**Engagement:** badges, streak, donor_memory (tone, anchors, language), outreach_protocol_stats

*Real data: seeded from the actual Blood Warriors Hyderabad donor dataset (anonymized/hashed).*

---

## SLIDE 17 — Architecture (high level)

```
        ┌────────────── USERS ──────────────┐
        │ Telegram Bot       Staff Dashboard │
        │ (donors, agentic)  (React + Vite)  │
        └─────────┬───────────────┬──────────┘
                  │ webhook        │ REST + WebSocket
        ┌─────────▼───────────────▼──────────┐
        │      FastAPI Backend (async)        │
        │  ┌──────────────────────────────┐   │
        │  │ LangGraph 14-Node Pipeline    │   │
        │  │ + APScheduler (monitor/cron)  │   │
        │  └──────────────────────────────┘   │
        │  ML: XGBoost · SVD · scipy          │
        └──┬─────────┬──────────┬─────────┬───┘
           │         │          │         │
       Supabase   Neo4j      Bedrock    Bolna/
       (Postgres) (graph)    (LLMs)     Telegram/ntfy
```

Deployment target: **EC2 (backend) + S3/CloudFront (frontend)** — Docker + nginx HTTPS.

---

## SLIDE 18 — Why This Is Different (the "Aha")

1. **Autonomous, not assistive** — the LangGraph chain repairs itself; staff only get pulled in on escalation.
2. **Weighted, tunable matching** — 6 real parameters, not just blood type.
3. **Operations-research optimal** — Hungarian assignment across competing patients.
4. **Self-improving** — failure-learning loop adjusts channel/timing over time.
5. **Proactive** — forecasts demand and warms up donors before the emergency.
6. **India-real** — Telegram, 10 languages, voice, DPDP-compliant, ₹0 cost.

> *"We didn't build a notification app. We built an autonomous coordination layer for a blood NGO."*

---

## SLIDE 19 — Roadmap (honest, shows maturity)

| Phase | Item |
|---|---|
| **Now** | ABO+Rh + geo + engagement matching, autonomous coordination, engagement, dashboards |
| **+1 hr (final polish)** | Verify seeds loaded, finish UI animations, deploy to cloud |
| **Phase 2 (clinical)** | 8-antigen phenotyping (DHTR prevention) — schema + scorer ready |
| **Phase 3 (scale)** | e-RaktKosh live API, LoRa hardware, multi-region |

*Speaker: be transparent — judges respect a clear roadmap over over-claiming.*

---

## SLIDE 20 — Closing

# BloodBridge AI
**Autonomous AI that coordinates, learns, and self-heals a blood support network.**

- 4 pillars, one for each operational failure
- 14 autonomous agents · weighted + optimal matching · self-healing chains
- Telegram-first · 10 languages · DPDP-compliant · ₹0

*"Every drop, coordinated by AI — so no Thalassemia child waits."*

**Team Inqilab — DNR College of Engineering & Technology**

---

## APPENDIX — Judge Q&A Prep

**Q: Is this just a chatbot?**
A: No. It's a 14-node autonomous state machine. The bot is one channel; the coordination, matching,
monitoring, and self-repair run without human input.

**Q: How do you match donors?**
A: A weighted score over 6 parameters — blood compatibility, proximity (3 geo rings), engagement,
eligibility freshness, churn risk, and bridge commitment. Tunable weights. For competing patients we
run the Hungarian algorithm for globally optimal allocation.

**Q: What about clinical antigen safety?**
A: Designed and built as Phase 2 (Kell/Duffy/Kidd phenotyping to prevent DHTR). It activates once
phenotype data is collected; today's NGO dataset is ABO+Rh, so the live matcher uses ABO+Rh + geo +
engagement.

**Q: Why Telegram not WhatsApp?**
A: Telegram Bot API is free, instant, zero-approval. Our channel layer is abstracted — adding
WhatsApp later is one handler, no agent changes.

**Q: Is it really autonomous?**
A: Yes — the chain monitor loops every 5 minutes on its own, repairs broken chains, escalates to
voice/SMS/blood-banks, and only pings a human via ntfy when everything is exhausted.

**Q: Privacy?**
A: DPDP 2023 — explicit consent gate, Row-Level Security, right-to-erasure, audit hashing, and no
clinical data ever sent over Telegram.

---

## APPENDIX B — LangGraph Multi-Agent Workflow (node-by-node)

This is a **Stateful Multi-Agent Workflow**, not a single chatbot. It is a compiled
`StateGraph` (`agents/graph.py`) where **14 nodes** share one typed `AgentState` object. Each node
is an autonomous agent that reads the shared state, does its job, writes back, and the graph decides
what runs next via **conditional routing functions** — so the path changes per request.

**The 14 agent nodes (real code):**

| # | Node | What it does |
|---|---|---|
| 1 | `intake` | Parses the request, fetches the patient record + context, initializes `AgentState` (request_id, blood_type, city, trace_id). |
| 2 | `eligibility` | Rule-based filtering — removes donors inside the 56-day gap, on medical hold, inactive, or without consent. |
| 3 | `antigen_score` | **Phase 2 (dormant):** 8-antigen penalty scoring. Node exists and runs, but the live matcher uses ABO+Rh+geo+engagement until phenotype data is collected. |
| 4 | `urgency_score` | XGBoost real-time urgency prediction for the patient (runs **parallel** to antigen_score). |
| 5 | `neo4j_match` | Graph traversal — geo radius-tier + weighted score over the compatible pool → top donors + backup pool. |
| 6 | `conflict` | **Bedrock Claude Haiku** arbitration when 2+ patients compete for the same rare donors (Hungarian assignment feeds this). Only entered if `conflict_detected`. |
| 7 | `planner` | Decides per-donor outreach strategy — channel (Telegram vs voice), language, tone — learned from donor history. |
| 8 | `outreach` | Parallel fan-out — sends Telegram messages to all matched donors in each donor's language (Bedrock Nova Lite). |
| 9 | `monitor` | The self-loop. APScheduler-style check every 5 min for stale/declined chain positions. |
| 10 | `repair` | Pulls the next-best backup donor when a position declines/goes silent, then loops back to outreach. |
| 11 | `inventory` | Blood-bank fallback when >3 positions go stale — finds nearest banks, escalates to staff (ntfy). |
| 12 | `voice` | Bolna.ai AI voice call escalation for stale donors, then returns to monitor. |
| 13 | `gamification` | Awards badges, updates streaks/leaderboard after a successful outcome. |
| 14 | `outcome_node` | Finalizes the request, updates stats, schedules the 2-hr impact story. |

**The two routing functions (this is what makes it autonomous, not a fixed script):**

```python
# After matching: branch to conflict resolver only if patients compete
def route_after_neo4j_match(state):
    return "conflict" if state.get("conflict_detected") else "planner"

# After monitoring: the graph picks its own next move from live state
def route_after_monitor(state):
    if state['outcome'] in ['SUCCESS', 'ESCALATED']: return 'complete'   # → outcome_node
    if len(state['stale_positions']) > 3:            return 'inventory'   # blood-bank fallback
    if state['stale_positions']:                     return 'repair'      # pull backup donor
    return 'wait'                                                          # loop monitor again
```

**Execution flow (actual edges):**

```
intake → eligibility → ┌ antigen_score ┐
                       └ urgency_score ┘ → neo4j_match
   → route_after_neo4j_match → (conflict?) → planner → outreach → monitor
        → route_after_monitor:
             complete  → outcome_node → gamification → END
             repair    → repair → outreach (re-loop)
             voice     → voice  → monitor
             inventory → inventory → outcome_node
             wait      → monitor (self-loop every 5 min)
```

*Speaker: "Nodes 2→4 run with a parallel fan-out, the graph joins them at matching, then two
decision functions drive the rest. The monitor literally re-enters itself until the chain succeeds
or escalates — that's the autonomy."*

---

## APPENDIX C — Neo4j as the Coordination Engine

We use Neo4j **not as a passive store** but as the live coordination graph. Modeling donors,
patients, and chains as nodes/edges turns coordination questions that are painful in SQL into a
single fast Cypher query.

**The graph model:**

| Element | Type | Holds |
|---|---|---|
| `Donor` | node | blood_type, geo point (lat/lng), engagement stats, churn_score, status |
| `Patient` / `Bridge` | node | blood_type, geo point(s), urgency, transfusion cycle |
| `BloodBank` | node | location, stock cache |
| `COMPATIBLE_WITH` | edge | donor↔patient compatibility stored as a **weighted edge** |
| `IN_CHAIN` | edge | the live 8-donor chain — `chain_position`, `status` (PENDING/ALERTED/CONFIRMED/DECLINED), `alerted_at` — **stateful** |
| `SERVES_BRIDGE` | edge | recurring donor↔patient commitment |

**Why a graph wins here:**

1. **Matching in one query** — rank the compatible pool by score and `point.distance` and `LIMIT`
   the top donors, instead of multi-table SQL joins + app-side math.
2. **Chain-break detection is trivial** — "find `IN_CHAIN` edges where status=ALERTED and
   alerted_at older than 7 min" is one pattern match. In SQL this is awkward; in Cypher it's natural.
3. **Stateful relationships** — the chain's status lives *on the edges*, so the monitor/repair
   agents query and mutate the live chain directly.
4. **Geo-proximity ranking** — `point.distance()` ranks donors by real distance inside the query.
5. **Live visualization** — the same graph feeds the `react-force-graph-2d` dashboard, where node
   color = chain status and the network updates in real time over WebSocket.

```cypher
// Conceptual: find best available donors for a patient
MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p:Patient {id: $patient_id})
WHERE d.status = 'active' AND d.next_eligible_date <= date()
RETURN d
ORDER BY c.score DESC, point.distance(d.location, p.location) ASC
LIMIT 8
```

*Speaker: "Neo4j is the coordination engine — the chain's live state lives on the edges, so detecting
a broken link and finding the next backup is one query, not a batch job."*
