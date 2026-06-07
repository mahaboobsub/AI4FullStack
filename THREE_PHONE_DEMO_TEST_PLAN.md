# BloodBridge AI — 3-Phone Live Demo Test Plan (4 Pillars)

Use **exactly these 3 phones** for all real-time actions. Background seed data (D-BGND-001..006, P-THREE-002) fills dashboards only.

| Phone | E.164 | Role | ID | Blood | Real-time actions |
|-------|-------|------|-----|-------|-------------------|
| **Phone 1** | +917075899966 | **Donor 1** Sheik Bhai | D-THREE-001 | B+ Kell-neg | Telegram YES/NO, Bolna voice call, Donor Portal |
| **Phone 2** | +919642273274 | **Donor 2** Arjun Singh | D-THREE-002 | O+ Kell-neg | Telegram registration, backup chain, Donor Portal |
| **Phone 3** | +916305589656 | **Patient** Ravi Kumar | P-THREE-001 | B+ anti-Kell | Patient Portal, **not** voice target |

**Bot:** [@ummedrakho_bot](https://t.me/ummedrakho_bot)  
**City:** Hyderabad · **Hospital:** KIMS Secunderabad  
**Emergency default:** P-THREE-001 / B+ / Hyderabad

---

## Part 0 — Setup (15 min, once per session)

### Terminal 1 — ngrok
```powershell
ngrok http 8000
```
Copy HTTPS URL → set `TELEGRAM_WEBHOOK_URL=https://<id>.ngrok-free.app/webhook/telegram` in `.env`

### Terminal 2 — Backend
```powershell
cd "BloodBridge_AI_Backend"
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Terminal 3 — Webhook + seed
```powershell
cd "BloodBridge_AI_Backend"
# Use venv if present; otherwise system Python (no venv in this repo):
python setup_webhook.py
python -m data.seed_three_phones
```
**Requires:** ngrok already running (Terminal 1). `setup_webhook.py` auto-detects the ngrok URL and writes `TELEGRAM_WEBHOOK_URL` to `.env`.

### Terminal 4 — Frontend
```powershell
cd "BloodBridge_AI_frontend\artifacts\bloodbridge"
pnpm run dev
```
Open http://localhost:5173 — toggle **light mode** on Donor + Patient portals.

### `.env` flags for live demo
```env
APP_ENV=development
DEMO_MOCK_MODE=false          # real Bolna calls
THREE_PHONE_DEMO_MODE=true    # restrict matching to D-THREE-001/002
BOLNA_API_KEY=...
BOLNA_AGENT_ID=...
TELEGRAM_BOT_TOKEN=...
```

### Pre-flight checklist
| Check | URL / action | Pass |
|-------|----------------|------|
| Health | http://localhost:8000/health | ☐ |
| Patient exists | GET /api/patients/P-THREE-001 | ☐ |
| Donors exist | GET /api/donors/D-THREE-001 | ☐ |
| Graph | GET /api/donors/graph/data?request_id=all | ☐ |
| Webhook | setup_webhook.py → no last error | ☐ |

---

## PILLAR 1 — Smart Matching (7-parameter + antigen ISBT)

**Story:** Patient P-THREE-001 has **anti-Kell** → only Kell-negative donors score high.

### 1.1 Staff — trigger emergency
1. Login → `/dashboard/emergency`
2. **New Emergency** — defaults: `P-THREE-001`, `B+`, `Hyderabad`
3. Submit → watch terminal: `IntakeAgent` → `antigen_score` → `neo4j_match`

**Pass:** Chain shows 8 nodes; D-THREE-001 position 1 = ALERTED  
**Pass:** Kell-positive background donors rank lower / excluded

### 1.2 Graph page
1. `/dashboard/graph` → live Neo4j/Supabase network
2. Filter: active emergency request

**Pass:** Patient node + hospital + donor edges with antigen scores (not mock)

### 1.3 Hungarian optimizer
1. `/dashboard/admin` → **Run Optimizer Preview**
2. If 2+ IN_PROGRESS emergencies, see disjoint donor assignment

**Pass:** No donor assigned to two patients

### 1.4 Matching API (optional)
```powershell
.\venv\Scripts\python.exe test_scenario_a.py
```
**Pass:** Top donors Kell-negative; antigen scores vary (not all 1.0)

---

## PILLAR 2 — Multi-Agent Coordination (14 LangGraph nodes)

### 2.1 AI voice call — **Phone 1 only** (do this first)

```powershell
cd BloodBridge_AI_Backend
.\venv\Scripts\python.exe scripts\test_bolna_call.py D-THREE-001
```

Or from dashboard: `/dashboard/donors` → 📞 on Sheik Bhai

**Pass:** Phone **7075899966** rings within 30s  
**Pass:** Backend log: `Bolna call INITIATED` (not DEMO_MOCK_MODE skip)  
**Fail fix:** Set `DEMO_MOCK_MODE=false`, verify `BOLNA_API_KEY` + `BOLNA_AGENT_ID`

### 2.2 Telegram outreach — Phone 1
1. Phone 1 opens @ummedrakho_bot → `/start`
2. Or dashboard: Donors → 💬 on Sheik Bhai

**Pass:** Hindi/English alert with B+ KIMS emergency  
**Pass:** Backend: `POST /webhook/telegram 200`

### 2.3 Full coordination loop
| Step | Action | Phone | Expected |
|------|--------|-------|----------|
| 1 | Create emergency | Staff dashboard | Chain ALERTED pos 1 |
| 2 | Telegram alert | Phone 1 | Message received |
| 3 | No reply 5–7 min | — | Monitor → voice escalation |
| 4 | Reply `YES` | Phone 1 | Chain → CONFIRMED (WebSocket) |
| 5 | Mark Resolved | Emergency dashboard | Status COMPLETED |
| 6 | Decline test | Phone 1 sends `NO` | Repair → Phone 2 alerted |

### 2.4 WebSocket real-time
1. Keep `/dashboard/emergency` open
2. Confirm donor on Telegram

**Pass:** Chain dot turns green without refresh

### 2.5 Proactive scheduler
1. Phone 3 → `/patient?id=P-THREE-001`
2. Tap **Generate Auto-Schedule**

**Pass:** Toast success; upcoming dates appear (needs transfusion_count ≥ 2)

---

## PILLAR 3 — Donor Engagement & Gamification

### 3.1 Donor portal — Phone 1
1. `/donor/login` → phone `7075899966` or ID `D-THREE-001`
2. Check in **light mode**: badges, lives saved counter, eligibility card, DPDP consent

**Pass:** Rank, impact stories, health status, locations CRUD

### 3.2 Donor portal — Phone 2
1. Login `9642273274` or register via Telegram first
2. Toggle availability pause/resume

### 3.3 Patient portal — Phone 3
1. `/patient/login` or `/patient?id=P-THREE-001`
2. Linked donors, chain history, transfusion calendar, antibody flags

### 3.4 Admin engagement
| Feature | Page | Action |
|---------|------|--------|
| Churn scores | `/dashboard/donors` | See churn_score column |
| Demand forecast | `/dashboard/admin` | Run Forecast → 28-day chart |
| XGBoost retrain | `/dashboard/admin` | Retrain Now → jobId toast |
| Leaderboard | Donor portal | Top 10 Hyderabad |

---

## PILLAR 4 — Scale & Responsible AI

### 4.1 Telegram bot — all cases (Phone 1 & 2)

| # | Test | Command / action | Pass |
|---|------|------------------|------|
| T1 | Start + consent | `/start` | ☐ |
| T2 | Register donor | `/register` or guided flow | ☐ |
| T3 | Profile | `/profile` | ☐ |
| T4 | Eligibility | `/eligibility` or free text | ☐ |
| T5 | Badges | `/badges` | ☐ |
| T6 | Leaderboard | `/leaderboard` | ☐ |
| T7 | OCR blood card | Send photo of blood group card | ☐ |
| T8 | Emergency accept | Reply `YES` to alert | ☐ |
| T9 | Emergency decline | Reply `NO` | ☐ |
| T10 | Language | Ask in Hindi/Telugu | ☐ |

**Phone 2 only:** Fresh registration with blood O+, city Hyderabad.

### 4.2 Map + blood banks
1. `/dashboard/map` → Hyderabad banks, filter B+
2. (Optional) POST `/api/blood-banks/refresh` via Swagger

### 4.3 DPDP (Donor portal)
1. Consent summary → revoke → export my data

### 4.4 Admin profile + staff
1. Staff login → sidebar shows your name/hospital
2. Admin → staff add/delete (real API)

---

## Recommended demo order (45 min showcase)

```
0. Seed + webhook (5 min)
1. PILLAR 2 — Voice call Phone 1 (5 min)          ← judges hear the phone ring
2. PILLAR 2 — Telegram alert + YES (5 min)
3. PILLAR 1 — Emergency dashboard + Graph (5 min)
4. PILLAR 3 — Donor portal Phone 1 light mode (5 min)
5. PILLAR 3 — Patient portal Phone 3 (5 min)
6. PILLAR 1 — Hungarian optimizer (3 min)
7. PILLAR 3 — Demand forecast + retrain (5 min)
8. PILLAR 4 — Telegram registration Phone 2 (7 min)
9. PILLAR 4 — Map + DPDP (5 min)
```

---

## Quick login cheatsheet

| Role | Login | Portal |
|------|-------|--------|
| Staff | `/login` (staff creds) | `/dashboard/emergency` |
| Donor 1 | `7075899966` | `/donor` |
| Donor 2 | `9642273274` | `/donor` |
| Patient | `6305589656` or `P-THREE-001` | `/patient` |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Voice doesn't ring | `DEMO_MOCK_MODE=false`, Bolna keys set |
| Telegram silent | ngrok running, `setup_webhook.py` OK |
| Graph shows mock | Run seed; create active emergency |
| Patient portal empty | URL `?id=P-THREE-001` |
| Matching wrong donors | `THREE_PHONE_DEMO_MODE=true` + re-seed |
| Light mode broken | Hard refresh; check `dark:` classes |

---

## Automated smoke (after manual demo)

```powershell
cd BloodBridge_AI_Backend
.\venv\Scripts\python.exe run_scenarios_ae.py
.\venv\Scripts\python.exe scripts\test_bolna_call.py all
```
