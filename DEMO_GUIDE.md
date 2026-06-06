# BloodBridge AI — Complete Demo Guide

## How Every Feature Works & How to Demo It

---

## 🏗️ System Architecture (4 Pillars)

### Pillar 1: Smart Matching (8-Antigen ISBT Compatibility)
**What it does:** Scores donor-patient compatibility using 7 parameters:
1. ABO blood group compatibility
2. Rh(D) factor
3. Kell antigen (kell_negative)
4. Duffy antigen (duffy_negative)
5. Kidd antigen (kidd_negative)
6. Rh-E subtype (rh_e_negative)
7. Rh-c subtype (rh_c_negative)
8. Geographic distance (3-tier radius)

**Where it lives:** `services/matching_engine.py` → `rank_donors_for_patient()`

**How to demo:**
1. Go to Admin → Click "Run Optimizer" (Hungarian Assignment)
2. Watch terminal logs: `MatchingEngine: ranking donors for patient P-10045`
3. See `8 primary, 46 wide-net` — primary = exact ABO+Rh match, wide-net = broader compatible types
4. The optimizer output shows match_score per donor (0.0-1.0)

**3-Tier Radius Search:**
- Ring 1: 0-5km (immediate vicinity of hospital)
- Ring 2: 5-15km (city area)
- Ring 3: 15-50km (metro area)
- This is computed in `rank_donors_for_patient()` using geohash proximity from `donor_locations` table

---

### Pillar 2: AI Agent Coordination (LangGraph 14-Node Pipeline)

**Agents in the system:**

| # | Agent | File | What it does |
|---|---|---|---|
| 1 | **Intake Agent** | `agents/intake.py` | Receives emergency request, validates patient, scores urgency |
| 2 | **Matching Agent** | `agents/matching.py` | Calls MatchingEngine to find best donors |
| 3 | **Outreach Agent** | `agents/outreach.py` | Sends Telegram alerts to matched donors |
| 4 | **Monitor Agent** | `agents/monitor.py` | Watches chain status every 1 min, escalates timeouts |
| 5 | **Repair Agent** | `agents/repair.py` | Auto-repairs broken chains by finding replacement donors |
| 6 | **Voice Agent** | `agents/voice.py` | Triggers Bolna AI voice calls when Telegram fails |
| 7 | **Outcome Agent** | `agents/outcome.py` | Logs final outcomes, updates stats |
| 8 | **Planner Agent** | `agents/planner.py` | Orchestrates the full LangGraph flow |
| 9 | **Eligibility Agent** | `agents/eligibility.py` | Checks WHO/NBTC donation eligibility gates |
| 10 | **Gamification Agent** | `agents/gamification.py` | Awards badges, updates leaderboard |
| 11 | **Demand Forecast Agent** | `agents/demand_forecast_agent.py` | Predicts blood demand by type for next 4 weeks |
| 12 | **Proactive Scheduler** | `agents/proactive_scheduler.py` | Auto-generates transfusion dates from history |
| 13 | **Neo4j Match Agent** | `agents/neo4j_match.py` | Graph-based relationship matching |
| 14 | **Conflict Agent** | `agents/conflict.py` | Resolves scheduling conflicts |

**How to demo the full pipeline:**
1. Open Emergency Dashboard (`/dashboard/emergency`)
2. Click "⚡ Demo Emergency" button (or "New Emergency" → fill form)
3. Watch the terminal logs — you'll see each agent fire in sequence:
   ```
   [REQ-xxx] IntakeAgent started...
   [REQ-xxx] MatchingAgent: found 8 donors in ring 1...
   [REQ-xxx] OutreachAgent: alerting via Telegram...
   ```
4. Donor D-72485 receives Telegram alert on phone
5. Wait 1 minute → Monitor detects no reply → Voice Agent triggers Bolna call
6. Donor replies "YES" on Telegram → Chain confirms → WebSocket updates dashboard

**LangGraph execution flow:** `agents/graph.py` defines the StateGraph:
```
intake → matching → outreach → monitor → [confirm OR escalate → voice → repair]
```

---

### Pillar 3: Engagement & Retention

**Features:**

| Feature | How it works | Where to see it |
|---|---|---|
| **Churn Prediction** | XGBoost model predicts donor dropout risk (F1: 0.87) | Admin → ML Models panel |
| **Gamification** | Badges: blood_hero, life_saver, crisis_hero, rare_guardian, weekend_warrior | Donor Portal → Badges Grid |
| **Leaderboard** | City rankings by lives_saved | Donor Portal → City Leaderboard |
| **Impact Stories** | AI-generated "who you helped" narratives stored in donor_memory | Donor Portal → Impact Stories |
| **Demand Forecast** | Predicts next 4 weeks blood demand by type | Admin → Demand Forecast Panel |

**How to demo:**
1. Login as D-72485 at `/donor` → see badges (Life Saver ✓, Crisis Hero ✓)
2. See "Rank #5 Hyderabad" in header
3. See 2 impact stories about patients helped
4. Admin Panel → Click "Retrain" → Watch XGBoost train in terminal (MAE: 0.027)
5. Admin Panel → "Run Demand Forecast" → See AI-generated shortage alerts

---

### Pillar 4: Scale + Responsible AI

| Feature | How it works |
|---|---|
| **Telegram Bot** | @ummedrakho_bot — registration, alerts, Q&A via tool-calling LLM |
| **Bolna Voice AI** | Automated calls to donors who don't respond on Telegram |
| **AWS Textract OCR** | Blood card scanning → extracts blood group + antigens |
| **DPDP 2023 Compliance** | Consent management, right to access (export), right to erasure (delete) |
| **TRAI Safe Hours** | Voice calls only 8 AM - 11:30 PM IST (queued otherwise) |
| **Idempotency** | Emergency requests use UUID keys to prevent duplicates |
| **Multi-model AI** | Bedrock Claude (reasoning), XGBoost (churn), Vision LLM (OCR) |

---

## 🎯 Demo Script (5-Minute Walkthrough)

### Step 1: Emergency Creation (30 sec)
- Open `/dashboard/emergency`
- Click "⚡ Demo Emergency"
- Show the chain building in real-time (dots going from grey → amber → green)
- Point out the WebSocket live updates

### Step 2: Telegram Alert (30 sec)
- Show phone receiving Telegram message from @ummedrakho_bot
- Message says: "🚨 Emergency B+ needed at KIMS Secunderabad..."
- Reply "YES" → chain confirms

### Step 3: AI Voice Escalation (60 sec)
- Don't reply to Telegram
- Wait 1 min → terminal shows `[SCHED-xxx] ChainMonitorAgent started...`
- Then: `Voice call initiated to +917075899966`
- Phone rings with Bolna AI asking "Can you donate today?"

### Step 4: Donor Portal (30 sec)
- Open `/donor` (logged in as D-72485)
- Show: badges, leaderboard rank, eligibility status
- Show: Blood Bridge card (connected patients)
- Show: DPDP consent management

### Step 5: Patient Portal (30 sec)
- Open `/patient` (login as patient)
- Show: next transfusion date, hemoglobin tracking
- Show: transfusion calendar (AI auto-generated)
- Click "Generate Auto-Schedule"

### Step 6: Admin Intelligence (60 sec)
- Open `/dashboard/admin`
- Show: service health, LangGraph traces
- Click "Retrain" → live ML training
- Show: demand forecast, Hungarian optimizer
- Show: bridge management (donor↔patient pairs)

### Step 7: OCR Card Scan (30 sec)
- Go to `/signup` → select Donor
- Upload blood card image
- Show: blood group + all antigens detected (D+, C−, K−, etc.)

---

## 🔧 How Each Component Proves It's Working

| Component | Evidence in Logs/UI |
|---|---|
| LangGraph agents | Terminal shows `[REQ-xxx] AgentName started...` for each node |
| Neo4j graph | Graph page shows donor↔patient relationships |
| Hungarian optimizer | Admin → "Run Optimizer" → shows assignments per patient |
| Matching Engine | Logs: `MatchingEngine: 8 primary, 46 wide-net for P-10045` |
| 3-tier radius | Donors sorted by distance in matching output |
| e-RaktKosh | Map page shows blood bank inventory (simulated — real API not public) |
| Telegram bot | Message arrives on real phone via @ummedrakho_bot |
| Bolna voice | Phone call rings after 1-min timeout |
| XGBoost churn | Admin → ML Models shows F1: 0.87, retrain updates model |
| OCR Textract | Upload card → terminal shows `Textract result: blood_group=O+, name=...` |
| Vision LLM | If Textract fails → `Vision LLM raw output: O+` in terminal |
| Antigen extraction | Terminal shows `Antigen extraction: panel={D: Positive, K: Negative...}` |
| WebSocket | Emergency dashboard updates without page refresh |
| DPDP consent | Donor Portal → Privacy section shows consent grid |
| Auto-scheduler | Patient clicks "Generate Auto-Schedule" → dates appear |

---

## 🧪 Quick Test Commands

```bash
# Test emergency pipeline end-to-end
curl -X POST http://localhost:8000/api/emergencies \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"P-10026","blood_type":"B+","city":"Hyderabad","ward":"Thalassemia","hospital":"KIMS Secunderabad"}'

# Test voice call
curl -X POST http://localhost:8000/api/donors/D-72485/voice

# Test optimizer
curl -X POST http://localhost:8000/api/admin/optimize-assignments \
  -H "X-Staff-Token: test-admin-token"

# Test OCR upload
curl -X POST http://localhost:8000/api/donors/upload-card \
  -F "file=@blood_card.jpg"

# Test demand forecast
curl -X POST http://localhost:8000/api/admin/forecast/run \
  -H "X-Staff-Token: test-admin-token"
```

---

## 📊 Data Available for Demo

| Entity | Count | Sample IDs |
|---|---|---|
| Donors | 503 | D-72485 (your test donor), D-50001 thru D-50500 |
| Patients | 50 | P-10000 thru P-10049 |
| Emergencies | 5 active | REQ-TEST-B001, REQ-TEST-001, etc. |
| Bridge Memberships | 74 | Mapped donor↔patient pairs |
| Transfusion Schedule | 300 | Auto-generated for all patients |
| Blood Banks | 8 | Hyderabad area (simulated e-RaktKosh) |

---

## ⚠️ Known Limitations (For Demo Context)

1. **e-RaktKosh** — Uses simulated inventory data (real API requires government access)
2. **Neo4j** — Graph data is from Supabase fallback when Neo4j isn't connected locally
3. **Voice calls** — Work via Bolna AI (requires their API key to be active)
4. **TRAI hours** — Currently set to 8 AM - 11:30 PM for testing (production: 9 PM cutoff)
5. **Monitor timeout** — Set to 1 min for testing (production: 7 minutes)
