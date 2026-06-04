# 🩸 BloodBridge AI — Deployment Guide

Complete step-by-step guide to deploy BloodBridge AI backend to production using free-tier cloud services.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Git | Latest | [git-scm.com](https://git-scm.com) |
| Render account | Free | [render.com](https://render.com) |

---

## Step 1 — External Services Setup

### 1.1 Supabase (PostgreSQL)

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Note your **Project URL**, **anon key**, and **service_role key**
3. In the SQL Editor, run `data/supabase_schema.sql` to create all tables
4. Run `data/seed_neo4j.py` to populate initial data (see Step 4)
5. Enable **Row Level Security** on `donors`, `patients`, `blood_requests` tables

**Environment variables to note:**
```
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJ...  (anon key)
SUPABASE_SERVICE_KEY=eyJ...  (service_role key — keep secret!)
```

### 1.2 Neo4j Aura (Graph DB)

1. Go to [console.neo4j.io](https://console.neo4j.io) → **New Instance** → Free tier
2. Download the credentials file when prompted (only shown once!)
3. Connect via Neo4j Browser and run `data/neo4j_schema.cypher`
4. Run the seed script: `python data/seed_neo4j.py`

**Environment variables to note:**
```
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-generated-password
```

### 1.3 Groq API (Llama-3.3-70B)

1. Go to [console.groq.com](https://console.groq.com) → **API Keys** → Create
2. Free tier: 30 RPM, 6000 tokens/min — sufficient for demo

```
GROQ_API_KEY=gsk_...
```

### 1.4 Google AI (Gemini)

1. Go to [aistudio.google.com](https://aistudio.google.com) → **Get API Key**
2. Free tier: 15 RPM Gemini 1.5 Flash

```
GOOGLE_API_KEY=AIza...
```

### 1.5 Telegram Bot

1. Message `@BotFather` on Telegram → `/newbot`
2. Note the **bot token**
3. Set a webhook secret (any random 32-char string)

```
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_WEBHOOK_SECRET=my_random_secret_32chars
```

After deployment, set the webhook:
```bash
curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://bloodbridge-api.onrender.com/api/webhooks/telegram&secret_token={SECRET}"
```

### 1.6 Twilio (SMS + Voice) — Optional

1. Go to [twilio.com](https://twilio.com) → free trial account
2. Get a phone number
3. Note Account SID, Auth Token, phone number

```
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_FROM_NUMBER=+15551234567
TWILIO_MESSAGING_SERVICE_SID=MGxxxxxxxx
```

### 1.7 Vapi.ai (Voice AI) — Optional

1. Go to [vapi.ai](https://vapi.ai) → create account
2. Create an assistant → note Assistant ID
3. Add a phone number → note Phone Number ID

```
VAPI_API_KEY=vapi_...
VAPI_PHONE_NUMBER_ID=pn_...
VAPI_ASSISTANT_ID=asst_...
```

---

## Step 2 — Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/BloodBridge-AI.git
cd BloodBridge-AI/BloodBridge_AI_Backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 5. Seed databases
python data/seed_neo4j.py

# 6. Run locally
uvicorn main:app --reload --port 8000

# 7. Verify health
curl http://localhost:8000/health
```

---

## Step 3 — Deploy to Render.com

### 3.1 Connect Repository

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click **New** → **Blueprint**
3. Connect your GitHub/GitLab repository
4. Render auto-detects `render.yaml` and shows 2 services to create

### 3.2 Set Environment Variables

In the Render dashboard for `bloodbridge-api`:

1. Go to **Environment** tab
2. Click **Add Environment Variable** for each `sync: false` variable in `render.yaml`
3. Paste the values from Step 1

> [!IMPORTANT]
> **Never commit API keys to git.** Use Render's environment variables for all secrets.

### 3.3 Deploy

Click **Apply** — Render will:
1. Clone your repo
2. Install Python dependencies (`pip install -r requirements.txt`)
3. Install Tesseract OCR language packs (10 Indian languages)
4. Start the FastAPI server with `uvicorn`

Build takes ~3-5 minutes on first deploy.

### 3.4 Verify Deployment

```bash
# Health check — should return {"status": "ok", ...}
curl https://bloodbridge-api.onrender.com/health

# API docs
open https://bloodbridge-api.onrender.com/docs

# Test emergency endpoint
curl -X POST https://bloodbridge-api.onrender.com/api/emergencies \
  -H "Content-Type: application/json" \
  -d '{"blood_type":"O-","urgency_level":"CRITICAL","city":"Hyderabad","hospital_name":"NIMS"}'
```

---

## Step 4 — Tesseract OCR on Render

Render's build environment supports `apt-get`. The `buildCommand` in `render.yaml` already installs all 10 Indian language packs. No additional config needed.

To verify OCR after deploy:
```bash
curl -X POST https://bloodbridge-api.onrender.com/api/donors/verify-blood-card \
  -F "file=@test_blood_card.jpg"
```

---

## Step 5 — APScheduler Worker

The background worker (`bloodbridge-worker`) runs recurring jobs:
- Every 2 hours: churn score recalculation
- Daily at 2 AM IST: leaderboard refresh
- Hourly: stale chain detection + repair

Verify it's running in Render's **Logs** tab.

---

## Step 6 — LoRa Gateway Setup (Optional)

For rural offline support:

### Hardware Required
- Raspberry Pi 4 (any model)
- LoRa HAT (e.g., Waveshare SX1268 433M LoRa HAT)
- 433 MHz antenna

### Gateway Software
```bash
# On Raspberry Pi
pip install pyserial httpx

# Configure gateway to POST decoded packets to:
# POST https://bloodbridge-api.onrender.com/api/lora/receive

# Test connectivity
curl https://bloodbridge-api.onrender.com/api/lora/status
```

---

## Environment Variables Checklist

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key |
| `NEO4J_URI` | ✅ | Neo4j Aura connection URI |
| `NEO4J_USERNAME` | ✅ | Neo4j username |
| `NEO4J_PASSWORD` | ✅ | Neo4j password |
| `GROQ_API_KEY` | ✅ | Groq API key for Llama-3.3-70B |
| `GOOGLE_API_KEY` | ✅ | Google AI key for Gemini |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token |
| `TELEGRAM_WEBHOOK_SECRET` | ✅ | Webhook verification secret |
| `APP_ENV` | ✅ | Set to `production` |
| `TWILIO_ACCOUNT_SID` | Optional | SMS/Voice via Twilio |
| `TWILIO_AUTH_TOKEN` | Optional | |
| `TWILIO_FROM_NUMBER` | Optional | |
| `VAPI_API_KEY` | Optional | AI voice calls |
| `VAPI_PHONE_NUMBER_ID` | Optional | |
| `VAPI_ASSISTANT_ID` | Optional | |
| `STAFF_JWT_SECRET` | Optional | Staff authentication |

---

## Troubleshooting

### Neo4j Connection Fails
- Check that your IP is whitelisted in Neo4j Aura console (or allow all: `0.0.0.0/0`)
- Verify `NEO4J_URI` uses `neo4j+s://` (not `bolt://`) for Aura

### Supabase 401 Errors
- Make sure you're using `SUPABASE_SERVICE_KEY` (not anon key) for admin routes
- Check RLS policies in Supabase → Table Editor

### Tesseract Not Found
- Rebuild Render service to re-run the `apt-get install` buildCommand
- Verify with: `GET /health` → check OCR service status

### Rate Limit Errors (429)
- Emergency endpoint: 5/hour per IP
- Bulk import: 3/day per IP
- Voice calls: 10/hour per IP

### Render Free Tier Cold Start
- Free tier spins down after 15 min of inactivity
- First request after sleep takes ~30s
- Upgrade to Starter ($7/mo) for always-on

---

## Production Security Checklist

- [ ] All secrets in Render env vars (not in git)
- [ ] `APP_ENV=production` set
- [ ] CORS restricted to frontend domain (update `main.py`)
- [ ] Telegram webhook secret configured
- [ ] Supabase RLS enabled on all donor/patient tables
- [ ] Staff auth token rotated from default
- [ ] Neo4j password changed from auto-generated

---

## Demo Run (No Cloud Required)

To run a full pipeline demo locally without any cloud services:

```bash
python demo_run.py
```

This runs the entire 14-node LangGraph pipeline with mocked external services
and prints a colored step-by-step trace to the terminal.
