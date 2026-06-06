# BloodBridge AI — Implementation & End-to-End Test Plan

> Code-traced action plan to get the platform demo-ready.
> Every item below was verified against the actual codebase, not file existence.
> Scope: SMS fallback, LoRa, and cloud deployment are **explicitly out of scope** for now.

---

## Legend

| Symbol | Meaning |
|---|---|
| 🔴 | Blocker — breaks the demo if not fixed |
| 🟡 | Important — feature works partially or claim ≠ reality |
| 🟢 | Done / verified working |
| ⏳ | Test step (not a code change) |

---

## STATUS SNAPSHOT (as of this plan)

| Area | State |
|---|---|
| 6 runtime-fatal syntax bugs (outreach, repair, churn_batch, impact_story, transfusion_calendar, voice_service) | 🟢 **FIXED** (restored after a remote force-push wiped them — re-verify on every pull) |
| 8-antigen ISBT scoring in live matcher | 🟢 **WIRED & TESTED** (Kell/Duffy/Kidd penalties + hard ABO gate) |
| Bedrock model + region | 🔴 **OPEN** — single model for all 3 tiers, region likely wrong |
| Hungarian optimizer in live path | 🟡 **OPEN** — admin-only, not in graph |
| Neo4j live matching | 🟡 **OPEN** — bypassed by Python matcher |
| Channel routing tier count | 🟡 **OPEN** — 2-tier, deck may say 3 |
| Seed data loaded in live Supabase | 🔴 **UNVERIFIED** — #1 demo risk |
| bridge_memberships seeded | 🟡 **OPEN** — bridge_bonus weight never fires |

---

# PHASE 0 — BLOCKERS (do first, ~30 min)

## 0.1 🔴 Fix Bedrock model + region (`core/llm_provider.py`, `core/config.py`)

**Problem (traced):** `get_fast_llm`, `get_reasoning_llm`, `get_quality_llm` all return
`anthropic.claude-3-5-sonnet-20241022-v2:0`. `config.py` defaults `AWS_REGION="ap-south-1"`.
A bare Anthropic model ID in `ap-south-1` requires a **cross-region inference profile** →
throws `ValidationException` on every call → planner, outreach, conflict, voice, impact,
churn all silently fall back to templates. **Every AI feature is dead until this is fixed.**

**Decision needed:** which region is your Bedrock model access actually enabled in?
- **Option A (simplest):** set `AWS_REGION="us-east-1"` and keep standard model IDs.
- **Option B (stay in Mumbai):** use APAC inference profile IDs, e.g.
  `apac.anthropic.claude-3-5-sonnet-20241022-v2:0`.

**Action:**
1. Confirm region + that the models are granted in the Bedrock console.
2. Update `llm_provider.py` to wire the **3 real tiers** (item 0.2).
3. Update `.env` `AWS_REGION` accordingly.

## 0.2 🔴/🟡 Wire the real 3 models (`core/llm_provider.py`)

**Problem:** deck claims Nova Lite + Haiku + Sonnet; code uses Sonnet for all three.

**Action:**
| Function | Target model | Used by |
|---|---|---|
| `get_fast_llm` | `amazon.nova-lite-v1:0` (or Haiku) | Telegram replies, outreach messages |
| `get_reasoning_llm` | `anthropic.claude-3-5-haiku-...` | planner, conflict, forecast, failure analysis, voice/calendar scripts |
| `get_quality_llm` | `anthropic.claude-3-5-sonnet-...` | impact stories |

> Note: Nova Lite uses a different message schema than Anthropic models on Bedrock.
> If Nova causes adapter issues under time pressure, fall back to **Haiku for fast + reasoning,
> Sonnet for quality** — still a real 2-model story, cheaper than all-Sonnet.

**Test ⏳:** `python -c "from core.llm_provider import get_fast_llm; print(get_fast_llm().invoke('say OK').content)"`
for each of the 3 functions. Must return text, not raise `ValidationException`.

## 0.3 🔴 Verify seed data is loaded in live Supabase (#1 demo risk)

**Problem (traced):** `matching_engine.rank_donors()` reads `patients`, `patient_locations`,
`donors`, `bridge_memberships`. If these are empty, it returns `{primary:[], wide_net:[]}`
and the matching demo shows **nothing**.

**Action:**
1. Run schema: `data/supabase_schema.sql` + `schema_v4_locations.sql` in Supabase SQL editor.
2. Run `python data/seed_supabase.py` (500 donors, 50 patients, locations, consent, memory, badges).
3. Run `python data/seed_neo4j.py` (chain graph + blood banks).

**Test ⏳ (must pass before anything else):**
```bash
python -c "import asyncio; from services.matching_engine import rank_donors; r=rank_donors('P-10000'); print('primary:', len(r['primary']), 'wide_net:', len(r['wide_net']))"
```
Expected: `primary: 8` (non-zero). If `0`, seeds are not loaded — STOP and fix.

## 0.4 🟡 Seed `bridge_memberships` so bridge_bonus fires

**Problem:** `rank_donors` looks up `bridge_memberships` for the `bridge_bonus` (0.20) weight,
but `seed_supabase.py` never inserts any → the weight is dead for every donor.

**Action:** add a seeding block: for ~20 patients, attach 2-3 nearby compatible donors as
bridge members (`bridge_id = patient_id`, `donor_id = ...`). Makes the "6-parameter" story real.

**Test ⏳:** re-run 0.3 test for a patient with bridge donors; confirm a bridge donor's
`match_score` is measurably higher than an equivalent non-bridge donor.

---

# PHASE 1 — PILLAR 1: SMART MATCHING

## 1.1 🟢 8-Antigen ISBT scoring (DONE)
Wired into `rank_donors`: `compute_antigen_score(donor, patient)` →
`antigen_safety` weight (0.15) + hard gate (`antigen <= 0 → skip`).
Verified: safe O+ donor = 1.0, Kell-mismatch = 0.65, ABO-incompatible = 0.0 (filtered).

**E2E test ⏳ (the DHTR-prevention demo):**
1. Pick a patient with `antibody_kell=true`.
2. Run `rank_donors(patient_id)`.
3. Confirm Kell-**negative** donors rank above Kell-**positive** donors of equal distance.
4. Confirm no ABO-incompatible donor appears at all.

## 1.2 🟡 Hungarian optimizer — decide story (pick ONE)

**Reality:** `optimize_assignments()` only runs from `GET/POST /api/admin/optimize-assignments`.
The live `conflict` graph node uses a Supabase flag + LLM, never the Hungarian solver.

- **Option A (honest, recommended, 0 code):** present it as an **admin batch optimizer**
  ("when multiple patients compete, staff run global optimization"). Update deck wording.
- **Option B (wire it live, ~45 min):** in `agents/conflict.py`, when ≥2 CRITICAL patients
  share donors, build `patient_candidates` and call `optimize_assignments()` to reorder chains.
  Higher risk; only if Phase 0 is green and time remains.

**Test ⏳ (Option A):** `POST /api/admin/optimize-assignments` with 2 patients sharing donors →
returns disjoint donor→patient assignment. (Option B: trigger 2 concurrent CRITICAL requests,
confirm chains don't double-book the same donor.)

## 1.3 🟡 Neo4j matching — reframe (0 code)

**Reality:** `find_top_donors()` calls the Python `rank_donors()` on Supabase. The
`COMPATIBLE_WITH` Cypher exists but never runs for live matching. Neo4j stores `IN_CHAIN`
chain edges + powers the force-graph dashboard.

**Action:** change the deck from "O(1) graph matching <100ms" to
**"Neo4j powers live chain state + real-time visualization."** (True and still impressive.)

**Test ⏳:** after an emergency, query Neo4j for `IN_CHAIN` edges of that `request_id`;
confirm 8 edges with `status`/`chain_position`; confirm dashboard renders them.

## 1.4 🟢 XGBoost urgency, eligibility filter, e-RaktKosh fallback
Urgency + eligibility = verified wired. e-RaktKosh = real code but live portal schema is
guessed → **treat as mocked**; rely on Neo4j/local-seed tiers for the demo.

---

# PHASE 2 — PILLAR 2: AUTONOMOUS COORDINATION

## 2.1 🟢 14-node LangGraph pipeline
Verified in `agents/graph.py` — entry `intake`, parallel `antigen_score ∥ urgency_score`,
conditional `route_after_neo4j_match` and `route_after_monitor`, self-loop monitor.

## 2.2 🟢 Chain auto-repair + Bolna voice (syntax fixed)
`repair.py` and `voice_service.py` were crashing (IndentationError) — now fixed.
Voice requires `BOLNA_API_KEY` + `BOLNA_AGENT_ID` or it returns `SKIPPED` (graceful).
`DEMO_MOCK_MODE=true` simulates a successful call for offline demos.

## 2.3 🟡 Channel routing — reframe to 2-tier (0 code)
`planner.py` routes **Telegram → voice_queue → Telegram-fallback**. SMS is removed (intended).
**Action:** deck must say **2-tier (Telegram → Voice)**, not 3.

## 2.4 🟢 Proactive scheduler, WebSocket, ntfy
Proactive outreach (cron 7 AM), demand forecast (cron), WebSocket broadcasts, ntfy critical
alerts — all verified wired.

**E2E test ⏳ (full coordination loop):** see Phase 5 scenario B.

---

# PHASE 3 — PILLAR 3: ENGAGEMENT (mostly 🟢)

| Feature | State | Note |
|---|---|---|
| Churn 4-tier batch | 🟢 | syntax fixed; cron 8 PM |
| Failure-learning loop | 🟢 | `donor_memory.analyze_response_and_update` |
| Demand forecast (5-node) | 🟢 | cron + `/api/admin/forecast/run` |
| Gamification (6 badges) | 🟢 | leaderboard live |
| SVD challenge recommender | 🟢 | `ml/challenge_recommender.py` |
| Impact story (Sonnet) | 🟢 | syntax fixed; 2-hr post-donation |
| Donor memory | 🟢 | injected into LLM calls |
| DPDP consent | 🟢 | consent gate + audit hash |

**Test ⏳:** trigger churn batch manually, confirm CRITICAL→voice / HIGH→message /
MEDIUM→challenge routing; complete a donation and confirm an impact story is generated + sent.

---

# PHASE 4 — PILLAR 4: SCALE (mostly 🟢)

| Feature | State | Note |
|---|---|---|
| Telegram agentic bot | 🟢 | tool-calling, registration, /emergency |
| Bedrock multi-model | 🔴 | **fix in 0.1/0.2** |
| Amazon Textract OCR | 🟢 | + Vision-LLM fallback |
| 10-language support | 🟢 | templates + Bolna voice configs |
| SMS fallback | ⛔ | out of scope |
| LoRa offline | ⛔ | out of scope |
| Deployment | ⛔ | out of scope (run locally) |

---

# PHASE 5 — END-TO-END TEST SCENARIOS (frontend → backend → AI → Telegram)

> Run these only after Phase 0 is fully green. Each is a scripted demo path.

## Scenario A — Smart Matching + Antigen Safety (Pillar 1)
1. **Frontend:** open Patient Dashboard → pick a patient with anti-Kell flag.
2. **Trigger:** staff fires emergency (dashboard button or Telegram `/emergency B+ Hyderabad P-10000`).
3. **Backend:** `run_emergency_pipeline` → `intake → eligibility → antigen_score ∥ urgency → neo4j_match`.
4. **Verify:** top-8 donors are ABO-compatible AND Kell-negative ranked first; antigen_score
   visible per donor; no ABO-incompatible donor present.
5. **Frontend:** force-graph dashboard shows 8 chain nodes (position 1 = ALERTED).

**Pass criteria:** non-empty ranked list, antigen safety visibly affects order, dashboard renders chain.

## Scenario B — Autonomous Coordination + Self-Heal (Pillar 2)
1. Continue from A. First donor is ALERTED via **Telegram** (real message in donor's language).
2. **AI calling:** simulate no-response 7 min → monitor marks stale → routes to `voice` (Bolna
   call or `DEMO_MOCK_MODE` simulated) → back to monitor.
3. Simulate **decline** → `chain_repair` pulls next backup donor → re-outreach.
4. Simulate **confirm** ("YES" on Telegram) → node turns GREEN live (WebSocket) → `outcome` →
   `gamification` (badge) → END.
5. Force 3+ stale → `inventory` (blood-bank fallback) → ntfy alert to staff.

**Pass criteria:** chain never silently dies; every transition broadcasts to the dashboard.

## Scenario C — Telegram Agentic Bot (Pillar 4)
1. Donor registration flow via bot (incl. **OCR**: upload blood-card photo → Textract extracts type).
2. Language auto-detect → bot replies in detected language (Bedrock).
3. Donor asks free-text question → agentic tool-calling answers (badges, next eligible date, leaderboard).

**Pass criteria:** bot responds via Bedrock (not template fallback), OCR fills blood_type.

## Scenario D — Engagement Loop (Pillar 3)
1. Run churn batch → confirm tiered interventions dispatch.
2. Complete a donation → 2-hr impact story generated (Sonnet) + delivered on Telegram.
3. Run demand forecast → admin panel (`DemandForecastPanel.tsx`) shows 28-day chart + shortage alerts.

**Pass criteria:** churn tiers route correctly; impact story is personalized (not fallback);
forecast renders on Admin page.

## Scenario E — Conflict / Optimizer (Pillar 1 advanced)
1. Fire 2 concurrent CRITICAL requests sharing nearby donors.
2. **Option A path:** `POST /api/admin/optimize-assignments` → disjoint assignment.
3. **Option B path (if wired):** conflict node reorders chains, no double-booking.

**Pass criteria:** no donor assigned to two patients simultaneously.

---

# PRE-DEMO CHECKLIST (run in order)

- [ ] 0.1 Bedrock region/model confirmed — test invoke returns text for all 3 LLM functions
- [ ] 0.2 3 model tiers wired
- [ ] 0.3 Seeds loaded — `rank_donors('P-10000')` returns 8 primary donors
- [ ] 0.4 bridge_memberships seeded — bridge donor scores higher
- [ ] 1.1 Antigen safety test (Scenario A) passes
- [ ] 1.2 Hungarian story decided (deck updated or wired)
- [ ] 1.3 Neo4j deck wording corrected
- [ ] 2.3 Channel routing deck wording = 2-tier
- [ ] All 6 syntax-fixed files compile (`python -m compileall agents services`)
- [ ] Scenario A–E walked through once end-to-end
- [ ] `DEMO_MOCK_MODE` toggle decided (true = safe offline demo for voice/external APIs)

---

# GIT HYGIENE WARNING

The remote `main` was **force-pushed** by another machine, which silently **deleted the 6
syntax fixes**. They have been restored locally from commit `22e48b5`.

**Rule for this repo until coordinated:**
- Always `git fetch` + inspect `git log origin/main` before pushing.
- After any pull, re-run `python -m compileall BloodBridge_AI_Backend/agents BloodBridge_AI_Backend/services`
  to confirm the syntax fixes survived.
- Avoid force-push. If someone force-pushes, the 6 fixes + antigen wiring must be re-applied.

---

# OUT OF SCOPE (do not spend time here)
- SMS / Twilio fallback
- LoRa offline radio bridge
- Cloud deployment (EC2/S3/Render/Vercel) — demo runs locally
