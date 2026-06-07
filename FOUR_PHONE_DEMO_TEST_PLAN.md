# BloodBridge AI — 4-Phone Live Demo Test Plan (All 4 Pillars)

> **Goal:** Only 4 real phone numbers exist in Supabase. Three power the live Blood Bridge demo; the fourth is registered live during the judges demo and deleted afterward. Ten background records fill dashboards (graph, leaderboard, optimizer) without receiving real alerts.

---

## Phone roster

| # | Phone (login) | E.164 | Role | ID | Blood / flags | Real-time use |
|---|---------------|-------|------|-----|---------------|---------------|
| **1** | `7075899966` | +917075899966 | **Donor** Sheik Bhai | D-THREE-001 | B+ · Kell-neg | Telegram YES/NO · Bolna voice · Donor portal |
| **2** | `9642273274` | +919642273274 | **Donor** Arjun Singh | D-THREE-002 | O+ · Kell-neg | Backup chain · Telegram · Donor portal |
| **3** | `6305589656` | +916305589656 | **Patient** Ravi Kumar | P-THREE-001 | B+ · **anti-Kell** | Patient portal · auto-schedule · **never voice-called** |
| **4** | `9494421169` | +919494421169 | **Live registration** | *(created live)* | — | Telegram `/register` donor + patient → delete in Supabase after demo |

**Background (no phones):** D-BGND-001..010 + patient P-THREE-002 — dashboards only  
**Bot:** [@ummedrakho_bot](https://t.me/ummedrakho_bot)  
**City / hospital:** Hyderabad · KIMS Secunderabad  
**Emergency form default:** `P-THREE-001` / `B+` / Hyderabad

---

## Part 0 — One-time setup (15 min)

### Step 0.1 — Wipe + seed Supabase

```powershell
cd "BloodBridge_AI_Backend"
python -m data.wipe_and_seed_four_phone_demo
```

**What this does:**
- Clears emergencies, chains, traces, bridges, schedules, leaderboard
- Removes all donors/patients except D-THREE-001/002, D-BGND-001..010, P-THREE-001/002
- Seeds 3 real phones + 10 background donors + bridge + transfusion schedule + completed emergency history

**Pass:** Terminal prints `OK 4-Phone demo seed complete!`

---

### Step 0.2 — Start services (4 terminals)

| Terminal | Command |
|----------|---------|
| **1 — ngrok** | `ngrok http 8000` |
| **2 — Backend** | `cd BloodBridge_AI_Backend` → `python -m uvicorn main:app --reload --port 8000` |
| **3 — Webhook** | `cd BloodBridge_AI_Backend` → `python setup_webhook.py` |
| **4 — Frontend** | `cd BloodBridge_AI_frontend\artifacts\bloodbridge` → `pnpm run dev` |

Open **http://localhost:5173** — use **light mode** on donor/patient portals for judges.

---

### Step 0.3 — `.env` for live demo

```env
APP_ENV=development
DEMO_MOCK_MODE=false
THREE_PHONE_DEMO_MODE=true
BOLNA_API_KEY=...
BOLNA_AGENT_ID=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_URL=https://<ngrok-id>.ngrok-free.app/webhook/telegram
```

> `THREE_PHONE_DEMO_MODE=true` restricts **live matching** to D-THREE-001 and D-THREE-002 only. Background donors still appear on Graph, Donors list, Leaderboard, and Hungarian optimizer.

---

### Step 0.4 — Pre-flight checklist

| # | Check | How | Pass |
|---|-------|-----|------|
| 1 | Backend health | http://localhost:8000/health | ☐ |
| 2 | Patient seeded | http://localhost:8000/api/patients/P-THREE-001 | ☐ |
| 3 | Donor 1 seeded | http://localhost:8000/api/donors/D-THREE-001 | ☐ |
| 4 | Graph data | http://localhost:8000/api/donors/graph/data?request_id=all | ☐ nodes > 0 |
| 5 | Webhook | `setup_webhook.py` → no error | ☐ |
| 6 | Phone 4 absent | No row with `9494421169` in donors/patients | ☐ |

---

## Quick login cheatsheet

| Role | URL | Login |
|------|-----|-------|
| Staff | `/login` → `/dashboard/emergency` | staff credentials |
| Donor 1 | `/donor/login` → `/donor` | `7075899966` or `D-THREE-001` |
| Donor 2 | `/donor/login` → `/donor` | `9642273274` or `D-THREE-002` |
| Patient | `/patient/login` or `/patient?id=P-THREE-001` | `6305589656` |
| Registration demo | Telegram @ummedrakho_bot | Phone 4: `9494421169` |

---

## Recommended demo order (45 min showcase)

```
0.  Wipe + seed + webhook          (5 min)
1.  PILLAR 2 — Voice call Phone 1  (5 min)  ← phone rings for judges
2.  PILLAR 2 — Telegram + YES      (5 min)
3.  PILLAR 1 — Emergency + Graph   (5 min)
4.  PILLAR 3 — Donor portal P1     (5 min)
5.  PILLAR 3 — Patient portal P3   (5 min)
6.  PILLAR 1 — Hungarian optimizer (3 min)
7.  PILLAR 3 — Forecast + retrain  (5 min)
8.  PILLAR 4 — Live register P4    (7 min)
9.  PILLAR 4 — Map + DPDP          (5 min)
10. Cleanup Phone 4 in Supabase    (2 min)
```

---

# PILLAR 1 — Smart Matching (7-parameter + 8-antigen ISBT)

**Story for judges:** Patient Ravi (P-THREE-001) has **anti-Kell**. Only Kell-negative donors score high. Matching uses geo rings (5 km → 15 km → 30 km) and weighted scoring in `matching_engine.py`.

### Step 1.1 — Trigger emergency (Staff UI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Staff login → `/dashboard/emergency` | Emergency OC loads |
| 2 | Click **New Emergency** | Dialog opens with defaults |
| 3 | Confirm: `P-THREE-001`, `B+`, Hyderabad, KIMS | Pre-filled |
| 4 | Submit | Toast: "AI Agents dispatched" |
| 5 | Watch backend terminal | Logs: `intake` → `antigen_score` → `urgency_score` → `neo4j_match` → `planner` → `outreach` |

**Pass:** New card appears; chain shows **2 nodes** (D-THREE-001 pos 1 = ALERTED, D-THREE-002 pos 2 = PENDING)  
**Pass:** D-THREE-001 has higher antigen score than Kell-positive background donors (visible in trace)

---

### Step 1.2 — Graph view (Staff UI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `/dashboard/graph` | Force-graph renders |
| 2 | Filter: active emergency (or `request_id=all`) | Patient node + donor edges |
| 3 | Hover nodes | Names, antigen scores — not mock placeholders |

**Pass:** ≥12 nodes (2 demo donors + 10 background + patients)  
**Pass:** COMPATIBLE_WITH / IN_CHAIN edges visible

---

### Step 1.3 — Map view (Staff UI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `/dashboard/map` | Hyderabad map loads |
| 2 | Filter blood type **B+** | Donors + banks shown |
| 3 | Click a donor pin | Distance + blood type popup |

**Pass:** D-THREE-001 and D-THREE-002 pins near KIMS Secunderabad

---

### Step 1.4 — Hungarian optimizer (Staff UI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `/dashboard/admin` → **Run Optimizer Preview** | Optimizer runs |
| 2 | Create 2nd emergency for `P-THREE-002` (O-, Apollo) if needed | 2 IN_PROGRESS requests |
| 3 | Re-run optimizer | Disjoint donor assignments |

**Pass:** No donor assigned to two patients simultaneously  
**Pass:** Kell-safe donors preferred for P-THREE-001

---

### Step 1.5 — Matching API (optional terminal)

```powershell
cd BloodBridge_AI_Backend
python test_scenario_a.py
```

**Pass:** Top ranked = D-THREE-001, D-THREE-002; antigen scores differ; Kell-positive donors penalized/excluded

---

# PILLAR 2 — Multi-Agent Coordination (14 LangGraph nodes)

**Story:** Autonomous pipeline — intake → match → outreach → monitor → repair/voice → outcome. WebSocket updates dashboard live.

### Step 2.1 — Voice call (Phone 1) — do this first for judges

| Step | Action | Phone | Expected |
|------|--------|-------|----------|
| 1 | `/dashboard/donors` → find **Sheik Bhai** → click 📞 | — | Call initiated |
| **OR** | Terminal: `python scripts/test_bolna_call.py D-THREE-001` | — | Same |
| 2 | Wait ≤30 s | **Phone 1** | Phone **7075899966** rings |
| 3 | Check backend log | — | `Bolna call INITIATED` (not MOCK skip) |

**Fail fix:** `DEMO_MOCK_MODE=false`, verify `BOLNA_API_KEY` + `BOLNA_AGENT_ID`

---

### Step 2.2 — Telegram outreach (Phone 1)

| Step | Action | Phone | Expected |
|------|--------|-------|----------|
| 1 | Open @ummedrakho_bot → `/start` | Phone 1 | Welcome + consent |
| 2 | Or dashboard: Donors → 💬 on Sheik Bhai | — | Push alert |
| 3 | Check message | Phone 1 | B+ emergency at KIMS, YES/NO buttons |
| 4 | Backend log | — | `POST /webhook/telegram 200` |

---

### Step 2.3 — Full coordination loop

| Step | Action | Phone | Expected |
|------|--------|-------|----------|
| 1 | Create emergency (Step 1.1) | Staff | Chain ALERTED pos 1 |
| 2 | Telegram alert arrives | Phone 1 | Message received |
| 3 | Do **not** reply 5–7 min | — | Monitor escalates → voice (if configured) |
| 4 | Reply **`YES`** | Phone 1 | Chain → CONFIRMED |
| 5 | Keep `/dashboard/emergency` open | Staff | Dot turns **green** without refresh (WebSocket) |
| 6 | Click **Mark Resolved** | Staff | Status COMPLETED |
| 7 | New emergency → reply **`NO`** | Phone 1 | Repair alerts Phone 2 |

---

### Step 2.4 — Agent trace drawer (Staff UI)

| Step | Action | Expected |
|------|--------|----------|
| 1 | On emergency card → **View Trace** | Drawer opens |
| 2 | Inspect node list | intake, antigen_score, urgency_score, neo4j_match, planner, outreach, monitor… |
| 3 | Check timings | Each node shows duration_ms |

**Pass:** 14-node pipeline visible with real request_id

---

### Step 2.5 — Proactive scheduler (Patient UI)

| Step | Action | Phone | Expected |
|------|--------|-------|----------|
| 1 | `/patient?id=P-THREE-001` | Phone 3 | Patient dashboard |
| 2 | Tap **Generate Auto-Schedule** | — | Toast success |
| 3 | Scroll transfusion calendar | — | Upcoming dates (+7, +21, +35 days) |

**Pass:** Schedule rows in UI (seeded + generated)

---

# PILLAR 3 — Donor Engagement & Gamification

### Step 3.1 — Donor portal Phone 1 (light mode)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `/donor/login` → `7075899966` | Portal loads |
| 2 | Toggle **light mode** | Clean judge-friendly UI |
| 3 | Check badges | life_saver, rapid_responder |
| 4 | Check lives saved | 12 |
| 5 | Check eligibility card | Eligible (90 days since last donation) |
| 6 | DPDP consent section | Granted channels listed |
| 7 | Locations CRUD | Add/edit/delete location |

---

### Step 3.2 — Donor portal Phone 2

| Step | Action | Expected |
|------|--------|----------|
| 1 | `/donor/login` → `9642273274` | Portal loads |
| 2 | Toggle availability pause/resume | Status updates |
| 3 | View leaderboard | Top 10 Hyderabad (includes D-BGND donors) |

---

### Step 3.3 — Patient portal Phone 3

| Step | Action | Expected |
|------|--------|----------|
| 1 | `/patient/login` or `?id=P-THREE-001` | Dashboard loads |
| 2 | Linked donors / bridges | D-THREE-001, D-THREE-002 shown |
| 3 | Chain history | REQ-DEMO-HIST-001 COMPLETED |
| 4 | Antibody flags | anti-Kell highlighted |
| 5 | Transfusion calendar | Scheduled dates visible |

---

### Step 3.4 — Admin engagement panels

| Feature | Page | Action | Pass |
|---------|------|--------|------|
| Churn scores | `/dashboard/donors` | Sort by churn_score | ☐ D-BGND-006 HIGH, D-THREE-001 LOW |
| Demand forecast | `/dashboard/admin` | Run Forecast | ☐ 28-day chart populates |
| XGBoost retrain | `/dashboard/admin` | Retrain Now | ☐ jobId toast |
| Donor outreach | `/dashboard/donors` | 💬 / 📞 buttons | ☐ Only demo donors get real alerts |

---

# PILLAR 4 — Scale & Responsible AI

### Step 4.1 — Live Telegram registration (Phone 4 only)

> **Before demo:** Confirm Phone 4 is NOT in Supabase.  
> **After demo:** Delete Phone 4 rows from Supabase (see Step 4.5).

| # | Test | Phone 4 action | Pass |
|---|------|----------------|------|
| T1 | Start | `/start` @ummedrakho_bot | ☐ |
| T2 | Register donor | `/register` → name, O+, Hyderabad | ☐ |
| T3 | Profile | `/profile` | ☐ |
| T4 | Eligibility | `/eligibility` | ☐ |
| T5 | Badges | `/badges` | ☐ |
| T6 | Leaderboard | `/leaderboard` | ☐ |
| T7 | OCR blood card | Send photo of blood group card | ☐ |
| T8 | Language | Ask in Hindi/Telugu | ☐ |
| T9 | Register patient | Guided patient flow (if supported) | ☐ |
| T10 | Delete data | `/deletedata` or admin delete | ☐ |

**Show judges:** Real-time registration without pre-seeding.

---

### Step 4.2 — Telegram bot regression (Phones 1 & 2)

| # | Test | Phone | Pass |
|---|------|-------|------|
| T1 | Emergency accept | Phone 1 → `YES` | ☐ |
| T2 | Emergency decline | Phone 1 → `NO` → Phone 2 alerted | ☐ |
| T3 | Phone 2 backup | Phone 2 → `YES` | ☐ |

---

### Step 4.3 — Map + blood banks

| Step | Action | Expected |
|------|--------|----------|
| 1 | `/dashboard/map` | Hyderabad blood banks visible |
| 2 | Filter B+ | Inventory pins update |
| 3 | (Optional) Swagger POST `/api/blood-banks/refresh` | Cache refresh toast/log |

---

### Step 4.4 — DPDP compliance (Donor portal Phone 1)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Donor portal → Privacy / Consent | Summary shown |
| 2 | Export my data | JSON/download |
| 3 | Revoke consent (demo only) | Status updates |
| 4 | Re-grant via `/start` on Telegram | Consent restored |

---

### Step 4.5 — Cleanup Phone 4 after judges demo

In Supabase SQL editor or Table Editor:

```sql
-- Replace with actual donor_id / patient_id created during live registration
DELETE FROM consent_records WHERE donor_id IN (SELECT donor_id FROM donors WHERE phone LIKE '%9494421169%');
DELETE FROM donor_memory WHERE donor_id IN (SELECT donor_id FROM donors WHERE phone LIKE '%9494421169%');
DELETE FROM donors WHERE phone LIKE '%9494421169%';
DELETE FROM patients WHERE phone LIKE '%9494421169%';
```

**Pass:** Only 3 pre-seeded real phones remain (+ 10 background, no phones)

---

# UI page → pillar coverage matrix

| UI page | Pillar 1 | Pillar 2 | Pillar 3 | Pillar 4 |
|---------|----------|----------|----------|----------|
| `/dashboard/emergency` | ✓ trigger + chain | ✓ WebSocket + trace | — | — |
| `/dashboard/graph` | ✓ antigen edges | ✓ IN_CHAIN status | — | — |
| `/dashboard/map` | ✓ geo rings | — | — | ✓ blood banks |
| `/dashboard/donors` | ✓ churn column | ✓ outreach buttons | ✓ engagement | — |
| `/dashboard/admin` | ✓ Hungarian | ✓ forecast | ✓ retrain | ✓ staff CRUD |
| `/donor` | ✓ antigen flags | — | ✓ badges/leaderboard | ✓ DPDP |
| `/patient` | ✓ antibody flags | ✓ auto-schedule | ✓ chain history | — |
| Telegram bot | ✓ matching context | ✓ YES/NO loop | ✓ gamification | ✓ register/OCR |
| Voice (Bolna) | — | ✓ VoiceAgent | — | ✓ TRAI hours |

---

# Troubleshooting

| Issue | Fix |
|-------|-----|
| Voice doesn't ring | `DEMO_MOCK_MODE=false`; Bolna keys set; Phone 1 = 7075899966 |
| Telegram silent | ngrok running; re-run `setup_webhook.py` |
| Graph empty | Re-run `python -m data.wipe_and_seed_four_phone_demo` |
| Chain only 2 donors (not 8) | Expected with `THREE_PHONE_DEMO_MODE=true` — only 2 real demo donors in live chain |
| Patient portal empty | Use `/patient?id=P-THREE-001` |
| Phone 4 already exists | Delete before registration demo (Step 4.5) |
| Wrong donors matched | Re-seed; confirm `THREE_PHONE_DEMO_MODE=true` |
| Light mode broken | Hard refresh (Ctrl+Shift+R) |

---

# Automated smoke (after manual demo)

```powershell
cd BloodBridge_AI_Backend
python run_scenarios_ae.py
python scripts/test_bolna_call.py all
```

---

# Seed data reference

| ID | Type | Purpose |
|----|------|---------|
| D-THREE-001 | Donor (Phone 1) | Live chain pos 1, voice, Telegram |
| D-THREE-002 | Donor (Phone 2) | Live chain pos 2, backup |
| P-THREE-001 | Patient (Phone 3) | Emergency default, anti-Kell |
| P-THREE-002 | Patient (bg) | Hungarian optimizer 2nd patient |
| D-BGND-001..010 | Donors (bg) | Graph, leaderboard, churn variety |
| REQ-DEMO-HIST-001 | Emergency (bg) | Patient chain history UI |

**Real phones in DB after seed:** 3 only (`7075899966`, `9642273274`, `6305589656`)  
**Phone 4:** Register live → delete after demo
