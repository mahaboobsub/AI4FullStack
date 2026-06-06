# BloodBridge AI — V4 Development Prompts (NGO / Blood Warriors Edition)

> **Context for everyone:** This product is for the **Blood Warriors NGO**, NOT hospitals.
> The core model is the **"Blood Bridge"**: recurring voluntary donors committed to specific
> patients (a `bridge_id`), tracked by *engagement and continuity*, not hospital antigen
> phenotyping. We are building an autonomous AI donor-support network.
>
> **Hard rules for the AI (Antigravity), apply to every prompt below:**
>
> 1. This is an NGO donor-engagement platform. Do NOT introduce hospital/Thalassemia/8-antigen
>    clinical logic. ABO+Rh blood group is the only compatibility dimension (antigen layer is
>    a Phase-2 flag, default off).
> 2. WhatsApp is NOT used. Telegram is the ONLY conversational channel and it must be fully agentic.
> 3. All LLM calls go through Amazon Bedrock. All ML/forecasting uses AWS services where specified.
> 4. Final deployment target is AWS. Do not write deployment code until Phase 4.
> 5. Additive-only on the frontend: wrap/extend existing components, never rewrite working ones.
> 6. Output working changes, follow existing project patterns, do not break passing tests.

---

## Team & Time Split

| | Developer A (Backend / AI / Data) | Developer B (Agents / Comms / Frontend) |
|---|---|---|
| **Hour 1** | A1 Bedrock migration + bug fix · A2 Bridge-model reframe + real-data seed | B1 Fully agentic Telegram bot · B2 Comprehend + Textract |
| **Hour 2** | A3 Demand-Forecast LangGraph agent · A4 Churn retrain on real labels | B3 Voice hardening + SMS fallback · B4 Failure-learning loop |
| **Hour 3** | A5 Demand-forecast admin UI · A6 Production config | B5 Framer-motion polish (additive) · B6 RLS + JWT hardening |
| **Hour 4** | A7 Dockerize + EC2 · A8 Telegram webhook + nginx HTTPS | B7 S3 + CloudFront frontend · B8 Smoke test checklist |

### Phase 1.5 — Smart Matching Module (runs AFTER Phase 1, BEFORE Phase 2)

> This is NEW work. Neither the existing code nor A1–B8 solves geo-matching, multi-location,
> donor health self-management, or weighted matching. The 5 problems being fixed here:
> (1) patients have no lat/lng in schema — geo-matching is silently broken;
> (2) brittle city-string matching ("Hyderabad" vs "Secunderabad") → fix with geohash/coordinates;
> (3) no multi-location model → new donor_locations + patient_locations tables (one-to-many);
> (4) donor health self-update has no path → endpoint + Telegram tool + notify + auto-repair;
> (5) antigen logic still leaking → matching = ABO+Rh + geo + engagement (no Kell/Duffy).

| | **Dev A** — Schema / Geo / Matching engine | **Dev B** — Donor health / Telegram / UI |
|---|---|---|
| **Phase 1.5** | M1 Location schema + geo seed · M2 Geo radius-tier + weighted matching · M3 Hungarian multi-patient assignment | M4 Multi-location APIs · M5 Donor health self-update + auto-repair · M6 Location/zone UI (additive) |

**Dependency order:**

- A1 before A2 (seed needs Bedrock config). B1 before B3 (voice fallback uses agentic donor state).
- A2 before A3/A4 (forecasting + churn need Bridge schema + real data).
- **A2 before ALL M-prompts** (matching needs the bridge schema + real lat/lng seed).
- **M1 before M2/M3/M4** (everything needs the new location tables → M1 is a merge gate, like A1).
- M2 before M5 (health auto-repair calls the new radius matcher). B1 before M5 (health Telegram tool plugs into the agentic bot).
- Phase 4 starts only after A6 verifies locally.

**Who runs M-prompts:** Dev A → M1 → M2 → M3. Dev B → (wait for M1 merge) → M4 → M5 → M6.

---

# PHASE 1 — Foundation, Reframe & Real Data (Hour 1)

## Prompt A1 — Bedrock Migration + Gamification Bug Fix

```
CONTEXT:
BloodBridge AI is a FastAPI + LangGraph backend for the Blood Warriors NGO. It currently
uses Groq (fast replies) and Google Gemini (reasoning) via LangChain. We are migrating
fully to Amazon Bedrock because deployment will be on AWS with $30 of credits — choose
cost-efficient models.

TASK 1 — FIX GAMIFICATION BUG:
In agents/gamification.py (around line 70) a variable `donor` is used before being fetched
from Supabase, crashing the node at the end of each pipeline run. Fix by: read the agent
state entering the node, collect all donor_ids in the completed chain, fetch each donor's
full record from Supabase via the service-role client BEFORE any badge logic. Reframe the
badges to NGO engagement (no clinical badges): "First Drop" (1 donation), "Lifeline" (5),
"Bridge Hero" (12), "Rapid Responder" (confirmed within 2h), "Streak Keeper" (3+ on-cycle
donations in a row), "City Champion" (top-3 city). Remove any antigen/Kell-based badge.

TASK 2 — BEDROCK MIGRATION (cost-tiered):
Replace every LLM instantiation behind a single adapter so providers swap in one place.
- High-volume, latency-sensitive (telegram_bot.py replies, outreach.py message generation):
  ChatBedrock model_id "amazon.nova-lite-v1:0"
- Reasoning (planner.py, conflict.py, voice.py script gen, demand forecast insights):
  ChatBedrock model_id "anthropic.claude-3-5-haiku-20241022-v1:0"
- Highest quality only (impact_story.py): "anthropic.claude-3-5-sonnet-20241022-v2:0"
Region: ap-south-1. Create core/llm_provider.py exposing get_fast_llm(), get_reasoning_llm(),
get_quality_llm() — every agent/service imports from here, never instantiates directly.

In core/config.py add AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY as pydantic
settings. In requirements.txt add langchain-aws, boto3; remove groq and google-generativeai.
Update .env.example with the AWS variables. Prompt strings and chain/tool logic must NOT change.

EXPECTED OUTCOME:
- Gamification node never crashes; badges are NGO-engagement themed.
- All LLM traffic routes through Bedrock via one swappable adapter.
- No prompt or agent-logic changes.
```

## Prompt A2 — Bridge-Model Reframe + Real Blood Warriors Data Seed  ★ NEW, CRITICAL

```
CONTEXT:
We have the REAL Blood Warriors operational dataset (TSV) from Hyderabad. Columns:
user_id, bridge_id, role, role_status, bridge_status, blood_group, gender, latitude,
longitude, bridge_gender, bridge_blood_group, quantity_required, last_transfusion_date,
expected_next_transfusion_date, registration_date, donor_type, last_contacted_date,
last_donation_date, next_eligible_date, donations_till_date, eligibility_status,
cycle_of_donations, total_calls, frequency_in_days, status_of_bridge, status,
donated_earlier, last_bridge_donation_date, calls_to_donations_ratio,
user_donation_active_status, inactive_trigger_comment.

IMPORTANT: There is NO antigen data. The model is the "Blood Bridge": a patient bridge
(bridge_id) is served by committed Bridge Donors; Emergency Donors are a backup pool;
Volunteers help coordinate. Matching is by blood_group (ABO+Rh) + proximity + eligibility
+ engagement — NOT antigen phenotyping.

TASK 1 — SCHEMA REFRAME (data/supabase_schema.sql + migration):
Add a `bridges` table representing recurring patient bridges: bridge_id (PK),
bridge_blood_group, quantity_required, expected_next_transfusion_date, frequency_in_days,
cycle_of_donations, status_of_bridge, lat, lng, created_at. Extend `donors` with:
role (Bridge Donor / Emergency Donor / Volunteer), donor_type, next_eligible_date,
cycle_of_donations, frequency_in_days, total_calls, calls_to_donations_ratio,
last_contacted_date, last_bridge_donation_date, user_donation_active_status,
churn_risk_reason (maps inactive_trigger_comment). Add a `bridge_memberships` table linking
donor_id ↔ bridge_id with role and last_bridge_donation_date. Keep antigen columns but mark
them Phase-2/unused. Write the migration as schema_v4_bridge.sql (idempotent, IF NOT EXISTS).

TASK 2 — SUPABASE SEED (data/seed_supabase.py):
Read the TSV. donor_id = SHA256(user_id) truncated to UUID form (deterministic, DPDP-safe).
Deduplicate donors by user_id (a user may appear under multiple bridges — insert donor once,
then create one bridge_membership per (user_id, bridge_id)). Map blood_group "A Positive"→"A+"
etc. is_active = (user_donation_active_status == "Active"). donation_count = donations_till_date.
Seed `bridges` from unique bridge_id rows. Use upsert with conflict on the PKs.

TASK 3 — NEO4J SEED (data/seed_neo4j.py):
Create (:Donor) nodes for unique users and (:Patient)/(:Bridge) nodes for unique bridge_ids.
For Bridge Donor rows create (:Donor)-[:SERVES_BRIDGE {role, frequency_days, last_bridge_donation_date,
on_cycle:boolean}]->(:Bridge). Create (:Donor)-[:COMPATIBLE_WITH {blood_group_match:true}]->(:Bridge)
ONLY on ABO+Rh compatibility (no antigen_score). Store next expected transfusion date on the Bridge.

TASK 4 — VALIDATION SUMMARY:
Print: total unique donors, donors by role, total bridges, bridge memberships,
counts by blood type, counts by eligibility_status, active vs inactive counts, and the
distribution of inactive_trigger_comment values.

EXPECTED OUTCOME:
- Schema and graph reflect the real NGO Bridge model (no hospital/antigen assumptions).
- Graph page shows the real Hyderabad bridge network.
- Engagement fields (calls ratio, cycle, eligibility) available for matching + churn.
```

## Prompt B1 — Fully Agentic Telegram Bot (Bedrock Tool-Calling)

```
CONTEXT:
WhatsApp is NOT used — Telegram is the sole conversational channel and must be fully agentic.
services/telegram_bot.py has slash commands and a 10-tool framework, now on Bedrock Nova Lite.
Every message (command OR natural language) must run through a tool-calling loop that picks a
tool, executes it, and replies in a warm, memory-aware, multilingual way. This is an NGO donor
assistant — tone is gratitude-first and community-driven.

TASK 1 — TOOL REGISTRY (verify/complete 10 tools as Bedrock-callable function schemas):
get_donor_profile, check_eligibility (uses next_eligible_date + 56-day rule), get_donation_history,
toggle_availability, get_badges (NGO engagement badges with progress %), get_leaderboard (city
top-10 by donations), get_impact_story, get_next_donation_date, report_medical_hold,
get_my_bridge (returns the bridge(s) this donor serves, next expected transfusion date, and
whether they are currently on-cycle). Replace any get_active_emergency clinical framing with
the bridge-centric version.

TASK 2 — AGENTIC LOOP (handle_message()):
(1) Fetch donor_memory → build ~200-token context (preferred_language, tone_profile,
emotional_anchors, badges, streak, bridge commitment). (2) Prepend as system message.
(3) Call Bedrock Nova Lite with message + context + tool schemas. (4) On tool_use, execute the
local function, feed tool_result back. (5) Loop until plain-text reply. (6) Ensure final reply is
in donor's preferred_language (one Bedrock translate pass if needed). (7) Send via Telegram,
update donor_memory.last_interaction.

TASK 3 — OCR ONBOARDING: photo message → download via Telegram file API → ocr_service.py
(Amazon Textract) → parse blood group → confirm with donor → update profile → log in
donor_verifications (type "ocr_card").

TASK 4 — CONSENT GATEWAY: on /start, before any tool is usable, check consent_data_storage +
consent_outreach_telegram via consent_service.py. If missing, send DPDP 2023 consent message with
inline Yes/No buttons and block all other functionality until granted.

EXPECTED OUTCOME:
- "am I eligible?" or "when's my next donation?" works in natural language, in donor's language.
- "which patient do I support?" returns their bridge + next transfusion date.
- All 10 tools reachable without slash commands; replies feel personal and NGO-warm.
```

## Prompt B2 — Amazon Comprehend (language) + Textract (OCR)

```
CONTEXT:
Replace the langdetect library (telegram_bot.py, outreach.py) and pytesseract+Pillow
(ocr_service.py) with AWS services, since deployment is on AWS.

TASK 1 — Comprehend: create services/language_service.py wrapping
comprehend.detect_dominant_language(); take highest-confidence code; map to internal language
names (hi, ta, te, kn, ml, bn, mr, gu, pa, ur). All callers use this wrapper — no other file
imports boto3 for language.

TASK 2 — Textract: in ocr_service.py remove pytesseract/Pillow; use Textract analyze_document()
(FORMS + LINES) on base64 image bytes from Telegram. Parse blood group patterns ("A+", "B Positive",
"O-", "AB Positive") and donor name. Keep the function signature identical: input image bytes →
dict {blood_group, name, raw_text}. Remove pytesseract and Pillow from requirements.txt.

EXPECTED OUTCOME:
- More accurate language detection on short Indian-script messages.
- OCR works without local tesseract binaries; signatures unchanged for callers.
```

---

# PHASE 1.5 — Smart Matching Module (NEW — Geo, Multi-Location, Donor Health)

> Run AFTER Phase 1 (A2 must be merged) and BEFORE Phase 2. Fixes the 5 known matching gaps.
> Dev A: M1 → M2 → M3. Dev B: (wait for M1 merge) → M4 → M5 → M6.

## Prompt M1 — Location Schema + Geohash + Geo Seed  ★ MERGE GATE (Dev A first)

```
CONTEXT:
BloodBridge AI matching is geographically broken. The patients table has NO lat/lng columns,
yet Neo4j match queries reference p.lat/p.lng — so geo-matching silently fails. Matching also
relies on exact city-string equality ("Hyderabad" != "hyderabad" != "Secunderabad"), which is
brittle. And each donor/patient supports only ONE location. This prompt fixes the data layer.
This is an NGO Bridge model — compatibility is ABO+Rh + geography + engagement, NOT antigens.

TASK 1 — NEW MULTI-LOCATION TABLES (data/schema_v4_locations.sql, idempotent IF NOT EXISTS):
Create patient_locations: location_id (PK), patient_id (FK), label (e.g. Home/Work/Hospital),
lat, lng, geohash (precision-6 string), is_primary (bool), priority_order (int 1..5), created_at.
Constraint: a patient may have 1 to 5 locations.
Create donor_locations: location_id (PK), donor_id (FK), label, lat, lng, geohash (precision-6),
is_primary (bool), priority_order (int), created_at. A donor may have N locations (backup areas).
Add a geohash TEXT column to donors (primary location geohash) for fast bucketing.
Keep antigen columns but they remain Phase-2/unused — matching must not read them.
Add indexes on geohash for both location tables and on donors.geohash.

TASK 2 — GEOHASH UTILITY (services/geo_service.py):
Create a pure-Python module exposing: encode_geohash(lat, lng, precision=6),
haversine_km(lat1, lng1, lat2, lng2), neighbors(geohash) (returns the 8 adjacent cells),
and radius_buckets() returning the 3 tier definitions R1<=5km, R2<=15km, R3<=30km. No external
geo library — implement geohash + haversine directly so there is no new system dependency.

TASK 3 — SEED LAT/LNG + GEOHASH (data/seed_supabase.py + data/seed_neo4j.py):
The real BWF dataset has latitude/longitude per row. Seed each donor's primary location into
donor_locations (is_primary=true, priority_order=1) AND set donors.lat/lng/geohash. For patients
(bridges): derive the patient/bridge location from the bridge's served donors' coordinates
(use the centroid of that bridge's donor lat/lng) and write it to patients.lat/lng plus one
patient_locations row (is_primary=true). Compute and store geohash for every row. In Neo4j,
set lat/lng AND a geohash property on every (:Donor) and (:Patient)/(:Bridge) node, and create a
POINT index plus a geohash index.

TASK 4 — VALIDATION:
Print: patients with non-null lat/lng (must be 100%), donor_locations rows, patient_locations rows,
geohash coverage %, and a sample of 5 donor→nearest-patient distances in km to prove geo works.

EXPECTED OUTCOME:
- Every donor and patient has lat/lng + geohash; geo-matching no longer silently broken.
- Multi-location tables exist (patient 1–5, donor N) ready for M2/M4.
- City-string matching replaced by coordinate/geohash bucketing.
- This is a MERGE GATE: merge M1 before Dev B starts M4.
```

## Prompt M2 — Geo Radius-Tier + Weighted Matching Engine  ★ FOCUS (Dev A)

```
CONTEXT:
With location tables seeded (M1), replace the naive Neo4j "ORDER BY antigen_score DESC, distance
ASC LIMIT 8" with a proper NGO weighted, radius-tiered matcher. Remove antigen ranking from the
default path. The matcher must search expanding geographic rings and keep a separate low-priority
"wide-net" list for the farthest ring.

CREATE: services/matching_engine.py (used by agents/neo4j_match.py — keep the agent's outward
interface and return shape unchanged so the LangGraph pipeline is untouched).

TASK 1 — RADIUS-TIER SEARCH (geohash + haversine ring expansion):
For a patient, gather all their patient_locations (1–5). For each location, search donors by
geohash neighborhood, classify each candidate into a ring using haversine_km:
R1 <= 5km, R2 <= 15km, R3 <= 30km. Search R1 first; only expand to R2, then R3, if the eligible
pool is below the target chain size (default 8). Donors found ONLY in R3 go on a separate
wide_net list and receive a distance penalty (lower final score) — they are last-resort backups.
A donor reachable from ANY of the patient's locations qualifies; use their best (smallest) distance.

TASK 2 — WEIGHTED MULTI-CRITERIA SCORE (no antigens):
Compute a transparent score per donor:
score = w1*blood_match(ABO+Rh exact) + w2*proximity_score(1 - dist/30) + w3*engagement_score
+ w4*eligibility_freshness(days since donation, capped) + w5*(1 - churn_score) - w6*radius_penalty
engagement_score derives from real fields: calls_to_donations_ratio (lower=better → invert),
donations_till_date, response_rate. Put the weights in a single WEIGHTS dict at the top of the
file so they are tunable. Bridge Donors committed to THIS patient's bridge get a fixed bonus
(they are the natural first responders). Return donors sorted by score DESC.

TASK 3 — WIRE INTO AGENT:
In agents/neo4j_match.py, replace the body of find_top_donors() to call
matching_engine.rank_donors(patient_id, target=8) and return the same dict shape the chain
builder already expects (donor_id, name, telegram_chat_id, phone, preferred_language, churn_score,
blood_type, distance_km, plus a new "ring" field 1/2/3 and "match_score"). Keep antigen_score in
the output only as a constant 1.0 placeholder for backward compatibility — do NOT compute Kell/
Duffy. The DEMO_MOCK_MODE fallback stays.

TASK 4 — EXPOSE RESULT METADATA:
Return both the primary ranked chain (top N) and the wide_net backup list so M5's auto-repair and
the UI can show "primary zone vs wide-net" donors. Persist the ring + match_score into blood_chains
(add columns ring INT, match_score FLOAT via the M1 migration file if not already present).

EXPECTED OUTCOME:
- Matching searches 3 expanding rings; R3-only donors are separated and penalized.
- Donors ranked by a tunable weighted score using real engagement signals, not antigens.
- LangGraph pipeline interface unchanged; chain rows now carry ring + match_score.
```

## Prompt M3 — Hungarian Multi-Patient Assignment (Dev A)

```
CONTEXT:
When multiple active patients/bridges compete for the same nearby donors, independent greedy
matching produces globally sub-optimal assignments (two patients fight over one ideal donor while
a third gets none). Add an optimal global assignment step using the Hungarian algorithm.

CREATE: services/assignment_optimizer.py

TASK 1 — BUILD COST MATRIX:
Given a set of active patients (each with their ranked candidate donors + match_score from M2) and
the union of candidate donors, build a cost matrix where cost = (1 - match_score). Donors not in a
patient's eligible/in-range set get a large prohibitive cost so they are never assigned there.

TASK 2 — SOLVE OPTIMALLY:
Use scipy.optimize.linear_sum_assignment (Hungarian / Kuhn-Munkres) to compute the global
minimum-cost assignment of donors to patients. Respect that each patient needs up to N donors:
solve in rounds (assign 1 best donor per patient per round, remove assigned donors, repeat until
chains are filled or candidates exhausted). Add scipy to requirements.txt (tell Dev A to add it,
since Dev A owns requirements.txt).

TASK 3 — INTEGRATION POINT (do NOT change single-patient flow):
Expose optimize_assignments(active_requests) used ONLY by a new admin/batch path (e.g. when the
demand-forecast or a coordinator triggers multi-patient planning). The normal single-emergency
pipeline keeps using M2's rank_donors. Add GET/POST /api/admin/optimize-assignments in api/admin.py
that returns the optimal donor→patient plan for all currently IN_PROGRESS requests (read-only
preview; does not auto-alert). Log the chosen plan to agent_traces.

TASK 4 — FALLBACK:
If scipy is unavailable or patient count is 1, fall back to M2 greedy ranking. Never block the
single-emergency path on the optimizer.

EXPECTED OUTCOME:
- Globally optimal donor sharing across concurrent patients (advanced over greedy).
- Read-only "optimal assignment" preview available to coordinators; single flow untouched.
```

## Prompt M4 — Multi-Location APIs (Dev B — after M1 merge)

```
CONTEXT:
M1 created patient_locations and donor_locations (one-to-many). Expose CRUD APIs so patients can
register 1–5 search locations and donors can register N backup areas. These feed M2's radius search.

TASK 1 — PATIENT LOCATION APIs (api/patients.py):
POST /api/patients/{id}/locations — add a location {label, lat, lng, is_primary, priority_order};
enforce max 5 per patient (reject 6th with 400). On insert, compute geohash via services/geo_service.
GET /api/patients/{id}/locations — list ordered by priority_order.
DELETE /api/patients/{id}/locations/{location_id} — remove (cannot delete the last remaining one).
PATCH to set is_primary (only one primary; unset others).

TASK 2 — DONOR LOCATION APIs (api/donors.py):
POST /api/donors/{id}/locations — add backup location (no max cap, but soft-limit 10).
GET /api/donors/{id}/locations · DELETE one · PATCH is_primary. Compute geohash on write.
When a donor's locations change, call the existing Neo4j edge rebuild path so matching sees the
new coordinates (reuse Neo4jMatcher.rebuild_edges_for_donor or its bridge-model equivalent).

TASK 3 — VALIDATION + DOCS:
Validate lat in [-90,90], lng in [-180,180]. Return geohash in responses. Add these endpoints to
the lib/api.ts client (typed functions) so the frontend (M6) can call them.

EXPECTED OUTCOME:
- Patients manage 1–5 locations; donors manage N backup areas, all geohashed.
- Location changes propagate to the graph so radius matching stays correct.
```

## Prompt M5 — Donor Health Self-Update + Auto-Repair Trigger (Dev B)

```
CONTEXT:
Donors can become temporarily unfit (illness, hospitalization, recent checkup). Today there is no
path for a donor to report this; medical_hold exists in schema but nothing sets it, and nothing
notifies staff/patient or replaces the donor in an active chain. Build the full flow. Depends on
M2 (radius matcher) and B1 (agentic Telegram bot).

TASK 1 — HEALTH UPDATE ENDPOINT (api/donors.py):
POST /api/donors/{id}/health-status accepting {available: bool, reason: str, hold_until: date|null,
note: str}. When available=false: set donors.medical_hold=true, medical_hold_until=hold_until,
churn_risk_reason/notes=reason; mark is_active accordingly. Log to donor_verifications or a new
donor_health_log table (health_id, donor_id, status, reason, hold_until, reported_via, created_at).
When available=true and hold expired: clear medical_hold.

TASK 2 — TELEGRAM TOOL (services/telegram_bot.py):
Add an 11th agentic tool report_medical_hold(reason, hold_until?) that calls the endpoint above.
Wire it so natural language like "I'm sick this week" or "got hospitalized, can't donate till 20th"
triggers it. Confirm warmly in the donor's language. (This plugs into B1's Bedrock tool loop.)

TASK 3 — AUTO-REPLACE IN ACTIVE CHAINS:
On health=unavailable, check blood_chains for any ACTIVE row where this donor is ALERTED/PENDING/
CONFIRMED in an IN_PROGRESS request. For each: mark that position DECLINED (reason "donor_medical_hold"),
update Neo4j, and trigger the existing chain_repair_agent / M2 matcher to pull the next-best donor
(prefer the wide_net/backup pool from M2). This reuses the repair mechanics — do not duplicate them.

TASK 4 — NOTIFY STAFF + PATIENT:
Notify staff via ntfy.sh + Telegram ("Donor X unavailable (reason), position auto-repaired with
Donor Y"). Notify the affected patient through their existing channel that their chain was updated
(DPDP-safe: anonymized donor reference, no medical detail leaked to patient). Broadcast a WebSocket
event so dashboards update live.

EXPECTED OUTCOME:
- A donor can self-report unfitness via Telegram or API.
- The active chain auto-repairs from the backup pool; staff + patient are informed.
- No donor stays in a chain after declaring themselves medically on hold.
```

## Prompt M6 — Location & Zone UI (Dev B — additive only)

```
CONTEXT:
Surface the new multi-location + radius features in the existing frontend. STRICT additive rule:
wrap/extend existing components, never rewrite working ones. Framer Motion is available.

TASK 1 — PATIENT LOCATION MANAGER (PatientDashboard.tsx):
Add a "My Search Locations" card: list current locations (label, distance, primary badge), an
"Add Location" form (label + map pin or lat/lng), max 5 enforced in UI, set-primary toggle,
delete. Use the M4 typed api.ts functions. Animate list add/remove with framer-motion (staggered).

TASK 2 — DONOR BACKUP AREAS (DonorPortal.tsx):
Add a "Backup Areas" card so donors add N areas they can travel to. Same add/list/delete pattern.
Also add a "Health / Availability" control: a "Report unavailable" button with reason + until-date
that calls POST /api/donors/{id}/health-status (M5). Animate the availability state change.

TASK 3 — ZONE / RADIUS VISUAL (dashboard/Map.tsx or Emergency.tsx, additive section):
On the existing Leaflet map, draw the 3 concentric radius rings (5/15/30km) around the active
patient location and color donor pins by ring (R1 green, R2 amber, R3 grey = wide-net). Show a
small legend. Do not change existing map data fetching — add an overlay layer only.

TASK 4 — MATCH TRANSPARENCY (Emergency.tsx chain cards):
Where chain donors are listed, show their ring (1/2/3) and match_score from M2 as a small badge,
so coordinators see why a donor was chosen and which are wide-net backups.

EXPECTED OUTCOME:
- Patients manage 1–5 locations; donors manage backup areas + report health, all in-app.
- Map shows radius rings and ring-colored donor pins; chain cards show ring + match score.
- Zero changes to existing component logic/state/API calls.
```

---

# PHASE 2 — Intelligence Agents (Hour 2)

## Prompt A3 — Demand-Forecast LangGraph Agent  ★ MAJOR FOCUS

```
CONTEXT:
The NGO needs to anticipate blood demand. Build a standalone LangGraph agent that forecasts,
per blood type, how many donations will be needed in the coming weeks. For an NGO the primary
demand signal is the recurring BRIDGE schedule: each bridge needs `quantity_required` units
every `frequency_in_days`, with the next event at `expected_next_transfusion_date`. Emergency
request history is a secondary multiplier. This directly answers the problem statement's
"anticipate availability/need" and "demand forecasting" requirements.

CREATE: agents/demand_forecast_agent.py

AGENT STATE (TypedDict): bridges (upcoming recurring schedules), historical_requests (past 90d),
forecast_horizon_days (default 28), forecast_by_blood_type (dict), forecast_by_week (list),
supply_by_blood_type (eligible-donor counts), confidence_scores (dict), shortage_alerts (list),
agent_summary (str), generated_at.

5-NODE PIPELINE:
NODE 1 DATA_COLLECTOR — From Supabase pull all bridges with expected_next_transfusion_date in
the horizon plus their frequency_in_days and quantity_required; expand recurring events across
the 4 weeks. Pull last 90d emergency_requests grouped by blood_type + week. Also count eligible
donors per blood type (eligibility_status eligible AND next_eligible_date <= week) as SUPPLY.

NODE 2 SCHEDULE_ANALYZER — Build week-by-week needed-units per blood type from bridge recurrence
(deterministic baseline). Flag any week/blood-type where demand > 5 units.

NODE 3 SUPPLY_GAP_NODE — Compare demand vs eligible-donor supply per blood type per week; compute
a gap and a confidence_score per blood type (low historical variance = high confidence). Apply a
historical multiplier from emergency_requests (e.g., O+ historically +20%).

NODE 4 BEDROCK_INSIGHT_NODE — Send structured forecast (weekly demand, supply, gaps, multipliers)
to Bedrock Claude Haiku; get a plain-English 30-day summary, specific shortage risks, and one
recommended action per under-supplied blood type. Store as agent_summary.

NODE 5 PERSIST_NODE — Write to new Supabase table demand_forecasts (forecast_id, generated_at,
forecast_horizon_days, forecast_json JSONB, supply_json JSONB, shortage_alerts text[], ai_summary,
blood_type_breakdown JSONB). Upsert system_cache key "latest_demand_forecast".

SCHEDULING + API: register in scheduler/jobs.py daily 6 AM IST; add POST /api/admin/forecast/run
(background trigger) and GET /api/admin/forecast (latest forecast JSON for the frontend chart).
If any week shows a deficit, push an ntfy.sh staff alert.

EXPECTED OUTCOME:
- Daily NGO demand forecast driven by real bridge cycles, with supply-gap detection.
- Admin sees "Week 2: need 8× O+, have 5 eligible → shortage" plus an AI action plan.
```

## Prompt A4 — Churn / Inactivity Model on Real Labels

```
CONTEXT:
ml/churn_predictor.py loads a static model trained on synthetic data. The real BWF dataset has
a labeled signal: user_donation_active_status (Active/Inactive) and inactive_trigger_comment
("Very limited activity despite multiple calls", "Not donated in last 1 year"). Retrain on real
features and automate monthly. This is the "engagement / anticipate willingness" requirement.

TASK 1 — RETRAIN (ml/train_churn.py): features from Supabase donors (now real):
calls_to_donations_ratio (primary), donation_count, response_rate (confirmed/alerted from chains),
days_since_donation, is_one_time_donor (donor_type), serves_active_bridge (has SERVES_BRIDGE edge),
total_calls. Label: is_active. Handle class imbalance with scale_pos_weight. Atomic save: write
churn_model_new.joblib, rename to churn_model.joblib only if validation AUC > 0.70. Log AUC/precision/
recall to a new ml_model_logs table.

TASK 2 — RISK TIERS aligned to real trigger comments:
0.0–0.3 LOW (no action) · 0.3–0.6 MEDIUM (send impact story) · 0.6–0.8 HIGH ("not donated in 1 year"
pattern → send re-engagement badge challenge) · 0.8–1.0 CRITICAL ("limited activity despite calls"
pattern → AI voice call). Store the intervention strategy in each tier definition.

TASK 3 — MONTHLY AUTOMATION (scheduler/jobs.py): cron 1st of month 02:00 IST → train, then batch-
score all donors into donors.churn_score/churn_risk. Wire POST /api/models/retrain to trigger on
demand for the demo.

EXPECTED OUTCOME:
- Real-data churn model with 7 meaningful features and 4 actionable tiers.
- Admin model card shows real AUC; monthly retrain automated.
```

## Prompt B3 — Voice Agent Hardening + SMS Fallback

```
CONTEXT:
agents/voice.py places Bolna.ai calls. Bolna is kept (best for Indian languages). Two gaps:
no fallback on unanswered/lost-webhook calls, and no Bolna dashboard spec.

TASK 1 — Track attempts: table voice_call_attempts (attempt_id, donor_id, request_id, call_id,
initiated_at, status PLACED/ANSWERED/UNANSWERED/FAILED/FALLBACK_SMS_SENT, attempts_count). In
scheduler/jobs.py add a 15-min job: for calls stuck PLACED > 12 min, increment attempts_count;
at attempts_count == 2, send Twilio SMS (services/sms_service.py) with request details + YES/NO,
mark FALLBACK_SMS_SENT.

TASK 2 — Idempotent webhook (api/webhooks.py): if call_id already ANSWERED/UNANSWERED return 200
without reprocessing; on HMAC (BOLNA_WEBHOOK_SECRET) failure return 403 and log (no exception).

TASK 3 — Create BOLNA_AGENT_CONFIG.md: agent name "BloodBridge Donor Coordinator", Sarvam Hindi
female voice (exact model), 2-sentence NGO intro (who's calling + which patient bridge needs help),
YES/NO structured capture firing the webhook, TRAI hours 8 AM–9 PM IST, 20s no-response → disconnect
→ SMS fallback.

EXPECTED OUTCOME:
- No donor stuck after an unanswered call; SMS within 15 min.
- Webhook safe under retries; Bolna configurable from the spec doc.
```

## Prompt B4 — Failure-Learning & Self-Improving Outreach Loop  ★ EXPANDED

```
CONTEXT:
The problem statement requires the system to "self-manage improvement steps and protocols via
failure learning." Today donor_memory is read by the planner but rarely written back, and there
is no failure classification. Close the loop AND add protocol self-adjustment.

TASK 1 — RESPONSE SIGNAL CAPTURE (api/webhooks.py + agents/monitor.py): on every confirm/decline/
no-response capture: response_time_seconds (alerted_at→responded_at), outcome (CONFIRMED/DECLINED/
NO_RESPONSE), channel (TELEGRAM/VOICE/SMS), message_text (if any), time_of_day bucket (IST).

TASK 2 — FAILURE CLASSIFICATION (services/donor_memory.py → analyze_response_and_update()):
one Bedrock Claude Haiku call returns JSON: updated tone_profile (warm/urgent/factual/inspirational),
optional new emotional_anchor, optimal_contact_window, best_channel, and a failure_reason label when
outcome != CONFIRMED (e.g., wrong_channel, wrong_time, message_too_long, fatigue_from_calls — the last
maps to the real "limited activity despite multiple calls" pattern). Update donor_memory accordingly
(append anchors only if new).

TASK 3 — PROTOCOL SELF-ADJUSTMENT (new table outreach_protocol_stats + planner.py): aggregate
outcomes by (channel, time_of_day, blood_type, donor_role). Maintain rolling success rates. The
planner must READ these stats and pick the channel+time with the highest success rate for that
donor segment instead of a fixed Telegram-first rule. When a segment's success rate for a channel
drops below 25% over the last 20 attempts, the planner automatically deprioritizes that channel for
that segment. Log every protocol change to agent_traces so admins can see the system learning.

TASK 4 — WIRE-IN (agents/outcome.py): call analyze_response_and_update() for ALL donors in the
chain (confirmed and declined). Recompute each donor's response_rate (last 90d) and write back to
donors so churn inputs stay fresh.

EXPECTED OUTCOME:
- tone_profile + best_channel adapt to real behavior within a few runs.
- Planner shifts channels/timing automatically based on measured success — visible failure-learning.
- response_rate stays current without manual entry.
```

---

# PHASE 3 — Frontend & Hardening (Hour 3)

## Prompt A5 — Demand-Forecast Section in Admin Panel (additive)

```
CONTEXT:
Add a forecast section to dashboard/Admin.tsx. Additive only — do not modify existing components.

TASK 1 — Hook: useDemandForecast in lib/api.ts calling GET /api/admin/forecast (returns generated_at,
ai_summary, forecast_by_week [{week_label, blood_type_counts}], supply_by_week, shortage_alerts[]).
TASK 2 — Grouped Recharts BarChart "Blood Demand — Next 28 Days": X = 4 week labels, one bar per
blood type, distinct Tailwind colors, custom legend. Overlay supply as a faint line/marker so
shortages are visible.
TASK 3 — AI summary card (styled like existing trace cards, expandable, relative timestamp).
TASK 4 — Shortage banners (shadcn Alert destructive) each with a "Start Outreach" button calling
the existing emergency/outreach endpoint pre-filled with the flagged blood type.
TASK 5 — Skeleton loaders matching chart + card heights while loading.

EXPECTED OUTCOME:
- Admin sees weekly demand vs supply and an AI action plan; shortages are one-click actionable.
```

## Prompt A6 — Production Configuration

```
CONTEXT:
Frontend runs in dev; backend has test defaults. Prepare for AWS.

TASK 1 — vite.config.ts: API proxy only in dev; production uses VITE_API_URL (EC2 URL). Create
.env.production (gitignored) placeholder. lib/api.ts: every fetch uses import.meta.env.VITE_API_URL,
no hardcoded localhost.
TASK 2 — Remove hardcoded VITE_STAFF_TOKEN fallbacks; rely only on JWT from localStorage after
real login; bypass components redirect to /login.
TASK 3 — core/config.py: if APP_ENV == production, fail startup when DEMO_MOCK_MODE is True, CORS
contains "*", or any password is "password"/"admin". main.py: CORS allow_origins from ALLOWED_ORIGINS
env (dev "*", prod = CloudFront URL).
TASK 4 — package.json: confirm build → dist/; add preview on 4173 for smoke testing.

EXPECTED OUTCOME:
- pnpm build clean; no test creds/localhost in prod; backend refuses insecure prod start.
```

## Prompt B5 — Framer Motion Polish (Additive Only)

```
CONTEXT:
Framer Motion is installed. Improve donor portal + dashboards. STRICT: wrap existing components,
never change their internal structure/logic/data/props. Inspiration: ibelick.com / 21st.dev style
(staggered reveals, spring counters, smooth status transitions, subtle gradient/aurora wrappers).

TASK 1 — DonorPortal badge grid: container variant staggerChildren 0.07 / delayChildren 0.1; each
badge motion.div hidden {opacity:0,scale:0.8,y:20} → visible spring (stiffness 200, damping 15);
locked badges visible scale 0.95.
TASK 2 — Lives-saved counter: motion.span ticks up (y -16→0, opacity 0→1, 0.4s ease-out) when value
changes.
TASK 3 — Emergency/bridge chain dots: animate backgroundColor over 0.4s on status change (pending gray,
alerted orange, confirmed green, declined red) — keep existing status→color logic, only add animate.
TASK 4 — Graph.tsx entrance: wrap in motion.div opacity 0→1 over 0.6s; pulsing placeholder while
loading (opacity [0.3,0.7,0.3], repeat Infinity, 1.5s).
TASK 5 — Availability toggle: after API success, scale 1→1.08→1 over 0.3s; briefly highlight the
impact/lives-saved area.

EXPECTED OUTCOME:
- Polished, lively UI for the demo; zero changes to existing logic/state/API calls.
```

## Prompt B6 — Supabase RLS + JWT Hardening

```
CONTEXT:
Responsible-AI requirement. Lock down sensitive tables to service_role and add a dedicated JWT secret.

TASK 1 — consent_records: SELECT/INSERT service_role only, no anon.
TASK 2 — donor_memory: SELECT to owner or service_role; UPDATE service_role; no anon INSERT.
TASK 3 — donor_verifications: service_role only for all ops.
TASK 4 — donors: expose a donors_public view (name, blood_type, city, is_active, donation_count, role);
anon reads use the view only — phone, lat/lng, churn_score, calls ratio excluded. Update frontend list
calls to the view.
TASK 5 — core/security.py: add JWT_SECRET env (64-char) used exclusively for JWT sign/verify; stop using
SUPABASE_SERVICE_KEY as the crypto secret. Add to .env.example.
TASK 6 — SECURITY.md: list policies, service_role-only tables, JWT rotation steps.

EXPECTED OUTCOME:
- No sensitive donor data reachable from the browser; consent data service_role-only; dedicated JWT secret.
```

---

# PHASE 4 — AWS Deployment (Hour 4)

## Prompt A7 — Dockerize Backend + EC2

```
CONTEXT:
Deploy FastAPI backend to AWS EC2 so Telegram/Bolna webhooks and the frontend reach it over HTTPS.

TASK 1 — Dockerfile (root of BloodBridge_AI_Backend): base python:3.11-slim; WORKDIR /app; copy
requirements first then pip install --no-cache-dir; copy app; expose 8000; CMD uvicorn main:app
--host 0.0.0.0 --port 8000 --workers 2. .dockerignore: .env, venv/, __pycache__, *.pyc, .git,
ml/models/*.joblib, tests/.
TASK 2 — S3 model loading: helper ml/__init__.py load_model_from_s3(bucket,key,local_path) via boto3
→ /tmp/models/ if not cached; churn/urgency/antigen scorers load from S3 bucket "bloodbridge-models"
on cold start.
TASK 3 — AWS_DEPLOY.md: EC2 t3.micro (Amazon Linux 2023, ports 22/80/443/8000), install Docker, ECR
repo bloodbridge-backend, build/tag/push via ecr get-login-password, run with --env-file, nginx reverse
proxy, Certbot TLS, set ALLOWED_ORIGINS to CloudFront URL.
TASK 4 — /health hardening: also check Bedrock (list_foundation_models), S3 (list_objects on
bloodbridge-models), Comprehend reachability; 200 only if all pass.

EXPECTED OUTCOME:
- Working image on EC2; all endpoints over HTTPS; models load from S3 and cache.
```

## Prompt A8 — Telegram Webhook + nginx HTTPS

```
CONTEXT:
Move the Telegram webhook from ngrok to the permanent EC2/nginx HTTPS URL and auto-recover on restart.

TASK 1 — setup_webhook.py: read TELEGRAM_BOT_TOKEN + APP_BASE_URL; call setWebhook with
url=APP_BASE_URL+"/webhook/telegram" and secret_token=TELEGRAM_WEBHOOK_SECRET; verify via
getWebhookInfo; print URL, pending_update_count, last_error_message.
TASK 2 — nginx/bloodbridge.conf: 80→443 redirect; 443 with Certbot certs; proxy to 127.0.0.1:8000
with X-Real-IP/X-Forwarded-For/Proto/Host; client_max_body_size 10m; proxy_read_timeout 120s; gzip JSON.
TASK 3 — systemd bloodbridge.service: run container on boot, --env-file, restart on failure (5s), then
run setup_webhook.py ~10s after start to re-register.

EXPECTED OUTCOME:
- Telegram delivers to EC2; HTTPS clean; webhook auto-re-registers within 15s of restart.
```

## Prompt B7 — Frontend S3 + CloudFront

```
CONTEXT:
Host the Vite SPA on S3 + CloudFront over HTTPS.

TASK 1 — AWS_DEPLOY.md frontend section: S3 bucket bloodbridge-frontend (ap-south-1), static hosting
(index.html as both index AND error doc for SPA routing), public-read policy, sync via
aws s3 sync dist/ s3://bloodbridge-frontend --delete.
TASK 2 — CloudFront: origin = S3 website endpoint; default root index.html; custom error 403→/index.html
(200) for React Router; PriceClass_100; compression on.
TASK 3 — deploy.sh: read EC2_BACKEND_URL → write .env.production → pnpm build → s3 sync → CloudFront
invalidation /*.
TASK 4 — Add CloudFront URL to backend ALLOWED_ORIGINS, restart container, verify /health 200 from
the CloudFront origin.

EXPECTED OUTCOME:
- SPA at CloudFront over HTTPS; deep links work; deploy.sh one-command publishes + busts cache.
```

## Prompt B8 — Final Smoke Test Checklist

```
CONTEXT:
Backend (EC2) + frontend (CloudFront) deployed. Verify every flow before demo. CREATE SMOKE_TEST.md
with a numbered 15-minute checklist, 5 sections, NGO-framed:

SECTION 1 INFRA: /health all services ok (incl. Bedrock, Comprehend, S3, Neo4j, Supabase); landing
loads; /dashboard/graph shows real Hyderabad bridge network; /dashboard/map shows banks; WS connects <3s.
SECTION 2 AUTH: signup test donor; donor login → JWT; staff login → admin reachable; admin without JWT → 401.
SECTION 3 CORE: POST emergency/bridge outreach → pipeline runs; trace shows all nodes with non-zero ms;
chain built from seeded bridge donors; Telegram /start → consent; natural-language "which patient do I
support?" → bridge answer (Bedrock tool-calling confirmed); GET /api/admin/forecast → AI summary + weekly
breakdown + supply gap.
SECTION 4 ML: donors sorted by churn_score (0–1, real); POST /api/models/retrain → 202 + log; eligibility
uses real next_eligible_date.
SECTION 5 DEMO HIGHLIGHTS: trigger outreach → chain dots animate orange→green live via WS; donor badges
stagger-animate; admin forecast chart renders demand vs supply with AI summary.
End note: log endpoint+error+timestamp for any failure; do not demo until all checks pass.

EXPECTED OUTCOME:
- One-person 15-min runbook; checks executable with browser + curl; demo highlights identified.
```

---

## What changed vs v3 (so the team knows)

- **Added A2 (Bridge-model reframe + real-data seed)** — the missing core; everything now matches the NGO dataset (roles, bridges, cycles), not hospital antigen logic.
- **Added PHASE 1.5 Smart Matching Module (M1–M6)** — fixes the 5 known matching gaps that neither the old code nor A1–B8 solved: patient lat/lng missing, brittle city-string matching, no multi-location model, no donor health self-update path, and leaking antigen logic. Dev A builds M1→M2→M3 (schema + weighted radius matcher + Hungarian assignment); Dev B builds M4→M5→M6 (multi-location APIs + donor health auto-repair + UI).
- **Expanded B4** into real **failure-learning + protocol self-adjustment** (a graded problem-statement requirement).
- **Reframed badges, tools, forecasting, and smoke tests** to NGO/Bridge language; removed Thalassemia/8-antigen/hospital framing.
- **Demand forecast (A3)** now models **recurring bridge cycles + supply-gap**, not hospital schedules.
- **Bedrock tiering**: Nova Lite (high-volume) + Claude Haiku (reasoning) + Sonnet (stories) to stretch $30.
- Kept v3's strong deployment, voice, RLS, and animation prompts.

## Algorithms used in the matching module (M1–M3)

- **Geohash bucketing** (precision-6) — replaces brittle city-string matching; O(1) zone lookup.
- **Haversine ring expansion** — 3 radius tiers (R1≤5km, R2≤15km, R3≤30km); R3-only donors = penalized wide-net backups.
- **Weighted multi-criteria scoring** — blood + proximity + engagement + freshness + (1−churn) − radius penalty; tunable weights (this is "weighted greedy done right").
- **DBSCAN (optional, in M1 seed)** — density-based patient zone clustering from real lat/lng (no preset cluster count).
- **Hungarian algorithm (Kuhn–Munkres, scipy)** — globally optimal donor↔patient assignment when multiple patients compete; the genuinely advanced upgrade over greedy.
