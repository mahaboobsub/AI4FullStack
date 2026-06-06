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

## STATUS SNAPSHOT (updated after Phase 0 + 1 completion)

| Area | State |
|---|---|
| 6 runtime-fatal syntax bugs (outreach, repair, churn_batch, impact_story, transfusion_calendar, voice_service) | 🟢 **FIXED** (commit b147092 — re-verify on every pull) |
| 8-antigen ISBT scoring in live matcher | 🟢 **WIRED & TESTED** (Kell/Duffy/Kidd penalties + hard ABO gate) |
| Bedrock model + region | � **FIXED** — Claude Haiku 4.5 + Sonnet 4.6, us-east-1, inference profiles |
| Hungarian optimizer documentation | � **FIXED** — documented as admin batch optimizer (accurate) |
| Neo4j documentation | � **FIXED** — documented as chain state + visualization (accurate) |
| Channel routing documentation | � **FIXED** — documented as 2-tier Telegram→Voice (accurate) |
| Seed data loaded in live Supabase | � **VERIFIED** — 501 donors, 50 patients, matcher returns 8 donors |
| bridge_memberships seeded | � **SEEDED** — 20 bridges, 60 memberships, bridge_bonus active |

---

# PHASE 0 — BLOCKERS ✅ COMPLETE

## 0.1 ✅ Bedrock model + region FIXED
**Discovered:** Claude 3.5 models are EOL/Legacy in this account.  
**Solution:** Upgraded to Claude 4 with inference profiles:
- Fast: `us.anthropic.claude-haiku-4.5-20251001-v1:0`
- Reasoning: `us.anthropic.claude-haiku-4.5-20251001-v1:0`
- Quality: `us.anthropic.claude-sonnet-4-6`
- Region: `us-east-1`
- All 3 tiers tested and working

## 0.2 ✅ 3 model tiers WIRED
Using Claude Haiku 4.5 for fast+reasoning, Sonnet 4.6 for quality. Nova Lite has incompatible schema.

## 0.3 ✅ Seed data VERIFIED
- 501 donors seeded with lat/lng + phenotypes
- 50 patients seeded with antibody flags  
- `rank_donors('P-10000')` returns 8 primary donors
- Distance: 7.7-19km, antigen: 0.90-1.00

## 0.4 ✅ Bridge memberships SEEDED
- Ran `schema_v6_demo_fix.sql` in Supabase (adds patient geo + bridge tables)
- Ran `seed_bridge_memberships.py` → 20 bridges, 60 donor memberships
- Bridge bonus component now active

---

# PHASE 1 — PILLAR 1: SMART MATCHING ✅ COMPLETE

## 1.1 ✅ 8-Antigen ISBT scoring (DONE)
Wired into `rank_donors`: `compute_antigen_score(donor, patient)` →
`antigen_safety` weight (0.15) + hard gate (`antigen <= 0 → skip`).
Verified: safe O+ donor = 1.0, Kell-mismatch = 0.65, ABO-incompatible = 0.0 (filtered).

**E2E test ⏳ ready for Scenario A demo.**

## 1.2 ✅ Hungarian optimizer — DOCUMENTED ACCURATELY
**Decided:** Option A (honest presentation, 0 code changes).  
**Updated:** PRESENTATION.md SLIDE 7 now describes it as an **admin batch optimizer** 
(`/api/admin/optimize-assignments`) that staff trigger during surge events, with real-time 
AI conflict arbitration in the live graph. Matches actual implementation.

**Test ⏳:** `POST /api/admin/optimize-assignments` ready for Scenario E.

## 1.3 ✅ Neo4j matching — DOCUMENTED ACCURATELY  
**Updated:** PRESENTATION.md SLIDE 15 now describes Neo4j as **live chain state + visualization 
engine**, not O(1) matching. Matching uses weighted Python scoring on Supabase; Neo4j tracks 
chain state and powers force-graph dashboard. Matches actual implementation.

**Test ⏳:** Neo4j chain visualization ready for Scenario B.

## 1.4 ✅ XGBoost urgency, eligibility filter
Verified wired and working in graph pipeline.

---

# PHASE 2 — PILLAR 2: AUTONOMOUS COORDINATION ✅ VERIFIED

## 2.1 🟢 14-node LangGraph pipeline
Verified in `agents/graph.py` — entry `intake`, parallel `antigen_score ∥ urgency_score`,
conditional `route_after_neo4j_match` and `route_after_monitor`, self-loop monitor.

## 2.2 🟢 Chain auto-repair + Bolna voice (syntax fixed)
`repair.py` clsand `voice_service.py` were crashing (IndentationError) — now fixed.
Voice requires `BOLNA_API_KEY` + `BOLNA_AGENT_ID` or it returns `SKIPPED` (graceful).
`DEMO_MOCK_MODE=true` simulates a successful call for offline demos.

## 2.3 ✅ Channel routing — DOCUMENTED ACCURATELY (0 code)
**Updated:** PRESENTATION.md SLIDE 10 now describes **2-tier (Telegram → Voice)** routing. 
Matches actual planner.py implementation. SMS fallback explicitly out of scope.

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
