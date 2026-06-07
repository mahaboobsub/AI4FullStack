# BloodBridge AI — E2E Manual Test Guide (3 Phones + 14 Agents)

Use this checklist **before deploy**. Run every test in order, fill in the issue tracker at the bottom, then proceed to [BloodBridge_AI_Backend/DEPLOY.md](BloodBridge_AI_Backend/DEPLOY.md).

---

## Test Actors

| Phone | Name | Role | Donor ID | Blood | Expected in chain |
|-------|------|------|----------|-------|-------------------|
| 7075899966 | Sheik Bhai | Donor 1 | D-72485 | O+ | **ALERTED first** (Telegram + voice) |
| 9642273274 | Arjun Singh | Donor 2 | D-33512 | A+ | PENDING |
| 6305589656 | Ravi Kumar | Donor 3 | D-50013 | B+ | PENDING (voice if no Telegram) |

| Entity | ID | Details |
|--------|-----|---------|
| Patient | P-10026 | B− @ Apollo Banjara Hills |
| Emergency | REQ-TEST-B001 | Pre-seeded, IN_PROGRESS |
| Telegram bot | [@ummedrakho_bot](https://t.me/ummedrakho_bot) | Webhook required |

---

## Part 0 — Environment Setup (Do This First)

You need **4 terminals** open at the same time.

### Terminal 1 — ngrok (Telegram webhook tunnel)

```powershell
ngrok http 8000
```

Copy the **HTTPS** URL (example: `https://xxxx.ngrok-free.app`).  
Keep this terminal running. **Every ngrok restart changes the URL.**

### Terminal 2 — Backend

```powershell
cd "d:\projects with ai\AI4FullStack\BloodBridge_AI_Backend"

# Kill stale Python processes if port 8000 acts weird
taskkill /F /IM python.exe

# Activate venv if needed, then start API (ONE instance only)
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
```

Wait for: `Application startup complete` and `Uvicorn running on http://0.0.0.0:8000`

### Terminal 3 — Register Telegram webhook

Run **after** ngrok is up and backend is running:

```powershell
cd "d:\projects with ai\AI4FullStack\BloodBridge_AI_Backend"
.\venv\Scripts\python.exe setup_webhook.py
```

Expected output:
- `Telegram webhook set successfully!`
- `Pending updates: 0`
- `Last error: none`

Confirm `.env` has `TELEGRAM_WEBHOOK_URL=https://<your-ngrok>.ngrok-free.app/webhook/telegram`

### Terminal 4 — Frontend

```powershell
cd "d:\projects with ai\AI4FullStack\BloodBridge_AI_frontend\artifacts\bloodbridge"
npm run dev
```

Open: **http://localhost:5173**

### Seed E2E data (run once per test session)

```powershell
cd "d:\projects with ai\AI4FullStack\BloodBridge_AI_Backend"
.\venv\Scripts\python.exe -m data.seed_e2e_three_phones
```

Expected:
```
OK D-72485 (Sheik Bhai) +917075899966
OK D-33512 (Arjun Singh) +919642273274
OK D-50013 (Ravi Kumar) +916305589656
OK emergency REQ-TEST-B001 IN_PROGRESS
OK blood chain: 1 ALERTED + 2 PENDING
OK Neo4j COMPATIBLE_WITH + IN_CHAIN edges
```

### Pre-flight checks (2 minutes)

| Check | Command / Action | Pass? |
|-------|------------------|-------|
| Backend health | Browser or PowerShell: `http://127.0.0.1:8000/health` | ☐ |
| Graph API | `http://127.0.0.1:8000/api/donors/graph/data?request_id=REQ-TEST-B001` → 5 nodes | ☐ |
| Emergencies API | `http://127.0.0.1:8000/api/emergencies` → REQ-TEST-B001 with Sheik ALERTED | ☐ |
| Webhook | `setup_webhook.py` shows no last error | ☐ |
| `.env` flags | `THREE_PHONE_DEMO_MODE=false` | ☐ |
| Bolna keys | `BOLNA_API_KEY` and `BOLNA_AGENT_ID` set in `.env` | ☐ |

**Graph should show:** P-10026 → Apollo Banjara Hills → D-72485 (ALERTED), D-33512, D-50013

---

## Part 1 — Telegram Tests (Phones)

### Test 1 — Bot registration (`/start`)

**On all 3 phones:**

1. Open Telegram → search **@ummedrakho_bot**
2. Tap **Start** or send `/start`
3. Bot asks: *"Are you a donor or patient?"*
4. Reply: `donor`
5. Complete: name, blood type, city, phone

**Phone 2 (9642273274) — register fresh donor:**

| Field | Value |
|-------|-------|
| Name | Arjun Singh |
| Blood | A+ |
| City | Hyderabad |
| Phone | 9642273274 |

**Pass criteria:**
- [ ] All 3 phones get bot replies (no timeout)
- [ ] Backend terminal shows `POST /webhook/telegram 200 OK`
- [ ] Donor row exists in Supabase for each phone

**Staff dashboard check:** none required yet.

---

### Test 2 — Blood card OCR + antigen scan

**On Phone 1 (Sheik — 7075899966):**

1. Open chat with @ummedrakho_bot
2. Send a **photo of a blood group card** (camera or gallery)
3. Wait 10–20 seconds

**Expected bot reply (example):**
```
✅ Blood card scanned!
Blood group: O+
Antigens: D+, K−, Fya+ ...
Saved to your profile and admin graph.
```

**Backend terminal — look for:**
```
Textract: blood_group=O+, name=...
Bedrock vision: blood_group=O+, antigens=['D', 'K', 'Fya', ...], confidence=0.95
Antigen extraction: panel={'D': 'Positive', 'K': 'Negative', ...}
```

> OCR pipeline: **AWS Textract** (raw text) + **Bedrock Claude Sonnet 4.6 vision** (blood group + antigen panel). Override model via `BEDROCK_VISION_MODEL_ID` in `.env`.

**Admin graph check (browser):**

1. Go to **http://localhost:5173/dashboard/graph**
2. Search box should default to `REQ-TEST-B001` (or type it and press Enter)
3. Click **Sheik Bhai** node (D-72485)
4. Right panel → **OCR Antigen Panel** section should show scanned antigens

**Pass criteria:**
- [ ] Bot confirms blood group + antigens
- [ ] Terminal shows Textract/OCR logs
- [ ] Graph donor sheet shows antigen panel (may need page refresh; WebSocket toast: `OCR: D-72485...`)
- [ ] Neo4j donor node updated (agents use this for matching)

---

### Test 3 — Bot Q&A (14-agent tool calling)

**On any phone with an active donor session:**

Send these messages one at a time:

1. `What are my badges?`
2. `When can I donate next?`
3. `Show my profile`

**Pass criteria:**
- [ ] Bot answers with real donor data (not generic errors)
- [ ] Backend logs show tool calls: `get_donor_profile`, `get_donation_history`, `get_badges`
- [ ] Responses mention your name / donor ID

---

### Test 4 — Emergency → LangGraph pipeline

**Option A — Use pre-seeded emergency (fastest)**

Already active after seed: `REQ-TEST-B001`. Skip to pass criteria below.

**Option B — Create new emergency from dashboard**

1. Staff login: **http://localhost:5173/login**
   - Email: `staff2@apollo.org`
   - Password: `staff123`
2. Go to **http://localhost:5173/dashboard/emergency**
3. Click **New Emergency**
4. Fill:

| Field | Value |
|-------|-------|
| Patient ID | P-10026 |
| Blood Type | B- |
| City | Hyderabad |
| Ward | Thalassemia Day Care |
| Hospital | Apollo Banjara Hills |

5. Submit

**Watch backend terminal for agent logs:**

```
[REQ-xxx] IntakeAgent started...
[REQ-xxx] MatchingAgent: 3 donors found
[REQ-xxx] OutreachAgent: alerting...
  → Telegram sent to Sheik Bhai (+917075899966)
[REQ-xxx] MonitorAgent: checking chain...
```

**Phone 1 (Sheik) should receive:**

```
🚨 URGENT: Patient P-10026 needs B- blood at Apollo Banjara Hills
```

**Pass criteria:**
- [ ] All 4+ agent log lines appear in terminal
- [ ] Phone 1 gets Telegram alert
- [ ] Dashboard emergency card updates (WebSocket)
- [ ] Chain shows Sheik at position 1 = ALERTED

---

### Test 5 — Donor YES / NO response

**On Phone 1 (Sheik) — reply to the URGENT alert:**

#### Path A — Accept (YES)

1. Reply: `YES` (or `yes` / `Y`)

**Expected:**
- Bot confirms donation
- Chain status → **CONFIRMED** for D-72485
- Dashboard updates live (WebSocket)
- Log: `OutcomeAgent: chain confirmed D-72485`
- `life_saver` badge awarded

**Re-seed before Path B** if you already confirmed:
```powershell
.\venv\Scripts\python.exe -m data.seed_e2e_three_phones
```

#### Path B — Decline (NO) — for chain repair test

1. Reply: `NO`

**Expected:**
- Chain breaks for position 1
- RepairAgent runs
- Phone 3 (Ravi) or Phone 2 gets next alert
- Log: `RepairAgent: escalating to position 2 donor D-50013` (or D-33512)

**Pass criteria:**
- [ ] YES → CONFIRMED on dashboard + no 500 error in terminal
- [ ] NO → next donor alerted + repair logs visible

---

### Test 6 — 1-minute voice escalation (Bolna call)

This tests: *no Telegram reply within 1 minute → automatic voice call*.

#### Setup

1. **Re-seed** so Sheik is ALERTED again:
   ```powershell
   .\venv\Scripts\python.exe -m data.seed_e2e_three_phones
   ```
2. Confirm Phone 1 received the Telegram URGENT message
3. **Do NOT reply** on Telegram
4. Keep Phone 1 **unlocked** and volume up (Bolna will call +917075899966)

#### Wait

- Scheduler runs every **1 minute**
- After ~1–2 minutes, watch backend terminal:

```
[SCHED-B001] ChainMonitorAgent: timeout detected
Scheduler: Stale donors detected (Telegram timeout). Running voice agent...
VoiceAgentNode: placed 1 Bolna call(s)
```

#### Expected on Phone 1

- Incoming voice call from Bolna AI agent
- Call explains B− blood needed at Apollo Banjara Hills

#### Expected on dashboard

- Toast: `No reply in 1 min — calling Sheik Bhai`
- Chain status for D-72485 may change to **VOICE**

**Pass criteria:**
- [ ] Call received on 7075899966 within 2 minutes of alert
- [ ] Terminal shows Bolna `INITIATED` / `queued` with a `call_id`
- [ ] No `demo_mock` in voice result (real Bolna call)

---

### Test 7 — Chain repair (3-ring radius)

**Prerequisite:** Test 5 Path B (Sheik replies `NO`) OR wait for voice timeout then decline on call.

**Steps:**

1. Ensure Sheik is DECLINED or timed out
2. Watch backend for RepairAgent:

```
RepairAgent: escalating to position 2 donor D-50013
Ring 1 (5km) → Ring 2 (15km) → Ring 3 (50km)
```

3. **Phone 3 (Ravi — 6305589656)** should get alert  
   (Ravi has no Telegram by default → **Bolna voice call** instead)

**Optional — give Ravi Telegram alerts:**

1. On Phone 3, send `/start` to @ummedrakho_bot and register
2. Re-seed to link chat ID

**Pass criteria:**
- [ ] Position 2+ donor alerted after Sheik decline
- [ ] Ravi receives voice call or Telegram (depending on Telegram link)
- [ ] Dashboard chain shows updated positions

---

## Part 2 — Voice Call Manual Tests (All 3 Phones)

Use these to verify Bolna **before** or **alongside** Test 6.

### Method A — Script (recommended)

```powershell
cd "d:\projects with ai\AI4FullStack\BloodBridge_AI_Backend"

# Call all 3 E2E phones
.\venv\Scripts\python.exe scripts\test_bolna_call.py all

# Or one donor at a time:
.\venv\Scripts\python.exe scripts\test_bolna_call.py D-72485   # Sheik
.\venv\Scripts\python.exe scripts\test_bolna_call.py D-33512   # Arjun
.\venv\Scripts\python.exe scripts\test_bolna_call.py D-50013   # Ravi
```

**Expected output per donor:**
```
Result: {'status': 'INITIATED', 'call_id': '<uuid>', 'provider': 'bolna', 'bolna_status': 'queued'}
```

**On each phone:** answer the call within 30 seconds.

| Phone | Name | Expect call? |
|-------|------|--------------|
| 7075899966 | Sheik | ☐ |
| 9642273274 | Arjun | ☐ |
| 6305589656 | Ravi | ☐ |

### Method B — API curl (single donor)

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/donors/D-72485/voice"
```

### Method C — Automatic (scheduler, Test 6)

No action — just wait 1 minute after ALERTED without replying.

### Voice safety guard

In `APP_ENV=development`, Bolna only calls the **3 E2E phones** listed above unless `BOLNA_ALLOW_ANY_PHONE=true` in `.env`.

---

## Part 3 — Web Portal Tests (Browser)

### Test 8 — Donor portal

For **each donor**, open **http://localhost:5173/donor/login**

| Donor | Login with | Password |
|-------|------------|----------|
| Sheik | `7075899966` or `D-72485` | `donor123` (or any if phone lookup works) |
| Arjun | `9642273274` or `D-33512` | `donor123` |
| Ravi | `6305589656` or `D-50013` | `donor123` |

**Check each portal:**

- [ ] Name, blood type, city correct
- [ ] Active emergency card: "URGENT MATCH FOUND" (when chain active)
- [ ] Eligibility card (green/amber)
- [ ] Leaderboard (Sheik #1, Ravi #2, Arjun #3 — approximate)
- [ ] Blood Bridge shows connected patients
- [ ] Badges (`life_saver` if donation confirmed)
- [ ] DPDP consent section visible

---

### Test 9 — Patient portal

1. Open **http://localhost:5173/patient/login**
2. Login:

| Field | Value |
|-------|-------|
| Identifier | `P-10026` |
| Password | `tg:6352238849` *(from seed — matches Sheik's Telegram chat ID)* |

> If login fails, check seed output or Supabase `patients.password` for P-10026.

**Check:**

- [ ] Next transfusion date shown
- [ ] Hemoglobin gauge
- [ ] Linked donors (Sheik, Ravi, Arjun)
- [ ] Click **Generate Auto-Schedule** → dates appear
- [ ] Blood Bridge card shows donors

---

### Test 10 — Admin dashboard

1. Staff login: **http://localhost:5173/login** → `staff2@apollo.org` / `staff123`
2. Go to **http://localhost:5173/dashboard/admin**

**Check:**

- [ ] LangGraph traces show `REQ-TEST-B001` (or your new REQ) with node timings
- [ ] **Hungarian Optimizer** → Run Optimizer → assigns donors to patients
- [ ] **Demand Forecast** → run → shortage alerts appear
- [ ] **Retrain XGBoost** → training logs in backend terminal

---

### Test 11 — Neo4j graph (admin)

1. Go to **http://localhost:5173/dashboard/graph**
2. Search: `REQ-TEST-B001`
3. Press Enter or click Search

**Expected force graph:**

```
P-10026 (patient)
    ↓
Apollo Banjara Hills (hospital)
    ↓
D-72485 (Sheik) — ALERTED or CONFIRMED
D-33512 (Arjun) — PENDING
D-50013 (Ravi)  — PENDING
```

**Click a donor node:**

- [ ] Donor detail sheet opens
- [ ] Blood type shown
- [ ] OCR Antigen Panel (after Test 2 photo upload)
- [ ] Compatibility / churn scores

**Live updates:**

- [ ] After OCR scan → toast + graph refresh
- [ ] After YES/NO → chain colors update (green/amber/red)

---

## Part 4 — Telegram utility commands

Useful during testing:

| Command | Purpose |
|---------|---------|
| `/start` | Begin registration |
| `/status P-10026` | Show active chain for patient |
| `/emergency B- P-10026 Apollo Banjara Hills` | Staff-style emergency trigger (if staff chat linked) |

---

## Issue Tracker (fill as you test)

| # | Test | Result | Issue / notes |
|---|------|--------|---------------|
| 1 | Telegram `/start` | ☐ Pass ☐ Fail | |
| 2 | Blood card OCR | ☐ Pass ☐ Fail | |
| 3 | Bot Q&A | ☐ Pass ☐ Fail | |
| 4 | Emergency creation | ☐ Pass ☐ Fail | |
| 5 | Donor YES reply | ☐ Pass ☐ Fail | |
| 5b | Donor NO reply | ☐ Pass ☐ Fail | |
| 6 | 1-min voice escalation | ☐ Pass ☐ Fail | |
| 6b | Manual Bolna all 3 | ☐ Pass ☐ Fail | |
| 7 | Chain repair | ☐ Pass ☐ Fail | |
| 8 | Donor portal | ☐ Pass ☐ Fail | |
| 9 | Patient portal | ☐ Pass ☐ Fail | |
| 10 | Admin panel | ☐ Pass ☐ Fail | |
| 11 | Neo4j graph | ☐ Pass ☐ Fail | |

---

## Troubleshooting

### Bot not responding

1. Is ngrok running? (`http://127.0.0.1:4040`)
2. Re-run `setup_webhook.py`
3. Is backend on port 8000? (`http://127.0.0.1:8000/health`)
4. Check Telegram webhook: `Last error: none` in setup script output

### `localhost:8000` returns stale/wrong data

Zombie Python process on port 8000:

```powershell
taskkill /F /IM python.exe
Start-Sleep 3
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
```

Run **only one** uvicorn instance.

### YES/NO causes 500 error

Fixed in codebase (`utc_now_iso`). Pull latest and restart backend.

### Voice call not received

1. Check `BOLNA_API_KEY` + `BOLNA_AGENT_ID` in `.env`
2. Run `scripts\test_bolna_call.py D-72485` manually
3. Confirm phone is in E2E allowlist (+917075899966, +919642273274, +916305589656)
4. Check donor has `outreach_voice` consent (seed grants this)

### Ravi gets voice but not Telegram

By design until he `/start` the bot. Seed sets `telegram_chat_id = None` for D-50013.

### Graph empty or no hospital node

```powershell
.\venv\Scripts\python.exe -m data.seed_e2e_three_phones
```

Then reload graph with `REQ-TEST-B001`.

### ngrok URL changed

Every ngrok restart:

```powershell
.\venv\Scripts\python.exe setup_webhook.py
```

Update `TELEGRAM_WEBHOOK_URL` in `.env`.

---

## Pre-Deploy Checklist

Complete after all tests pass:

- [ ] Issue tracker: all critical tests (1–7, 11) = Pass
- [ ] No secrets committed to git (`.env` stays local)
- [ ] `THREE_PHONE_DEMO_MODE=false` for production matching
- [ ] Replace ngrok with production HTTPS URL for Telegram webhook
- [ ] Set `APP_ENV=production` on deploy host
- [ ] Review [BloodBridge_AI_Backend/DEPLOY.md](BloodBridge_AI_Backend/DEPLOY.md)
- [ ] Set production env vars: Supabase, Neo4j, Groq, Bolna, Telegram
- [ ] Run `python -m data.seed_e2e_three_phones` only on **staging** — not production
- [ ] Frontend: set `VITE_API_URL` to production API URL before build

### Quick deploy command reference

```powershell
# Backend (production example — use your host)
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend build
cd BloodBridge_AI_frontend/artifacts/bloodbridge
npm run build
```

---

## Suggested Test Order (90-minute run)

| Time | Step |
|------|------|
| 0–15 min | Part 0 setup + seed + pre-flight checks |
| 15–25 min | Tests 1–3 (Telegram register, OCR, Q&A) |
| 25–35 min | Test 4 (emergency alert on Phone 1) |
| 35–40 min | Test 5A (YES) **or** re-seed → Test 5B (NO) |
| 40–45 min | Manual voice: `test_bolna_call.py all` |
| 45–50 min | Test 6 (1-min auto voice — re-seed, don't reply) |
| 50–55 min | Test 7 (chain repair after NO) |
| 55–70 min | Tests 8–9 (donor + patient portals) |
| 70–80 min | Tests 10–11 (admin + graph) |
| 80–90 min | Fill issue tracker → pre-deploy checklist |

---

*Last updated: June 2026 — matches E2E seed `REQ-TEST-B001` and 3-phone Bolna guard.*
