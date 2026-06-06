# BloodBridge AI — Version 2 Pre-Hackathon Roadmap
## Gap Analysis · Phase-by-Phase Execution Plan · Agentic IDE Ready
### Team Inqilab · Blend360 Hackathon · Generated from Full Codebase Audit

---

## EXECUTIVE SUMMARY

After a full end-to-end audit of the codebase (`full_code.txt`, `MASTER_STATUS.txt`, `BloodBridge_AI_PRD_v6_FINAL.md`, `AI4BAKCENDPROMPTS_1__1_.md`), BloodBridge AI has a **strong 70% complete foundation**. The backend pipeline, AI agents, and API layer are largely built. However, there are **critical gaps** that will prevent a live hackathon demo from succeeding:

1. The **Telegram Bot is not agentic enough** — it only has 3 tools and doesn't handle the full conversational profile/data access the vision describes.
2. The **DonorPortal frontend is mostly hardcoded** and not wired to the real donor's profile by phone/telegram identity.
3. The **Patient Dashboard and Transfusion Calendar** are skeleton pages with no real data wiring.
4. The **emergency flow has no real-time UI update** path that a judge can see live.
5. Several **new features** from your brief (phone-based profile lookup, Telegram as the identity gateway, medical record restriction compliance) are **missing entirely**.

This document breaks everything into phases with clear goals, steps, and atomic tasks.

---

## PART 1 — FULL GAP INVENTORY

### GAP-01: Telegram Bot — Not Truly Agentic
**What exists:** A React agent with only 3 tools (`trigger_blood_emergency`, `check_chain_status`, `get_my_impact`). Free-text messages go to LLM but the LLM has no tools for profile lookup, next donation date, eligibility check, language preference, or schedule viewing.

**What you want:** A donor sends "what is my profile" or "when is my next donation" and the bot fetches their real data by `telegram_chat_id`, responds in their language, and respects medical data restrictions (DPDP Act).

**Gap:** 8+ missing tools. Profile tool, eligibility tool, schedule tool, language-switch tool, next-donation tool, donation history tool, badge detail tool, and a medical data restriction gate that refuses to expose raw clinical data.

---

### GAP-02: DonorPortal Frontend — Hardcoded, Not Dynamic
**What exists:** `DonorPortal.tsx` fetches all donors and finds one by `donor_id` from `localStorage`. It defaults to `D-1001` if nothing is set. The "Urgent Match Found" card is 100% hardcoded (patient name "Aarav", 87% match, etc.). The leaderboard rank is hardcoded as "Rank #2 City".

**What you want:** The portal shows the real logged-in donor's data: actual badge count, real lives_saved, actual blood type, real rank from leaderboard, and real pending donation request (if any active chain node exists for that donor).

**Gap:** No real leaderboard rank API call. No real "active emergency request" card fetch. No phone number or Telegram ID-based login path.

---

### GAP-03: Patient Dashboard — Skeleton Page
**What exists:** `PatientDashboard.tsx` is a page file with basic structure but no real API calls for patient-specific data, upcoming transfusion schedule, or chain status.

**What you want:** Patient logs in, sees their next scheduled transfusion date, which donor is confirmed, blood type match details, and historical donation records.

**Gap:** No `GET /api/patients/{id}/schedule` endpoint. No `GET /api/patients/{id}/chain-history` endpoint. Patient dashboard doesn't call any of these.

---

### GAP-04: Emergency Chain — No Live Staff View
**What exists:** WebSocket endpoint exists at `/ws/emergencies`. `Emergency.tsx` dashboard page exists with a WebSocket hook. But the chain visualization only shows a static or partially-fetched list — it doesn't animate or update in real-time when donors confirm or decline.

**What you want:** Staff triggers an emergency → dashboard shows the 8-donor chain expanding with live status updates (ALERTED → CONFIRMED / DECLINED) within 5 seconds, suitable for a live hackathon demo.

**Gap:** The WS broadcast events (`donor_confirmed`, `donor_declined`) exist in backend code but the frontend `Emergency.tsx` doesn't handle them to update individual chain node states.

---

### GAP-05: Auth Flow — Fragile Identity Binding
**What exists:** `/donor/login` stores `donor_id` in `localStorage`. `/patient/login` stores `patient_id`. But `/api/auth/signup` and `/api/auth/login` use a generic flow that doesn't enforce Telegram chat ID binding.

**What you want:** When a donor registers via Telegram (`/register B+`), their `telegram_chat_id` is stored in Supabase. When they later log into the web portal, the system can look them up by phone number OR by confirming their telegram identity.

**Gap:** No phone number → donor_id lookup endpoint. No Telegram deep link for web login. Web login and Telegram onboarding are two separate silos.

---

### GAP-06: Proactive Scheduler — Partially Wired
**What exists:** `scheduler/jobs.py` has `run_proactive_scheduler()` that calls `get_patients_due_in_days()` and triggers emergencies. `transfusion_calendar.py` has `auto_generate_schedule_from_history()`.

**What you want:** The scheduler runs on APScheduler, auto-generates schedules for patients who have 2+ completed transfusions, and triggers warm outreach 5-7 days before the scheduled date.

**Gap:** `auto_generate_schedule_from_history()` is defined but never called automatically. The scheduler job only reads existing `transfusion_schedule` rows — it doesn't create new ones. This means if the Supabase `transfusion_schedule` table is empty, the proactive feature never fires.

---

### GAP-07: Medical Data Restriction (DPDP 2023) — Telegram Gap
**What exists:** `/mydata` command returns raw donor data including phone number. DPDP consent system exists but is not enforced in the Telegram bot for data retrieval.

**What you want:** The Telegram bot must never send medical-adjacent data (antigen flags, antibody history, clinical urgency scores) via Telegram per the Digital Personal Data Protection Act 2023. Non-sensitive data (blood type, badge, donation count) is fine. Full medical profile must redirect to the secure web portal.

**Gap:** `/mydata` command exposes phone number and consent status via Telegram. No check exists to restrict sensitive fields. The bot needs a "medical data gate" that redirects clinical queries to the web portal URL.

---

### GAP-08: Donor Registration — No Phone Number Capture
**What exists:** `/register B+` creates a donor with `name: "Telegram Donor {last4}"` and no phone number. City defaults to "Hyderabad".

**What you want:** During registration, the bot should ask for the donor's name, city, and phone number (or at minimum name and city) in a multi-step conversational flow before completing registration.

**Gap:** Single-command registration loses critical profile data. No multi-turn conversation state for registration flow.

---

### GAP-09: Impact Story Delivery — Partially Wired
**What exists:** `services/impact_story.py` has `generate_impact_story()` and `send_impact_story_via_telegram()`. `outcome_agent` calls `generate_impact_story` and then `send_impact_story_via_telegram`.

**What you want:** 2 hours after a COMPLETED donation, the donor gets a warm Gemini-generated story about the patient they helped (anonymized).

**Gap:** The 2-hour delay mechanism is missing. Currently, the impact story sends immediately when outcome is recorded, not after a 2-hour delay. APScheduler needs a one-shot job for this.

---

### GAP-10: Neo4j Graph Dashboard — Empty Without Seed Data
**What exists:** `GET /api/donors/graph/data` endpoint returns Neo4j nodes and edges. `Graph.tsx` frontend renders a force-directed graph.

**What you want:** A pre-seeded graph showing donors connected to patients via `COMPATIBLE_WITH` edges, with the chain visualization showing a live emergency chain.

**Gap:** If Neo4j is empty (as noted in `MASTER_STATUS.txt` under Known Issue #3), the graph shows nothing. The seed script (`seed_neo4j.py`) exists but must be explicitly run. No auto-seed on startup.

---

### GAP-11: Blood Bank Map — Static Mock Data
**What exists:** `MapView.tsx` renders a Leaflet map. `GET /api/blood-banks` queries Supabase. 8 Hyderabad blood banks are seeded in `seed_supabase.py`.

**What you want:** Real-time blood bank availability, filtered by blood type, shown on the map when an emergency is raised.

**Gap:** Blood bank data is static seed data, not e-RaktKosh live data. The scraper exists but the 15-minute cache update is not scheduled by default. Map doesn't update when an emergency is raised.

---

### GAP-12: Admin Dashboard — Staff Token Placeholder
**What exists:** All admin endpoints exist and work. Frontend `Admin.tsx` page exists.

**What you want:** A working admin dashboard for demo day that shows real analytics, agent traces, and health status without requiring manual token setup.

**Gap:** `VITE_STAFF_TOKEN=test-admin-token` in the frontend .env is a placeholder. The real token must be fetched from the `staff` table in Supabase. This setup step is manual and undocumented for demo day.

---

### MISSING FEATURE-01: Phone Number → Profile Lookup
**Described in your brief:** "if about my profile then AI should give their profile data based on the phone number they using"

**Status: Does NOT exist.** No endpoint or bot command looks up donor data by phone number. The only identity binding is by `telegram_chat_id` after explicit `/register` command.

---

### MISSING FEATURE-02: Conversational Profile Access with Data Tiers
**Described in your brief:** Different access tiers — basic profile data is fine on Telegram, but medical records (antigen flags, clinical history) must be restricted.

**Status: Partially exists** — `/mydata` exists but doesn't tier the data. No data tier logic exists.

---

### MISSING FEATURE-03: Donor Can See Upcoming Transfusion Schedule
**Described in your brief:** Donors should be able to ask the bot "when is my next donation" and get an answer.

**Status: Does NOT exist.** No bot command or tool fetches the `transfusion_schedule` for a donor. The schedule is only used by the proactive scheduler internally.

---

### MISSING FEATURE-04: Deep Link from Telegram to Web Portal for Sensitive Data
**Described in your brief:** Medical data should redirect to the web app.

**Status: Does NOT exist.** No deep link mechanism. Telegram bot sends everything in-chat.

---

### MISSING FEATURE-05: Multi-Language Auto-Switch in Bot
**Described in brief:** Bot should respond in user's preferred language automatically.

**Status: Partially exists** — `langdetect` is imported and language is stored in `donor_profile`. But the bot's system prompt says "Reply with English as the primary language first, followed by the user's preferred language". This means English always comes first. If the donor only speaks Telugu, this is a poor UX.

---

### MISSING FEATURE-06: Donor Can Pause / Resume Donation Availability
**Needed for production but missing:** Donors going on vacation or medical hold should be able to text the bot "I'm unavailable for 2 weeks" and be marked inactive.

**Status: Does NOT exist.** No `/pause` or `/available` command. No availability management.

---

---

## PART 2 — PHASE-BY-PHASE DEVELOPMENT PLAN

---

### PHASE 0 — ENVIRONMENT STABILIZATION
**Goal:** Get the existing code running end-to-end before adding anything new.
**Time estimate:** 2–3 hours

#### Step 0.1 — Backend Startup
- Task: Ensure `python -m uvicorn main:app --reload --port 8000` starts without import errors
- Task: Confirm all environment variables in `.env` are filled (especially `TELEGRAM_WEBHOOK_URL` after ngrok)
- Task: Run `python -m pytest tests/test_e2e_pipeline.py -v` and confirm 29/29 passing

#### Step 0.2 — Database Seed Verification
- Task: Open Supabase dashboard → verify 11 required tables exist: `donors`, `patients`, `emergency_requests`, `blood_chains`, `donor_memory`, `donor_verifications`, `agent_traces`, `consent_records`, `staff`, `transfusion_schedule`, `blood_banks`
- Task: If any table is missing, run `supabase_schema.sql` (create from PRD schema if file doesn't exist)
- Task: Run `python data/seed_supabase.py` to populate synthetic donors and patients
- Task: Run `python data/seed_neo4j.py` to create Neo4j nodes and `COMPATIBLE_WITH` edges

#### Step 0.3 — Frontend Startup
- Task: Navigate to `BloodBridge_AI_frontend/artifacts/bloodbridge`
- Task: Run `node node_modules/vite/bin/vite.js` (or `pnpm run dev`)
- Task: Confirm all 13 pages render without blank screen or console errors

#### Step 0.4 — Telegram Webhook Setup
- Task: Sign up at ngrok.com, get auth token
- Task: Run `ngrok config add-authtoken <TOKEN>` then `ngrok http 8000`
- Task: Run `python setup_webhook.py` to register webhook URL
- Task: Open Telegram → search bot → send `/start` → confirm bot responds

#### Step 0.5 — Admin Token Setup
- Task: In Supabase SQL editor run: `SELECT auth_token FROM staff WHERE role = 'Admin' LIMIT 1;`
- Task: Copy the token → paste into `BloodBridge_AI_frontend/artifacts/bloodbridge/.env` as `VITE_STAFF_TOKEN`
- Task: Reload admin dashboard → confirm health, traces, and analytics load real data

---

### PHASE 1 — BACKEND: NEW API ENDPOINTS
**Goal:** Add the missing REST endpoints that v2 frontend and bot need.
**Time estimate:** 3–4 hours

#### Step 1.1 — Patient Schedule Endpoint
- Task: In `api/patients.py`, add `GET /api/patients/{id}/schedule` — queries `transfusion_schedule` table by `patient_id`, returns list of scheduled entries with `scheduled_date`, `hospital`, `status`, `days_until`
- Task: Add `GET /api/patients/{id}/chain-history` — queries `blood_chains` joined with `emergency_requests` for all completed/in-progress chains for this patient, returns summary of each with confirmed donor names (anonymized to first name + last initial)

#### Step 1.2 — Donor Profile by Phone Number
- Task: In `api/donors.py`, add `GET /api/donors/lookup?phone={phone_number}` — queries Supabase `donors` table by `phone` field, returns donor profile if found
- Task: This endpoint must be rate-limited (1 req/second per IP) using existing `slowapi` limiter
- Task: Add `GET /api/donors/lookup?telegram_chat_id={chat_id}` — alternative lookup by Telegram chat ID, used by the bot and web portal Telegram login

#### Step 1.3 — Leaderboard Rank for Single Donor
- Task: In `api/donors.py`, add `GET /api/donors/{id}/rank` — queries the leaderboard for the donor's city and returns their current rank number and lives_saved count
- Task: This data should come from the `leaderboard_cache` Supabase table (already used by the existing `/leaderboard` endpoint)

#### Step 1.4 — Active Emergency for Donor
- Task: In `api/donors.py`, add `GET /api/donors/{id}/active-request` — queries `blood_chains` for any chain node with `donor_id` = id and `status` IN ('ALERTED', 'SMS', 'VOICE'), joins with `emergency_requests` to get patient blood type, urgency, hospital name, and compatibility score
- Task: Returns `null` if no active request exists, or a single active request object if one exists
- Task: This powers the "Urgent Match Found" card in DonorPortal

#### Step 1.5 — Schedule Endpoints
- Task: In `api/admin.py` (or a new `api/schedule.py`), ensure `GET /api/schedule?days=30` and `POST /api/schedule` work for staff to manually create schedule entries
- Task: Add `POST /api/patients/{id}/auto-schedule` — triggers `auto_generate_schedule_from_history(patient_id)` as a background task for patients with 2+ completed transfusions

#### Step 1.6 — Availability Toggle for Donors
- Task: In `api/donors.py`, add `POST /api/donors/{id}/availability` — accepts body `{"available": false, "until": "2026-06-20"}`, updates donor `is_active` flag and adds a `medical_hold_until` date
- Task: The eligibility filter in `ml/eligibility_filter.py` already checks `medical_hold` — ensure the field name matches what the existing checker reads

---

### PHASE 2 — BACKEND: PROACTIVE SCHEDULER FIXES
**Goal:** Make the proactive outreach actually trigger automatically.
**Time estimate:** 1–2 hours

#### Step 2.1 — Auto-Schedule Generation on Startup
- Task: In `scheduler/jobs.py`, add a startup job that runs once at app start: query all patients with 2+ COMPLETED emergency requests but no PENDING `transfusion_schedule` entries, then call `auto_generate_schedule_from_history(patient_id)` for each
- Task: Register this startup job in `main.py` using APScheduler `add_job(..., trigger='date', run_date=datetime.now() + timedelta(seconds=30))`

#### Step 2.2 — Impact Story Delayed Delivery
- Task: In `agents/outcome.py` (or wherever outcome_agent fires), after marking a chain COMPLETED and generating the impact story, instead of calling `send_impact_story_via_telegram()` immediately, schedule a one-shot APScheduler job with `run_date = datetime.now() + timedelta(hours=2)`
- Task: The one-shot job calls `send_impact_story_via_telegram(donor_id, story)`
- Task: Store `story` in `donor_memory` table under a `pending_impact_story` key so the scheduler can retrieve it after 2 hours even if the app restarts

#### Step 2.3 — Blood Bank Cache Auto-Update
- Task: In `scheduler/jobs.py`, register the blood bank scraper as an APScheduler job running every 15 minutes: calls `blood_bank_scraper.scrape_and_cache()` which updates the `blood_banks` Supabase table
- Task: Register this in `main.py` alongside the existing churn batch job

---

### PHASE 3 — TELEGRAM BOT: AGENTIC UPGRADE
**Goal:** Transform the bot into a genuinely intelligent assistant that handles all donor interactions, respects data tiers, and is multi-lingual.
**Time estimate:** 4–6 hours

#### Step 3.1 — Add New LangGraph Tools to the Bot

**Tool: `get_my_profile`**
- Task: Create a tool that accepts `chat_id` (from system prompt context)
- Task: Fetches donor record by `telegram_chat_id`
- Task: Returns ONLY non-sensitive fields: name, blood_type, city, donation_count, lives_saved, is_active, preferred_language
- Task: Does NOT return: phone, antibody_flags, antigen_data, medical_hold reason

**Tool: `get_my_schedule`**
- Task: Fetches the next 1–2 upcoming `transfusion_schedule` entries for the donor's assigned patients (from `blood_chains` → `emergency_requests` → `transfusion_schedule`)
- Task: Returns date, hospital name, and days_until
- Task: If no schedule exists, returns a warm message saying "No upcoming donations scheduled — you'll get a notification when a patient needs you"

**Tool: `get_my_eligibility`**
- Task: Calls `check_donor_eligibility(donor_profile, {})` to check the donor's current eligibility
- Task: Returns eligible=true/false with a human-readable reason if not eligible
- Task: Never mentions the patient's clinical data — only references the donor's own eligibility

**Tool: `get_next_donation_date`**
- Task: Calculates 56 days from the donor's `last_donation_date`
- Task: Returns the date in the donor's preferred language format (e.g., "22 June 2026" in English, "22 जून 2026" in Hindi)

**Tool: `update_my_language`**
- Task: Accepts `language_code` (hi, te, ta, en, etc.)
- Task: Updates `preferred_language` in the `donors` table for this chat_id
- Task: Confirms the change in the new language

**Tool: `set_my_availability`**
- Task: Accepts `available: bool` and optional `until_date: str`
- Task: Calls `POST /api/donors/{id}/availability` internally
- Task: If donor sets unavailable, sends warm acknowledgment: "Understood! We'll pause donation requests until [date]. Thank you for letting us know."

**Tool: `get_medical_data_portal_link`**
- Task: When donor asks for clinical data (antigen flags, antibody history, hemoglobin), this tool returns a message explaining that detailed medical data is protected under DPDP 2023 and must be accessed via the secure web portal
- Task: Returns a formatted message with the web portal URL and instructions to log in with their Telegram-verified identity

#### Step 3.2 — Multi-Turn Registration Flow
- Task: Replace the single-command `/register B+` with a conversational flow using a simple session state dict stored in memory (keyed by `chat_id`)
- Task: Flow: `/register` → bot asks "What is your blood type? (e.g., B+, O-)" → user replies → bot asks "What is your city?" → user replies → bot asks "What is your name?" → user replies → bot creates donor record
- Task: Session state stores partial registration data under `registration_sessions[chat_id]`
- Task: If user sends a photo during registration, skip the blood type question and use OCR result instead

#### Step 3.3 — Language-First Responses
- Task: Modify the system prompt for the React agent to remove "Reply with English as the primary language first" and replace with: "Always reply ONLY in the donor's preferred language. If preferred_language is 'hi', reply in Hindi. If 'te', reply in Telugu. If 'en' or unknown, reply in English."
- Task: Pass `preferred_language` from `user_context` into the system prompt dynamically

#### Step 3.4 — Medical Data Restriction Gate
- Task: In `handle_command()` and in the React agent's system prompt, add explicit instruction: "NEVER provide antibody_flags, antigen_scores, hemoglobin_level, kell_negative status, or any clinical diagnostic data via Telegram. If asked, always invoke `get_medical_data_portal_link` tool."
- Task: Add a pre-check in `get_user_context()` that strips any clinical fields before passing donor profile to the LLM context

#### Step 3.5 — Update `/help` Command
- Task: Update the `/help` response to list all new commands: `/profile`, `/schedule`, `/eligibility`, `/nextdonation`, `/language [code]`, `/pause [days]`, `/resume`, `/badges`, `/leaderboard`, `/consent`, `/mydata`, `/revoke [type]`, `/deletedata`
- Task: The help message should be in the donor's preferred language

---

### PHASE 4 — FRONTEND: DONOR PORTAL FULL WIRING
**Goal:** Make DonorPortal.tsx fully dynamic with real API data.
**Time estimate:** 3–4 hours

#### Step 4.1 — Identity and Auth
- Task: In `DonorLogin.tsx`, add a phone number field alongside the existing donor ID field
- Task: On submit, first try `GET /api/donors/lookup?phone={phone}` — if found, store `donor_id` in localStorage
- Task: If not found by phone, fall back to donor_id direct entry
- Task: Add a "Connect via Telegram" link that opens `https://t.me/[BOT_USERNAME]` — after the donor sends `/start` to the bot, the bot stores their `telegram_chat_id` which the web portal can then verify

#### Step 4.2 — Real Profile Data
- Task: In `DonorPortal.tsx`, replace `getDonors()` call with `GET /api/donors/{donor_id}` (single donor endpoint)
- Task: Add `GET /api/donors/{id}/rank` call to fetch real leaderboard rank and display instead of hardcoded "Rank #2 City"
- Task: Display actual `badges` array from the donor record — show unlocked badges and greyed-out locked ones

#### Step 4.3 — Real Active Emergency Card
- Task: Add a `useEffect` that calls `GET /api/donors/{id}/active-request` on mount
- Task: If an active request exists, show the emergency card with real data: patient blood type, hospital name, urgency level, compatibility score from the chain
- Task: If no active request, show an "All clear" card with a placeholder message: "No urgent requests right now. We'll notify you via Telegram when your blood type is needed."
- Task: Replace the hardcoded "Aarav, 7 years old" and "87% Match" with real values from the API response

#### Step 4.4 — Telegram Connection Status
- Task: Check if `donor.telegram_chat_id` is non-null in the API response
- Task: If null, show "Connect Telegram" button with deep link to bot
- Task: If non-null, show "Connected ✅" with the username if available

#### Step 4.5 — Impact History Section
- Task: Add a new section below badges: "Your Impact Stories" — shows the last 3 Gemini-generated stories from `donor_memory.impact_stories` (if the field exists)
- Task: If empty, show placeholder: "After each donation, you'll see the story of who you helped here."

---

### PHASE 5 — FRONTEND: PATIENT DASHBOARD WIRING
**Goal:** Give patients a functional view of their care status.
**Time estimate:** 2–3 hours

#### Step 5.1 — Patient Authentication
- Task: `PatientLogin.tsx` currently stores `patient_id` in localStorage — this is fine; no changes needed

#### Step 5.2 — Patient Dashboard API Calls
- Task: In `PatientDashboard.tsx`, add calls to:
  - `GET /api/patients/{id}` — basic patient info
  - `GET /api/patients/{id}/schedule` — upcoming transfusion dates (new endpoint from Phase 1)
  - `GET /api/emergencies?patient_id={id}&limit=3` — recent emergency requests and their chain status
- Task: Display the next scheduled transfusion date prominently at the top of the page
- Task: Show a timeline of the last 3 emergency requests with their outcomes (COMPLETED, IN_PROGRESS, ESCALATED)

#### Step 5.3 — Chain Status View for Patient
- Task: For each in-progress emergency, show a visual chain: list of 8 chain positions with status icons (pending, alerted, confirmed, declined)
- Task: This uses data from `GET /api/emergencies/{id}/chain` which already exists
- Task: Keep donor names anonymous (show "Donor #1", "Donor #2") per DPDP compliance

---

### PHASE 6 — FRONTEND: LIVE EMERGENCY DASHBOARD
**Goal:** Make the staff emergency dashboard show real-time chain updates for demo day.
**Time estimate:** 2–3 hours

#### Step 6.1 — WebSocket Event Handling in Emergency.tsx
- Task: The existing `useWebSocket` hook connects to `/ws/emergencies` and receives messages
- Task: In `Emergency.tsx`, add handlers for these specific message types that the backend already broadcasts:
  - `donor_confirmed`: update the chain node visual to green ✅
  - `donor_declined`: update the chain node visual to red ❌
  - `chain_repair_started`: show a spinner on the next pending node
  - `emergency_escalated`: show a red alert banner at the top
  - `pipeline_started`: show the chain visualization with all nodes in PENDING state
- Task: Use React `useState` to maintain chain node statuses and update them when WS messages arrive

#### Step 6.2 — Demo Mode Trigger
- Task: Add a "Trigger Demo Emergency" button on the dashboard that calls `POST /api/emergencies` with a pre-filled test payload (blood type O+, hospital KIMS Hyderabad, a test patient ID from the seed data)
- Task: This is the judge-facing demo button — one click shows the full pipeline running live
- Task: The button should only appear when `VITE_STAFF_TOKEN` is set (i.e., staff is authenticated)

#### Step 6.3 — Chain Timeline Visualization
- Task: Replace any static donor list with a proper visual chain: 8 numbered nodes connected by lines
- Task: Each node shows: position number, donor blood type (not name, for DPDP), status badge (PENDING/ALERTED/CONFIRMED/DECLINED), and elapsed time since alert was sent
- Task: Animate status changes with a smooth color transition (yellow → green or red)

---

### PHASE 7 — FRONTEND: ADMIN DASHBOARD POLISH
**Goal:** Make the admin dashboard demo-ready without manual token setup.
**Time estimate:** 1–2 hours

#### Step 7.1 — Dev Token Auto-Setup
- Task: In `Admin.tsx`, if `VITE_STAFF_TOKEN` equals `test-admin-token` (the placeholder), show a banner: "⚠️ Using placeholder token — admin data may not load. Run: SELECT auth_token FROM staff WHERE role = 'Admin' LIMIT 1 in Supabase."
- Task: Add a token input field in the admin page header so staff can paste their real token without touching `.env`

#### Step 7.2 — Agent Trace Visualization
- Task: The `/api/admin/traces` endpoint returns the last 5 agent traces
- Task: In `Admin.tsx`, render each trace as an expandable card showing: request_id, patient_id, nodes visited, timestamps per node, and final outcome
- Task: This is a key demo element — show judges the 9-node pipeline visually

#### Step 7.3 — Real-Time Health Indicators
- Task: `GET /api/admin/health` returns 9 service statuses
- Task: Show each service as a traffic light: green (reachable), yellow (degraded), red (down)
- Task: Auto-refresh every 30 seconds using `setInterval`

---

### PHASE 8 — INTEGRATION: END-TO-END DEMO SCRIPT
**Goal:** Define and test the exact demo sequence judges will see.
**Time estimate:** 2–3 hours

#### Step 8.1 — Demo Data Seeding
- Task: Create `data/seed_demo.py` that inserts exactly the demo scenario: 1 patient (blood type B-, with kell_negative flag), 8 donors (mix of blood types, correct compatibility), 1 staff user, 1 transfusion schedule entry 6 days from today
- Task: This script should be idempotent (safe to run multiple times without duplicates)
- Task: Also seed Neo4j: run `seed_neo4j.py` which creates `COMPATIBLE_WITH` edges between these specific donors and the demo patient

#### Step 8.2 — Demo Sequence Documentation
The recommended demo sequence for judges (5 minutes):

1. Open `http://localhost:5173` → show Landing page
2. Open Telegram → send `/start` to bot → show consent flow → send `HAAN`
3. Send `/register B-` → show donor registered
4. Send `/profile` → show dynamic profile with blood type and city
5. Switch to staff admin browser tab → click "Trigger Demo Emergency"
6. Watch Emergency dashboard → show 8-donor chain expand with real-time status updates
7. On Telegram (as donor): receive emergency outreach message → reply "YES"
8. Dashboard updates donor node to CONFIRMED (live WebSocket update)
9. Admin sees agent trace showing all 9 pipeline nodes
10. 2 hours later (skip ahead in demo): show impact story received on Telegram

#### Step 8.3 — Fallback for Live Demo Failures
- Task: Create a `demo_mock_mode` flag in `core/config.py`
- Task: When enabled, all external API calls (Bolna, e-RaktKosh, Neo4j) return realistic mock responses
- Task: This ensures the demo doesn't fail if ngrok drops or Supabase has a timeout
- Task: Mock responses should be pre-loaded JSON fixtures in `data/mock_responses/`

---

### PHASE 9 — MISSING FEATURES IMPLEMENTATION (NEW)

#### Step 9.1 — Phone Number → Profile Gateway
- Task: Implement `GET /api/donors/lookup?phone={number}` (from Phase 1.2)
- Task: In the Telegram bot, when a registered donor's message comes in with `user_context.role == "Donor"` but no phone on record, the bot asks: "To link your phone number for full access, please share your contact" and uses Telegram's `contact` type message handler to capture it
- Task: Once phone is stored, subsequent profile lookups are possible from both web and bot

#### Step 9.2 — Deep Link: Telegram → Web Portal
- Task: When the bot receives a query for medical/clinical data, it responds with: "For your complete medical records, please visit: [web portal URL]?donor={donor_id}&token=[one-time-token]"
- Task: Generate a one-time secure token (UUID, stored in Supabase with 24h expiry) that pre-authenticates the donor in the web portal without requiring password
- Task: Add `GET /api/auth/telegram-login?token={token}` endpoint that validates the one-time token and returns a JWT for the web session

#### Step 9.3 — `/pause` and `/resume` Commands
- Task: Add `/pause [days]` command to `handle_command()` — calls `POST /api/donors/{id}/availability` with `available=false, until=today+days`
- Task: Add `/resume` command — calls the same endpoint with `available=true`
- Task: Both commands respond in the donor's preferred language

#### Step 9.4 — Language Auto-Detection on First Message
- Task: When a `Guest` user sends their first non-command message, use `langdetect` on the message text to detect language
- Task: Store detected language in the registration session or donor record after registration
- Task: This removes the need for explicit `/language te` commands for most users

---

### PHASE 10 — DEPLOYMENT & DEMO HARDENING
**Goal:** Ensure everything works on Render.com for the live demo.
**Time estimate:** 2–3 hours

#### Step 10.1 — Render.com Configuration
- Task: Ensure `render.yaml` has: web service (uvicorn), cron service (churn batch daily), all environment variables listed
- Task: Add `UptimeRobot` monitor for the Render URL to prevent free-tier sleep
- Task: Test full pipeline on Render URL (not localhost) before demo day

#### Step 10.2 — Vercel Frontend Deployment
- Task: Deploy frontend to Vercel with `VITE_API_URL` pointing to the Render.com backend URL
- Task: Test all 13 pages on the Vercel deployment

#### Step 10.3 — Telegram Webhook on Production
- Task: Update `TELEGRAM_WEBHOOK_URL` in Render.com environment variables to point to the Render URL (not ngrok)
- Task: Run `setup_webhook.py` with `WEBHOOK_URL=https://[your-render-app].onrender.com/webhook/telegram`
- Task: Test the full Telegram flow on the production URL

#### Step 10.4 — Final E2E Test Checklist
- Task: Run `pytest tests/test_e2e_pipeline.py -v` → confirm 29/29 passing
- Task: Manually test all 13 Telegram commands
- Task: Manually trigger one full emergency pipeline and confirm chain + WS updates + Telegram alerts all work
- Task: Confirm Neo4j graph dashboard shows real data
- Task: Confirm Admin dashboard shows real analytics and health status

---

## PART 3 — FEATURE PRESENCE MATRIX

| Feature | Exists? | Gap? | Phase to Fix |
|---|---|---|---|
| 9-node LangGraph pipeline | ✅ Complete | None | — |
| 8-antigen ISBT compatibility scorer | ✅ Complete | None | — |
| XGBoost urgency scorer | ✅ Complete | None | — |
| XGBoost churn predictor | ✅ Complete | None | — |
| Chain repair agent | ✅ Complete | None | — |
| Telegram bot basic commands | ✅ Partial | Missing 8+ tools | Phase 3 |
| Phone number → profile lookup | ❌ Missing | Full gap | Phase 1.2 + 9.1 |
| Agentic profile tool | ❌ Missing | Full gap | Phase 3.1 |
| Agentic schedule tool | ❌ Missing | Full gap | Phase 3.1 |
| Medical data restriction gate | ❌ Missing | Full gap | Phase 3.4 |
| Telegram deep link to web portal | ❌ Missing | Full gap | Phase 9.2 |
| Multi-turn registration flow | ❌ Missing | Full gap | Phase 3.2 |
| Language-first bot responses | ⚠️ Partial | English always first | Phase 3.3 |
| Donor availability pause/resume | ❌ Missing | Full gap | Phase 9.3 |
| DonorPortal dynamic data | ⚠️ Partial | Hardcoded cards | Phase 4 |
| Patient Dashboard wired | ⚠️ Skeleton | No real API calls | Phase 5 |
| Emergency chain live WS updates | ⚠️ Partial | Frontend not handling events | Phase 6.1 |
| Real leaderboard rank in portal | ❌ Missing | No endpoint | Phase 1.3 + 4.2 |
| Active emergency card (real data) | ❌ Missing | No endpoint | Phase 1.4 + 4.3 |
| Proactive scheduler auto-seeds | ⚠️ Partial | Doesn't create schedules | Phase 2.1 |
| Impact story 2-hour delay | ⚠️ Partial | Fires immediately, not after 2h | Phase 2.2 |
| Blood bank cache auto-update | ⚠️ Partial | Scraper exists, not scheduled | Phase 2.3 |
| Demo mode / fallback mocks | ❌ Missing | Full gap | Phase 8.3 |
| Neo4j auto-seed on startup | ❌ Missing | Must run manually | Phase 0.2 |
| One-click demo trigger button | ❌ Missing | Full gap | Phase 6.2 |
| Admin trace visualization | ⚠️ Partial | Data exists, no visual | Phase 7.2 |
| DPDP-compliant data tiers | ⚠️ Partial | /mydata exposes phone | Phase 3.4 |
| Bolna voice service | ✅ Complete | Config needed | Phase 0 (manual) |
| LoRa offline bridge | ✅ Complete | None | — |
| OCR blood card photo | ✅ Complete | None | — |
| Gamification badges | ✅ Complete | Frontend not wired | Phase 4.2 |
| SVD challenge recommender | ✅ Complete | None | — |
| DPDP consent management | ✅ Complete | None | — |

---

## PART 4 — PRIORITY ORDER FOR HACKATHON

If time is limited, execute in this exact order:

**MUST HAVE (Demo Day Blockers):**
1. Phase 0 — Environment stabilization + seed data
2. Phase 6 — Live emergency chain WS updates in frontend
3. Phase 3.1 — Agentic bot tools (profile + eligibility + schedule)
4. Phase 4.2 + 4.3 — DonorPortal dynamic wiring
5. Phase 8.2 — Demo sequence rehearsal

**SHOULD HAVE (Strong differentiators):**
6. Phase 3.2 — Multi-turn registration
7. Phase 3.3 + 3.4 — Language-first + medical data gate
8. Phase 5 — Patient Dashboard
9. Phase 2.1 + 2.2 — Proactive scheduler fixes
10. Phase 9.2 — Telegram deep link to web portal

**NICE TO HAVE (Polish):**
11. Phase 7 — Admin dashboard polish
12. Phase 9.3 — Pause/resume availability
13. Phase 9.4 — Language auto-detection
14. Phase 10 — Production deployment

---

## PART 5 — INSTRUCTIONS FOR AGENTIC IDE

When giving this file to Antigravity IDE or any agentic coding tool, use this prompt template:

```
You are a senior full-stack developer working on BloodBridge AI, a clinical blood donation coordination platform. 

The codebase is at [repo path]. The backend is FastAPI + Python in BloodBridge_AI_Backend/. The frontend is React + Vite + TypeScript in BloodBridge_AI_frontend/artifacts/bloodbridge/src/.

Please implement [PHASE X — STEP Y] from version_2_pre-hackathon.md. 

Key constraints:
- Do NOT modify agents/graph.py or the core LangGraph pipeline
- Do NOT modify existing test files
- All new API endpoints must follow the existing pattern in api/donors.py
- All new React components must use the existing shadcn/ui component library
- Use Supabase for all database operations via get_supabase_admin()
- Keep the existing auth pattern (X-Staff-Token for staff, JWT for donors)

After implementing, update MASTER_STATUS.txt to mark the relevant items as ✅.
```

---

*Document generated from full codebase audit — June 2026*
*BloodBridge AI · Team Inqilab · DNR College of Engineering and Technology*
