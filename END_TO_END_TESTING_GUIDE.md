# BloodBridge AI — End-to-End Testing Guide

> **Audience**: A new tester who has never seen this codebase before.
> This document walks you through every feature of BloodBridge AI with exact steps, URLs, payloads, and expected results.

---

## Table of Contents

1. [Prerequisites & Setup](#1-prerequisites--setup)
2. [Starting All Services](#2-starting-all-services)
3. [Feature List](#3-complete-feature-list)
4. [Test Suite](#4-test-suite)
   - [Test 1: Health Check & Service Status](#test-1-health-check--service-status)
   - [Test 2: Donor Registry (List, Filter, Sort)](#test-2-donor-registry-list-filter-sort)
   - [Test 3: Single Donor Profile](#test-3-single-donor-profile)
   - [Test 4: Donor Eligibility Check](#test-4-donor-eligibility-check)
   - [Test 5: Create an Emergency Request](#test-5-create-an-emergency-request)
   - [Test 6: View Emergency Chain](#test-6-view-emergency-chain)
   - [Test 7: Confirm / Close an Emergency](#test-7-confirm--close-an-emergency)
   - [Test 8: Agent Execution Trace](#test-8-agent-execution-trace)
   - [Test 9: Gamification & Leaderboard](#test-9-gamification--leaderboard)
   - [Test 10: DPDP Consent Management](#test-10-dpdp-consent-management)
   - [Test 11: Right to Erasure (DPDP Section 12)](#test-11-right-to-erasure-dpdp-section-12)
   - [Test 12: Right to Access / Data Export (DPDP Section 11)](#test-12-right-to-access--data-export-dpdp-section-11)
   - [Test 13: Trigger AI Voice Call (Bolna)](#test-13-trigger-ai-voice-call-bolna)
   - [Test 14: Trigger Telegram Outreach](#test-14-trigger-telegram-outreach)
   - [Test 15: Telegram Bot Chatbot Interaction](#test-15-telegram-bot-chatbot-interaction)
   - [Test 16: Bulk Import Donors (JSON)](#test-16-bulk-import-donors-json)
   - [Test 17: Bulk Import Donors (CSV)](#test-17-bulk-import-donors-csv)
   - [Test 18: Blood Bank Inventory (Neo4j)](#test-18-blood-bank-inventory-neo4j)
   - [Test 19: LoRa Offline Bridge](#test-19-lora-offline-bridge)
   - [Test 20: Admin Analytics Dashboard](#test-20-admin-analytics-dashboard)
   - [Test 21: Staff Management](#test-21-staff-management)
   - [Test 22: Transfusion Schedule](#test-22-transfusion-schedule)
   - [Test 23: Agent Config Management](#test-23-agent-config-management)
   - [Test 24: Model Retraining Trigger](#test-24-model-retraining-trigger)
   - [Test 25: WebSocket Real-time Updates](#test-25-websocket-real-time-updates)
   - [Test 26: Frontend Web Dashboard](#test-26-frontend-web-dashboard)
   - [Test 27: Patient Dashboard](#test-27-patient-dashboard)
   - [Test 28: Donor Portal](#test-28-donor-portal)
   - [Test 29: Demo Pipeline (Offline)](#test-29-demo-pipeline-offline)

---

## 1. Prerequisites & Setup

| Requirement | Details |
|---|---|
| **Python** | 3.11+ with `venv` |
| **Node.js** | 18+ with `pnpm` |
| **Ngrok** | Download from [ngrok.com](https://ngrok.com) (for Telegram) |
| **Supabase** | Cloud project with schema applied (see `BloodBridge_AI_Backend/data/supabase_schema.sql`) |
| **Neo4j Aura** | Free instance at [neo4j.io](https://neo4j.io) |
| **Telegram** | A bot token from [@BotFather](https://t.me/BotFather) |

### Environment Files

Make sure these `.env` files exist and are filled:

- `BloodBridge_AI_Backend/.env` — All backend secrets (Supabase, Neo4j, Groq, Gemini, Telegram, Bolna)
- `BloodBridge_AI_frontend/artifacts/bloodbridge/.env` — Frontend config (`VITE_API_URL`, `VITE_STAFF_TOKEN`)

### Seed the Databases

Before testing, seed both Supabase and Neo4j with 100 test donors:
```powershell
cd BloodBridge_AI_Backend
$env:PYTHONPATH="."; .\venv\Scripts\python.exe scripts\seed_db.py
```

---

## 2. Starting All Services

Open **4 separate terminals** and run each command:

### Terminal 1 — Backend API
```powershell
cd BloodBridge_AI_Backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
✅ Verify: Open http://localhost:8000/docs — you should see the Swagger UI.

### Terminal 2 — Frontend Dashboard
```powershell
cd BloodBridge_AI_frontend\artifacts\bloodbridge
pnpm run dev
```
✅ Verify: Open http://localhost:5173 — you should see the BloodBridge landing page.

### Terminal 3 — Ngrok Tunnel (for Telegram)
```powershell
ngrok http 8000
```
✅ Verify: You see a `Forwarding` URL like `https://xxxx.ngrok-free.app`.

### Terminal 4 — Register Telegram Webhook
```powershell
cd BloodBridge_AI_Backend
.\venv\Scripts\python.exe setup_webhook.py
```
✅ Verify: You see `DONE! Webhook is live.`

---

## 3. Complete Feature List

| # | Feature | Backend Endpoint | Frontend Page |
|---|---------|-----------------|---------------|
| 1 | System Health Check | `GET /health` | `/dashboard/admin` |
| 2 | Donor Registry (List/Filter/Sort) | `GET /api/donors` | `/dashboard/donors` |
| 3 | Single Donor Profile | `GET /api/donors/{id}` | — |
| 4 | Donor Eligibility Check | `GET /api/donors/{id}/eligibility` | — |
| 5 | Emergency Request Creation | `POST /api/emergencies` | `/dashboard/emergency` |
| 6 | Emergency Chain Viewer | `GET /api/emergencies/{id}/chain` | `/dashboard/emergency` |
| 7 | Confirm / Close Emergency | `POST /api/emergencies/{id}/confirm` | `/dashboard/emergency` |
| 8 | Agent Execution Traces | `GET /api/traces` | `/dashboard/admin` |
| 9 | Gamification Leaderboard | `GET /api/donors/leaderboard` | `/dashboard/donors` |
| 10 | DPDP Consent Management | `GET /api/donors/{id}/consent` | — |
| 11 | Right to Erasure | `DELETE /api/donors/{id}/data` | — |
| 12 | Right to Access / Export | `GET /api/donors/{id}/my-data` | — |
| 13 | AI Voice Call (Bolna) | `POST /api/donors/{id}/trigger-voice` | `/dashboard/donors` |
| 14 | Telegram Outreach | `POST /api/donors/{id}/outreach` | `/dashboard/donors` |
| 15 | Telegram Bot (AI Chat) | `POST /webhook/telegram` | Telegram App |
| 16 | Bulk Import (JSON) | `POST /api/donors/bulk-import` | — |
| 17 | Bulk Import (CSV) | `POST /api/donors/bulk-import-csv` | — |
| 18 | Blood Bank Inventory | `GET /api/blood-banks?city=X` | `/dashboard/map` |
| 19 | LoRa Offline Bridge | `POST /api/lora/receive` | — |
| 20 | Analytics Dashboard | `GET /api/analytics` | `/dashboard/admin` |
| 21 | Staff Management | `GET/POST/DELETE /api/staff` | `/dashboard/admin` |
| 22 | Transfusion Schedule | `GET/POST /api/schedule` | `/dashboard/admin` |
| 23 | Agent Config | `GET/PUT /api/config` | `/dashboard/admin` |
| 24 | Model Retraining | `POST /api/models/retrain` | `/dashboard/admin` |
| 25 | Real-time WebSocket | `WS /ws` | All dashboard pages |
| 26 | Neo4j Graph Visualization | — | `/dashboard/graph` |
| 27 | Patient Dashboard | `GET /api/patients/{id}` | `/patient` |
| 28 | Donor Self-Service Portal | — | `/donor` |
| 29 | Demo Pipeline (Offline) | `python demo_run.py` | — |

---

## 4. Test Suite

> **Base URL**: `http://localhost:8000`
> **Swagger UI**: `http://localhost:8000/docs` (use this for all API tests)
> **Frontend**: `http://localhost:5173`

---

### Test 1: Health Check & Service Status

**Purpose**: Verify all 9 microservices are reachable.

**Steps**:
1. Open your browser or use curl:
   ```
   GET http://localhost:8000/health
   ```
2. **Expected Response**:
   ```json
   {
     "status": "ok",
     "services": {
       "fastapi": { "status": "ok", "latency_ms": 0 },
       "neo4j": { "status": "ok", "latency_ms": 200 },
       "supabase": { "status": "ok", "latency_ms": 100 },
       "telegram": { "status": "ok", "latency_ms": 300 },
       "bolna": { "status": "ok", "latency_ms": 400 }
     }
   }
   ```
3. **Pass Criteria**: `fastapi`, `neo4j`, and `supabase` must all say `"ok"`.

---

### Test 2: Donor Registry (List, Filter, Sort)

**Purpose**: Verify all 100 seeded donors are returned and filtering works.

**Steps**:
1. **List all donors**:
   ```
   GET http://localhost:8000/api/donors
   ```
   ✅ Expected: Array of 100 donor objects.

2. **Sort by name**:
   ```
   GET http://localhost:8000/api/donors?sortBy=name
   ```
   ✅ Expected: Donors sorted alphabetically by name.

3. **Filter by churn risk**:
   ```
   GET http://localhost:8000/api/donors?riskFilter=HIGH
   ```
   ✅ Expected: Only donors with `churn_risk: "HIGH"` are returned.

**Frontend**: Open http://localhost:5173/dashboard/donors — you should see a table of all donors with sorting/filter controls.

---

### Test 3: Single Donor Profile

**Purpose**: Fetch a specific donor's complete profile.

**Steps**:
1. Pick any `donor_id` from Test 2 results (e.g., `D-12345`).
2. ```
   GET http://localhost:8000/api/donors/D-12345
   ```
3. **Expected**: A single JSON object with fields: `donor_id`, `name`, `blood_type`, `city`, `churn_score`, `badges`, etc.
4. **Pass Criteria**: Returns `200 OK` with all fields populated.

---

### Test 4: Donor Eligibility Check

**Purpose**: Verify the WHO/NBTC eligibility screening logic.

**Steps**:
1. Pick a `donor_id`.
2. ```
   GET http://localhost:8000/api/donors/D-12345/eligibility
   ```
3. **Expected**:
   ```json
   {
     "eligible": true,
     "reason": null,
     "days_until_eligible": null
   }
   ```
4. **Pass Criteria**: Returns eligibility status with reasons if ineligible (e.g., "Less than 56 days since last donation").

---

### Test 5: Create an Emergency Request

**Purpose**: Trigger the full 14-node LangGraph agentic pipeline.

**Steps**:
1. First, get a valid `patient_id` from your seeded patients. If none exist, you can check Supabase or use the seed script output.
2. Open Swagger UI at `http://localhost:8000/docs`.
3. Find `POST /api/emergencies` and use this payload:
   ```json
   {
     "patient_id": "P-12345",
     "blood_type": "O-",
     "city": "Hyderabad",
     "ward": "ICU",
     "hospital": "Government General Hospital"
   }
   ```
4. **Expected**: `{ "requestId": "REQ-XXXXX" }` with status `200`.
5. **Behind the Scenes**: The backend will:
   - Create an `emergency_requests` record in Supabase
   - Query Neo4j for compatible donors
   - Run the AI matching pipeline in the background
   - Broadcast a WebSocket event to the frontend

**Frontend**: Open http://localhost:5173/dashboard/emergency — you should see the new emergency appear in real-time.

---

### Test 6: View Emergency Chain

**Purpose**: See which donors were matched to the emergency.

**Steps**:
1. Use the `requestId` from Test 5.
2. ```
   GET http://localhost:8000/api/emergencies/REQ-XXXXX/chain
   ```
3. **Expected**: An array of chain nodes, each with `donor_id`, `donor_name`, `chain_position`, `status`, `antigen_score`.

---

### Test 7: Confirm / Close an Emergency

**Purpose**: Mark an emergency as successfully resolved.

**Steps**:
1. ```
   POST http://localhost:8000/api/emergencies/REQ-XXXXX/confirm
   ```
2. **Expected**: `{ "success": true }`
3. **Side Effects**:
   - `emergency_requests.status` → `COMPLETED`
   - WebSocket broadcast sent to all connected dashboards

---

### Test 8: Agent Execution Trace

**Purpose**: View the detailed AI agent execution log for debugging.

**Steps**:
1. ```
   GET http://localhost:8000/api/traces
   ```
   > **Note**: This endpoint requires the staff token. Add header: `Authorization: Bearer <VITE_STAFF_TOKEN from .env>`
2. **Expected**: Array of trace objects showing each agent node's name, status, and duration.

---

### Test 9: Gamification & Leaderboard

**Purpose**: View top-ranked donors for a city.

**Steps**:
1. ```
   GET http://localhost:8000/api/donors/leaderboard?city=Hyderabad
   ```
2. **Expected**: Array of leaderboard entries with `rank`, `name`, `city`, `lives_saved`, `donation_count`, `badges`.

**Frontend**: Check the Donors page for leaderboard section.

---

### Test 10: DPDP Consent Management

**Purpose**: Verify India's Digital Personal Data Protection Act (2023) compliance.

**Steps**:
1. **View consent status**:
   ```
   GET http://localhost:8000/api/donors/D-12345/consent
   ```
   ✅ Expected: JSON showing consent status for each category (data_storage, outreach_telegram, etc.)

2. **Revoke consent**:
   ```
   POST http://localhost:8000/api/donors/D-12345/consent/revoke
   Body: { "consent_type": "outreach_voice" }
   ```
   ✅ Expected: `{ "success": true, "message": "Consent for 'outreach_voice' successfully revoked." }`

---

### Test 11: Right to Erasure (DPDP Section 12)

**Purpose**: A donor can request complete deletion of their data.

**Steps**:
1. ```
   DELETE http://localhost:8000/api/donors/D-12345/data
   ```
2. **Expected**: `{ "success": true }`
3. **Side Effects**: All records for this donor are purged from Supabase.

---

### Test 12: Right to Access / Data Export (DPDP Section 11)

**Purpose**: A donor can download all data the system holds about them.

**Steps**:
1. ```
   GET http://localhost:8000/api/donors/D-12345/my-data
   ```
2. **Expected**: Full JSON export of all donor data (profile, consent records, donation history, badges).

---

### Test 13: Trigger AI Voice Call (Bolna)

**Purpose**: Make the AI call a donor's phone number.

> **Requires**: Valid `BOLNA_API_KEY` and `BOLNA_AGENT_ID` in `.env`.

**Steps**:
1. Open Swagger UI → `POST /api/donors/{id}/trigger-voice`
2. Enter a donor ID that has a phone number.
3. **Expected**: `{ "callSid": "call-xxxx" }`
4. **Side Effect**: The donor's phone will ring with an AI voice agent speaking to them!

---

### Test 14: Trigger Telegram Outreach

**Purpose**: Send a manual Telegram message to a donor.

> **Requires**: The donor must have a `telegram_chat_id` set.

**Steps**:
1. ```
   POST http://localhost:8000/api/donors/D-12345/outreach
   ```
2. **Expected**: `{ "messageId": "MSG-D-12345-..." }`
3. **Side Effect**: Donor receives a Telegram message.

---

### Test 15: Telegram Bot Chatbot Interaction

**Purpose**: Test the AI-powered Telegram chatbot end-to-end.

> **Requires**: Ngrok running + webhook registered (see Setup step 3 & 4).

**Steps**:
1. Open Telegram on your phone or web.
2. Search for your bot (check the bot username from @BotFather).
3. Send `/start`.
   ✅ Expected: Bot replies with a welcome message and consent prompt.
4. Reply `YES`.
   ✅ Expected: Bot confirms consent and registers you.
5. Send `/register B+`
   ✅ Expected: Bot sets your blood type.
6. Send `/badges`
   ✅ Expected: Bot shows your current badges and donation stats.
7. Send `/leaderboard`
   ✅ Expected: Bot shows the city leaderboard.
8. Send a freeform message like "I want to donate blood".
   ✅ Expected: The Groq Llama-3 AI agent responds intelligently.

---

### Test 16: Bulk Import Donors (JSON)

**Purpose**: Import multiple donors via a JSON payload.

**Steps**:
1. ```
   POST http://localhost:8000/api/donors/bulk-import
   Body:
   {
     "donors": [
       { "name": "Test User 1", "blood_type": "A+", "city": "Mumbai", "phone": "+919999900001" },
       { "name": "Test User 2", "blood_type": "B-", "city": "Delhi", "phone": "+919999900002" }
     ]
   }
   ```
2. **Expected**:
   ```json
   { "success": true, "imported_count": 2, "failed_count": 0, "errors": [] }
   ```

---

### Test 17: Bulk Import Donors (CSV)

**Purpose**: Upload a CSV file to bulk-import donors.

> **Requires**: Staff auth token in `Authorization` header.

**Steps**:
1. Create a file called `test_donors.csv`:
   ```csv
   name,phone,blood_type,city
   CSV User 1,+919999900003,O+,Hyderabad
   CSV User 2,+919999900004,AB-,Warangal
   ```
2. Use Swagger UI → `POST /api/donors/bulk-import-csv`, upload the file.
3. **Expected**:
   ```json
   { "success": true, "imported_count": 2, "skipped_duplicates": 0, "failed_count": 0, "errors": [], "neo4j_edges_queued": true }
   ```

---

### Test 18: Blood Bank Inventory (Neo4j)

**Purpose**: Query blood banks and their stock levels from the graph database.

**Steps**:
1. ```
   GET http://localhost:8000/api/blood-banks?city=Hyderabad
   ```
2. **Expected**: Array of blood bank objects with `name`, `city`, `units` (stock per blood type), `distance_km`, `drive_min`.

**Frontend**: Open http://localhost:5173/dashboard/map — you should see blood banks plotted on a map.

---

### Test 19: LoRa Offline Bridge

**Purpose**: Simulate receiving an emergency packet from a rural LoRa gateway.

**Steps**:
1. **Receive a packet**:
   ```
   POST http://localhost:8000/api/lora/receive
   Body:
   {
     "request_id": "LORA0001",
     "patient_id": "PAT00001",
     "blood_type": "O-",
     "urgency_level": "CRITICAL",
     "city": "Warangal",
     "hospital_name": "Rural PHC",
     "units_needed": 2,
     "source": "lora"
   }
   ```
   ✅ Expected: `{ "success": true, "emergency_id": "...", "queued_offline": false, "message": "..." }`

2. **Check gateway status**:
   ```
   GET http://localhost:8000/api/lora/status
   ```
   ✅ Expected: `{ "gateway_online": true, "queue_depth": 0, ... }`

3. **Flush offline queue**:
   ```
   POST http://localhost:8000/api/lora/flush
   ```
   ✅ Expected: `{ "success": true, "flushed_count": 0, "failed_count": 0, "errors": [] }`

---

### Test 20: Admin Analytics Dashboard

**Purpose**: View real-time engagement metrics computed from live data.

> **Requires**: Staff auth token.

**Steps**:
1. ```
   GET http://localhost:8000/api/analytics
   ```
   Add header: `Authorization: Bearer <VITE_STAFF_TOKEN>`
2. **Expected**:
   ```json
   {
     "active_donors": 100,
     "total_donors": 100,
     "active_pct": 100.0,
     "at_risk_count": 0,
     "avg_response_rate": 50,
     "donated_this_month": 0,
     "trend": [...],
     "by_city": [...]
   }
   ```

**Frontend**: Open http://localhost:5173/dashboard/admin — you should see charts and metrics.

---

### Test 21: Staff Management

**Purpose**: CRUD operations for hospital staff coordinators.

> **Requires**: Staff auth token.

**Steps**:
1. **List staff**:
   ```
   GET http://localhost:8000/api/staff
   ```

2. **Add staff**:
   ```
   POST http://localhost:8000/api/staff
   Body: { "username": "dr_ramesh", "hospital": "GGH Hyderabad", "role": "Coordinator" }
   ```

3. **Remove staff**:
   ```
   DELETE http://localhost:8000/api/staff/dr_ramesh
   ```

---

### Test 22: Transfusion Schedule

**Purpose**: Manage upcoming transfusion appointments.

> **Requires**: Staff auth token.

**Steps**:
1. **View schedule**:
   ```
   GET http://localhost:8000/api/schedule?days=7
   ```

2. **Create entry**:
   ```
   POST http://localhost:8000/api/schedule
   Body:
   {
     "patient_id": "P-12345",
     "scheduled_date": "2026-06-10",
     "hospital": "GGH Hyderabad",
     "blood_type": "B+",
     "advance_days": 5
   }
   ```

---

### Test 23: Agent Config Management

**Purpose**: View and update the AI orchestration settings.

> **Requires**: Staff auth token.

**Steps**:
1. **View config**:
   ```
   GET http://localhost:8000/api/config
   ```
   ✅ Expected:
   ```json
   {
     "coordination_timeout_mins": 7,
     "channel_sequence": ["telegram", "voice", "sms"],
     "retry_limit": 3,
     "safe_calling_hours": { "start": 8, "end": 21 }
   }
   ```

2. **Update config**:
   ```
   PUT http://localhost:8000/api/config
   Body: { "retry_limit": 5 }
   ```

---

### Test 24: Model Retraining Trigger

**Purpose**: Kick off a background job to retrain the XGBoost churn/urgency models.

> **Requires**: Staff auth token.

**Steps**:
1. ```
   POST http://localhost:8000/api/models/retrain
   ```
2. **Expected**: `{ "jobId": "JOB-..." }`
3. Check backend terminal logs for training progress.

---

### Test 25: WebSocket Real-time Updates

**Purpose**: Verify the dashboard receives live updates without refreshing.

**Steps**:
1. Open http://localhost:5173/dashboard/emergency in your browser.
2. Open a second browser tab with Swagger UI at http://localhost:8000/docs.
3. In Swagger, create a new emergency (`POST /api/emergencies`).
4. **Expected**: The first browser tab instantly updates to show the new emergency — no page refresh needed.

---

### Test 26: Frontend Web Dashboard

**Purpose**: Visually verify all dashboard pages load and display data.

| Page | URL | What to Check |
|------|-----|---------------|
| Landing | http://localhost:5173/ | Hero section, feature cards load |
| Staff Login | http://localhost:5173/login | Login form appears |
| Emergency Dashboard | http://localhost:5173/dashboard/emergency | Emergency list, create button |
| Donor Registry | http://localhost:5173/dashboard/donors | 100 donors in table, filters work |
| Graph Visualization | http://localhost:5173/dashboard/graph | Neo4j donor-patient graph renders |
| Blood Bank Map | http://localhost:5173/dashboard/map | Map with blood bank markers |
| Admin Panel | http://localhost:5173/dashboard/admin | Health, analytics, traces, config |

---

### Test 27: Patient Dashboard

**Purpose**: View a patient's profile, linked donors, and transfusion history.

**Steps**:
1. Open http://localhost:5173/patient/login
2. Enter a valid `patient_id` (from seeded data).
3. **Expected**: Dashboard showing patient info, linked donors, and transfusion history.

**API**:
```
GET http://localhost:8000/api/patients/P-12345
```

---

### Test 28: Donor Portal

**Purpose**: Self-service portal for donors to check their stats and badges.

**Steps**:
1. Open http://localhost:5173/donor/login
2. Enter a valid `donor_id`.
3. **Expected**: Portal showing donation count, badges, consent status, and leaderboard rank.

---

### Test 29: Demo Pipeline (Offline)

**Purpose**: Run the complete 14-node LangGraph pipeline in demo mode without needing any cloud services.

**Steps**:
1. Open a terminal:
   ```powershell
   cd BloodBridge_AI_Backend
   .\venv\Scripts\python.exe demo_run.py --blood-type "O-" --city "Hyderabad" --urgency CRITICAL
   ```
2. **Expected**: A colorful step-by-step console output showing all 14 agent nodes executing:
   - IntakeAgent → EligibilityFilter → AntigenScoring → UrgencyScoring → Neo4jMatching → ConflictResolver → Planner → Outreach → ChainMonitor → ChainRepair → Inventory → Gamification → ImpactStory → Outcome
3. **Pass Criteria**: Script completes with `PIPELINE COMPLETE` banner and summary stats.

---

## Quick Reference: Auth Headers

For any endpoint that requires staff authentication, add this header:

```
Authorization: Bearer <your VITE_STAFF_TOKEN value from .env>
```

You can find the token in `BloodBridge_AI_frontend/artifacts/bloodbridge/.env` under `VITE_STAFF_TOKEN`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `500 Internal Server Error` on any `/api/donors` call | Check that the Supabase schema has been applied and `SUPABASE_KEY` starts with `eyJ...` |
| Neo4j shows `offline` in health check | Verify `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` in `.env` |
| Telegram bot not responding | Make sure ngrok is running and you re-ran `setup_webhook.py` |
| Frontend shows empty data | Confirm the backend is running on port 8000 and seeding was done |
| `CORS error` in browser console | Restart the backend — CORS is set to allow all origins |

---

*Last updated: June 2026*
