<![CDATA[<div align="center">

# 🩸 BloodBridge AI

### Autonomous AI for Blood Donor Coordination

*We don't just notify donors — we coordinate, learn, and self-heal an entire blood support network, autonomously.*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.23-4581C3?logo=neo4j&logoColor=white)](https://neo4j.com)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-Claude%204-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Team Inqilab · DNR College of Engineering & Technology · Blend360 Hackathon**

---

[Features](#-features) · [Architecture](#-architecture) · [Tech Stack](#%EF%B8%8F-tech-stack) · [Getting Started](#-getting-started) · [API Reference](#-api-reference) · [Deployment](#-deployment) · [Roadmap](#-roadmap)

</div>

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [AI & ML Models](#-ai--ml-models)
- [Data Privacy & Security](#-data-privacy--security)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Demo Guide](#-demo-guide)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧬 About the Project

**BloodBridge AI** is an autonomous multi-agent AI platform that manages the entire lifecycle of blood donor coordination for the **Blood Warriors NGO** — an organization that supports **Thalassemia patients** in India who require blood transfusions **every 15–28 days, for life** (500–700 lifetime transfusions).

Unlike traditional blood-bank apps that are essentially contact lists with a "send" button, BloodBridge AI is a **self-driving coordination engine** built on a **14-node LangGraph state machine** where each node is an independent AI agent. The system autonomously handles:

- **Intelligent matching** — finding the right donor based on 6+ weighted parameters
- **End-to-end coordination** — from intake to confirmation with zero human intervention on the happy path
- **Self-healing chains** — detecting and repairing broken donor chains in seconds
- **Continuous learning** — improving outreach strategy from every donor interaction

---

## 🚨 The Problem

Blood Warriors coordinates voluntary donors for Thalassemia patients across India. They face **four critical operational failures**:

| # | Failure | Impact |
|---|---------|--------|
| 1 | **Manual Matching** | No prioritization, no way to resolve when 2 patients need the same rare donor |
| 2 | **Chain Collapse** | 8–10 donor "bridge" chains collapse when one says no; **80% of staff time** lost to manual follow-up calls |
| 3 | **Donor Attrition** | ~60% donors go inactive; generic reminders get only **15% response rate** |
| 4 | **Scale Limitations** | 36 states, 22+ languages, patchy rural internet, strict DPDP 2023 data law |

> *A human team literally cannot call hundreds of donors fast enough when a chain breaks.*

---

## 💡 Our Solution

> An **autonomous multi-agent AI platform** that takes a blood request from intake → matching → outreach → monitoring → self-repair → confirmation → engagement — **with zero human intervention on the happy path**, accessible via a zero-install Telegram bot and a live staff dashboard.

### The Four Pillars

| Pillar | Solves | Our Answer |
|--------|--------|------------|
| 🩸 **A. Smart Matching** | Right donor, right time | Geo radius-tier + weighted scoring + Hungarian optimizer |
| 🔗 **B. Autonomous Coordination** | Chain collapse, staff overload | 14-node LangGraph pipeline + self-healing chains + voice/SMS |
| 💚 **C. Engagement** | Donor drop-off | Churn ML + gamification + failure-learning + impact stories |
| 🌍 **D. Scale & Responsible AI** | Reach + privacy | Telegram + 10 languages + Bedrock + DPDP compliance + AWS |

---

## ✨ Features

### 🩸 Pillar A — Smart Matching

#### 1. Geo Radius-Tier Matching
Finds compatible donors by searching outward in **3 concentric geographic rings** instead of a single flat "same city" query:
- **Ring 1** (≤ 5 km) — Neighbourhood
- **Ring 2** (≤ 15 km) — City zone
- **Ring 3** (≤ 30 km) — Wide net (last-resort backups)

Uses **geohash bucketing** (precision-6, ~1.2 km cells) and **haversine distance** — no fragile city-string matching.

#### 2. Weighted Multi-Criteria Scoring
Every donor is ranked by a transparent, tunable formula:

```
score =  w1 · blood_match           (ABO+Rh exact = 1.0, partial = 0.8)
       + w2 · proximity             (1 − distance/30)
       + w3 · engagement            (calls-to-donation ratio, response rate, history)
       + w4 · eligibility_freshness (peaks at 56 days post-donation, decays to 365)
       + w5 · (1 − churn_score)     (avoid donors likely to drop off)
       + w6 · bridge_bonus          (donors already committed to THIS patient)
       − w7 · radius_penalty        (Ring 3 penalised, Ring 2 half, Ring 1 none)
```

Weights live in a single `WEIGHTS` dict — the NGO can tune behavior without touching code.

#### 3. Hungarian Multi-Patient Optimizer
When 2+ active patients compete for the same nearby donors, the **Hungarian algorithm** (`scipy.optimize.linear_sum_assignment`) computes the **globally optimal** donor→patient assignment. Available as an admin batch endpoint at `POST /api/admin/optimize-assignments`.

#### 4. Multi-Location Model
Patients register **1–5 search locations** (home, work, hospital). Donors register backup areas they can travel to. The matcher considers ALL locations and uses each donor's *best* (smallest) distance.

---

### 🔗 Pillar B — Autonomous Coordination

#### 5. 14-Node LangGraph Pipeline
The core of BloodBridge AI — a stateful graph where each node is an independent agent:

```
intake → eligibility → [antigen_score ∥ urgency_score] → neo4j_match
   → (conflict?) → planner → outreach → monitor
        ├─ confirmed  → outcome → gamification → END
        ├─ stale      → voice   → back to monitor
        ├─ declined   → repair  → re-outreach
        └─ exhausted  → inventory (blood bank fallback) → escalate
```

| Node | Role | Key Action |
|------|------|------------|
| `intake` | Request parser | Fetch patient + context, init AgentState |
| `eligibility` | Rule engine | WHO/NBTC filter: 56-day gap, medical hold, consent |
| `antigen_score` | Compatibility scorer | ABO+Rh now; 8-antigen ready for Phase 2 |
| `urgency_score` | XGBoost model | Score urgency 0–10 → CRITICAL/HIGH/ROUTINE |
| `neo4j_match` | Matching engine | Geo radius-tier + weighted score → top donors |
| `conflict` | Claude reasoner | Resolves 2-patients-1-donor conflicts |
| `planner` | Strategy LLM | Channel + tone + timing per donor (learned history) |
| `outreach` | Parallel dispatch | Telegram messages in each donor's language |
| `monitor` | Scheduled watcher | Every 5 min: detect stale/declined → route |
| `repair` | Chain fixer | Pull next-best backup donor, re-alert |
| `voice` | Voice agent | Bolna.ai call in donor's language; SMS fallback |
| `inventory` | Fallback agent | e-RaktKosh blood bank lookup |
| `gamification` | Reward engine | Badge checks + leaderboard update |
| `outcome` | Closer | Record result, update stats, schedule impact story |

**What makes it autonomous:**
1. **Shared typed state** — all 14 agents read/write one `AgentState`
2. **Conditional routing** — the graph picks the next node from state (not a fixed script)
3. **Self-looping** — monitor re-enters itself every 5 min until success or escalation

#### 6. Self-Healing Chains
```
chain_monitor (every 5 min)
   ↓ donor ALERTED >7 min, no reply  → escalate to AI voice call
   ↓ donor DECLINED / unreachable    → chain_repair pulls next-best backup
   ↓ 3 consecutive fails             → inventory fallback → alert staff (ntfy)
   ↓ donor reports "sick"            → auto-remove + pull replacement + notify
```
Every status change broadcasts live over **WebSocket** to the staff dashboard.

#### 7. Donor Health Self-Update
Donors can declare themselves temporarily unfit (illness, hospitalization) via Telegram or the Donor Portal. The system instantly removes them from active chains, triggers auto-repair, and notifies staff — all without exposing medical details to patients (DPDP-safe).

#### 8. AI Voice Calling + SMS Fallback
- **Bolna.ai** outbound calls in Indian languages (Sarvam AI TTS)
- TRAI safe hours enforced (8 AM – 9 PM IST)
- Keyword NLU for voice responses (haan/nahi/kal)
- SMS fallback after 2 failed call attempts
- HMAC-verified idempotent webhooks

#### 9. Demand Forecasting Agent
A standalone **5-node LangGraph** agent that predicts weekly blood demand and flags shortages BEFORE emergencies happen:
1. `data_collector` → Pull bridges due in next 28 days + 90-day emergency history
2. `schedule_analyzer` → Expand bridge recurrence into weekly needed-units
3. `supply_gap_node` → Demand vs supply per blood type per week
4. `bedrock_insight` → Claude turns numbers into plain-English action plan
5. `persist_node` → Write forecasts + ntfy alerts on deficits

Runs daily at 6 AM IST via APScheduler.

---

### 💚 Pillar C — Engagement

#### 10. Churn Prediction (XGBoost)
Trained on **real labels** from the Blood Warriors dataset. Features: `calls_to_donations_ratio`, `donation_count`, `response_rate`, `days_since_donation`, `is_one_time_donor`, `serves_active_bridge`.

**4 risk tiers → tiered interventions:**
| Risk Score | Tier | Action |
|-----------|------|--------|
| 0.0–0.3 | LOW | No action |
| 0.3–0.6 | MEDIUM | Send impact story |
| 0.6–0.8 | HIGH | Re-engagement badge challenge |
| 0.8–1.0 | CRITICAL | AI voice call |

#### 11. Gamification
**Badges:** First Drop (1), Lifeline (5), Bridge Hero (12), Rapid Responder (<2h confirm), Streak Keeper (3+ on-cycle), City Champion (top-3 city). Plus monthly city leaderboard.

#### 12. Failure-Learning Loop
Every non-confirmation is classified (wrong channel/time/fatigue) → planner self-adjusts future outreach. Protocol stats are aggregated by channel, time-of-day, blood type, and role. Channels with <25% success over 20 attempts are deprioritized.

#### 13. Agentic Telegram Bot
Every message (command OR natural language) runs through a **Bedrock tool-calling loop with memory**:
- 10+ tools: profile, eligibility, history, availability, badges, leaderboard, impact story, bridge info, medical hold, next donation date
- Photo → **Amazon Textract** OCR for blood card onboarding
- DPDP consent gate on `/start`
- Auto-detected language for all replies

---

### 🌍 Pillar D — Scale & Responsible AI

#### 14. Amazon Bedrock LLMs
Three-tier cost-optimized model strategy:

| Tier | Model | Used By |
|------|-------|---------|
| Fast | Claude Haiku 4.5 | Telegram replies, outreach messages |
| Reasoning | Claude Haiku 4.5 | Planner, conflict resolver, forecast, failure analysis |
| Quality | Claude Sonnet 4.6 | Impact story generation |

#### 15. DPDP 2023 Compliance
- Consent gate before any bot interaction
- Row-Level Security on sensitive tables
- `donors_public` view hides phone/lat-lng/churn
- Dedicated JWT secret (not Supabase key)
- No clinical data over Telegram
- Right-to-erasure support

#### 16. Multi-Language Support
10 Indian languages supported across Telegram bot, voice calls (Sarvam AI TTS), and OCR (Tesseract language packs for Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi).

#### 17. AWS Deployment
Docker + nginx HTTPS reverse proxy, S3 + CloudFront for frontend, hardened `/health` endpoint with latency checks for all services.

---

## 🏗 Architecture

```
        ┌────────────── USERS ──────────────┐
        │ Telegram Bot       Staff Dashboard │
        │ (donors, agentic)  (React + Vite)  │
        └─────────┬───────────────┬──────────┘
                  │ webhook        │ REST + WebSocket
        ┌─────────▼───────────────▼──────────┐
        │      FastAPI Backend (async)        │
        │  ┌──────────────────────────────┐   │
        │  │ LangGraph 14-Node Pipeline    │   │
        │  │ + APScheduler (monitor/cron)  │   │
        │  └──────────────────────────────┘   │
        │  ML: XGBoost · SVD · scipy          │
        └──┬─────────┬──────────┬─────────┬───┘
           │         │          │         │
       Supabase   Neo4j      Bedrock    Bolna/
       (Postgres) (graph)    (LLMs)     Telegram/ntfy
```

### End-to-End Flow

```
 1. REQUEST   Staff (Telegram/dashboard): "B+ needed, Patient P-101, Hyderabad"
 2. INTAKE    Fetch patient + context, create request, init AgentState
 3. ELIGIBLE  Filter donors: 56-day gap, medical hold, active, consent
 4. SCORE     Parallel: urgency (XGBoost) + compatibility (ABO+Rh)
 5. MATCH     Geo radius-tier + weighted score → top 8 donors + backup pool
 6. CONFLICT  If 2 patients share donors → Hungarian optimal assignment
 7. PLAN      Per donor: best channel + language + tone (learned from history)
 8. OUTREACH  Parallel Telegram messages in each donor's language (Bedrock)
 9. MONITOR   Every 5 min: stale → voice; declined → repair (next backup)
10. CONFIRM   Donor replies "yes" → chain node turns GREEN on dashboard
11. OUTCOME   Update stats, award badges, schedule 2-hr impact story
12. LEARN     Classify any failures → planner self-improves next time
```

---

## ⚙️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **Python 3.11** | Core language |
| **FastAPI** | Async REST API framework |
| **LangGraph 0.2** | Multi-agent stateful graph orchestration |
| **LangChain** | LLM abstraction layer |
| **APScheduler** | Cron jobs (monitor, forecast, churn batch) |
| **Pydantic** | Data validation & settings management |
| **Uvicorn** | ASGI server |

### AI & ML
| Technology | Purpose |
|-----------|---------|
| **Amazon Bedrock** | Claude Haiku 4.5 + Sonnet 4.6 LLMs |
| **XGBoost** | Churn prediction + urgency scoring |
| **scikit-learn SVD** | Personalized donor challenge recommender |
| **scipy Hungarian** | Multi-patient optimal assignment |
| **Amazon Textract** | Blood card OCR |
| **Amazon Comprehend** | Language detection |
| **Bolna.ai** | AI voice calls (Sarvam AI Indian voices) |

### Databases
| Technology | Purpose |
|-----------|---------|
| **Supabase (PostgreSQL)** | Primary data store with RLS |
| **Neo4j Aura** | Graph database for chain state + visualization |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tooling |
| **react-force-graph-2d** | Live chain visualization |
| **Framer Motion** | Animations |
| **pnpm** | Package manager |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **nginx** | HTTPS reverse proxy |
| **AWS EC2** | Backend hosting |
| **AWS S3 + CloudFront** | Frontend CDN |
| **ntfy.sh** | Push notifications for staff alerts |

---

## 📂 Project Structure

```
AI4FullStack/
├── BloodBridge_AI_Backend/          # FastAPI backend
│   ├── agents/                      # 14 LangGraph agent nodes
│   │   ├── graph.py                 #   Main StateGraph definition
│   │   ├── intake.py                #   Request parser agent
│   │   ├── eligibility.py           #   WHO/NBTC filter agent
│   │   ├── matching.py              #   Compatibility scoring
│   │   ├── neo4j_match.py           #   Graph-based matching + chain build
│   │   ├── conflict.py              #   Multi-patient conflict resolver
│   │   ├── planner.py               #   Outreach strategy planner
│   │   ├── outreach.py              #   Parallel message dispatcher
│   │   ├── monitor.py               #   Chain health monitor (self-loop)
│   │   ├── repair.py                #   Chain auto-repair agent
│   │   ├── voice.py                 #   Voice call escalation
│   │   ├── gamification.py          #   Badge + leaderboard agent
│   │   ├── outcome.py               #   Request closer + stats updater
│   │   ├── demand_forecast_agent.py #   5-node demand prediction pipeline
│   │   └── proactive_scheduler.py   #   Pre-emptive warm outreach
│   ├── api/                         # REST API routes
│   │   ├── emergency.py             #   Emergency request endpoints
│   │   ├── donors.py                #   Donor CRUD + locations + health
│   │   ├── patients.py              #   Patient CRUD + locations
│   │   ├── admin.py                 #   Admin dashboard APIs
│   │   ├── blood_banks.py           #   Blood bank lookup
│   │   ├── auth.py                  #   JWT authentication
│   │   ├── webhooks.py              #   Telegram + Bolna webhooks
│   │   ├── websocket.py             #   Live chain updates (WS)
│   │   └── lora.py                  #   LoRa offline bridge (concept)
│   ├── core/                        # Shared infrastructure
│   │   ├── config.py                #   Pydantic settings
│   │   ├── database.py              #   Supabase client
│   │   ├── neo4j_client.py          #   Neo4j driver
│   │   ├── llm_provider.py          #   3-tier Bedrock LLM adapter
│   │   ├── security.py              #   JWT + HMAC + auth middleware
│   │   ├── ws_manager.py            #   WebSocket connection manager
│   │   ├── limiter.py               #   Rate limiting (slowapi)
│   │   └── time_utils.py            #   IST timezone helpers
│   ├── services/                    # Business logic services
│   │   ├── matching_engine.py       #   Geo radius-tier + weighted scoring
│   │   ├── assignment_optimizer.py  #   Hungarian algorithm optimizer
│   │   ├── telegram_bot.py          #   Agentic Telegram bot (10+ tools)
│   │   ├── donor_memory.py          #   Failure-learning loop
│   │   ├── gamification_service.py  #   Badge rules + leaderboard
│   │   ├── impact_story.py          #   AI impact story generator
│   │   ├── voice_service.py         #   Bolna.ai voice call integration
│   │   ├── sms_service.py           #   SMS fallback service
│   │   ├── consent_service.py       #   DPDP consent management
│   │   ├── ocr_service.py           #   Blood card OCR (Textract)
│   │   ├── geo_service.py           #   Geohash + distance calculations
│   │   ├── language_service.py      #   Language detection
│   │   ├── alerts.py                #   ntfy.sh push alerts
│   │   ├── blood_bank_scraper.py    #   e-RaktKosh data fetcher
│   │   ├── churn_batch.py           #   Batch churn scoring cron
│   │   ├── transfusion_calendar.py  #   Auto-schedule generation
│   │   └── lora_bridge.py           #   LoRa offline concept
│   ├── ml/                          # Machine learning models
│   │   ├── train_churn.py           #   XGBoost churn trainer
│   │   ├── train_urgency.py         #   XGBoost urgency trainer
│   │   ├── churn_predictor.py       #   Churn inference
│   │   ├── urgency_scorer.py        #   Urgency inference
│   │   ├── antigen_scorer.py        #   8-antigen compatibility scorer
│   │   ├── eligibility_filter.py    #   Donation eligibility rules
│   │   ├── challenge_recommender.py #   SVD-based challenge suggestions
│   │   └── models/                  #   Saved model artifacts (.joblib)
│   ├── scheduler/                   # APScheduler cron jobs
│   ├── data/                        # Seed data & migration scripts
│   ├── tests/                       # Test suites
│   ├── main.py                      # FastAPI app entry point
│   ├── Dockerfile                   # Production container
│   ├── requirements.txt             # Python dependencies
│   └── SECURITY.md                  # RLS & JWT documentation
│
├── BloodBridge_AI_frontend/         # React + Vite + TypeScript frontend
│   ├── lib/                         #   Shared libraries & API client
│   ├── artifacts/                   #   Built app artifacts
│   ├── scripts/                     #   Build & utility scripts
│   ├── package.json                 #   pnpm workspace root
│   └── tsconfig.json                #   TypeScript configuration
│
├── deploy/                          # Deployment configs
│   ├── setup-ec2.sh                 #   EC2 instance bootstrap script
│   ├── deploy-app.sh                #   Application deployment script
│   ├── nginx-production.conf        #   nginx HTTPS config
│   ├── nginx-http-temp.conf         #   nginx HTTP-only (pre-SSL)
│   ├── fix-webhook.sh               #   Telegram webhook repair
│   └── .env.production.template     #   Production env template
│
├── FEATURES_DEEP_DIVE.md            # Detailed feature documentation
├── PRESENTATION.md                  # Slide deck script
├── IMPLEMENTATION_PLAN.md           # Code-traced action plan
├── DEMO_GUIDE.md                    # Live demo walkthrough
├── TEST_PLAN.md                     # Comprehensive test plan
└── AWS_COMPLETE_DEPLOYMENT_GUIDE.md # Full AWS deployment guide
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **pnpm**
- **Docker** (optional, for containerized deployment)
- **ngrok** (for local Telegram webhook testing)

### External Service Accounts

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Supabase](https://supabase.com) | PostgreSQL database | ✅ Yes |
| [Neo4j Aura](https://neo4j.com/cloud/aura-free/) | Graph database | ✅ Yes |
| [AWS Bedrock](https://aws.amazon.com/bedrock/) | Claude LLMs | Pay-per-use |
| [Telegram Bot API](https://core.telegram.org/bots) | Donor chat interface | ✅ Free |
| [Bolna.ai](https://platform.bolna.ai) | AI voice calls (optional) | Free trial |
| [ntfy.sh](https://ntfy.sh) | Staff push alerts | ✅ Free |

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/AI4FullStack.git
cd AI4FullStack/BloodBridge_AI_Backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section)

# 5. Set up Telegram webhook (requires ngrok)
ngrok http 8000
# Copy the HTTPS URL, then:
python setup_webhook.py

# 6. Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd BloodBridge_AI_frontend

# Install dependencies
pnpm install

# Start dev server
pnpm run dev
```

The dashboard will be available at `http://localhost:5173`.

### Docker Setup

```bash
cd BloodBridge_AI_Backend

# Build the image
docker build -t bloodbridge-ai .

# Run the container
docker run -d \
  --name bloodbridge \
  --env-file .env \
  -p 8000:8000 \
  bloodbridge-ai
```

---

## 🔐 Environment Variables

Create a `.env` file in `BloodBridge_AI_Backend/` based on `.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon public key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key |
| `NEO4J_URI` | ✅ | Neo4j Aura connection URI |
| `NEO4J_USERNAME` | ✅ | Neo4j username |
| `NEO4J_PASSWORD` | ✅ | Neo4j password |
| `AWS_REGION` | ✅ | AWS region (default: `ap-south-1`) |
| `AWS_ACCESS_KEY_ID` | ✅ | AWS access key for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | ✅ | AWS secret key for Bedrock |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token from @BotFather |
| `TELEGRAM_WEBHOOK_URL` | ✅ | Public HTTPS URL for webhook |
| `TELEGRAM_WEBHOOK_SECRET` | ✅ | 32-char random string |
| `BOLNA_API_KEY` | ❌ | Bolna.ai API key (voice calls) |
| `BOLNA_AGENT_ID` | ❌ | Bolna.ai agent ID |
| `NTFY_TOPIC` | ❌ | ntfy.sh topic for staff alerts |
| `DEMO_MOCK_MODE` | ❌ | `true` for offline demos (simulates voice, Neo4j fallback) |
| `THREE_PHONE_DEMO_MODE` | ❌ | `true` to restrict to 3 real phones |
| `APP_ENV` | ❌ | `development` or `production` |
| `LOG_LEVEL` | ❌ | Logging level (default: `INFO`) |

---

## 📡 API Reference

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health with per-service latency |

### Emergency Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/emergency/request` | Trigger full 14-node agent pipeline |
| `GET` | `/api/emergency/requests` | List all emergency requests |

### Donors
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/donors` | List all donors (paginated) |
| `GET` | `/api/donors/{id}` | Get donor profile |
| `POST` | `/api/donors/{id}/health-status` | Update donor health/availability |
| `GET/POST/DELETE/PATCH` | `/api/donors/{id}/locations` | Donor location CRUD |
| `POST` | `/api/donors/{id}/voice` | Trigger voice call |
| `POST` | `/api/donors/{id}/outreach` | Trigger outreach message |
| `GET` | `/api/donors/graph/data` | Live chain graph data for visualization |

### Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/patients` | List all patients |
| `GET` | `/api/patients/{id}` | Get patient profile |
| `GET/POST/DELETE/PATCH` | `/api/patients/{id}/locations` | Patient location CRUD (max 5) |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/optimize-assignments` | Hungarian global optimizer |
| `POST` | `/api/admin/forecast/run` | Trigger demand forecast |
| `POST` | `/api/admin/retrain` | Retrain ML models |
| `GET/POST/DELETE` | `/api/admin/staff` | Staff member management |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhook/telegram` | Telegram bot webhook |
| `POST` | `/webhook/bolna` | Bolna.ai voice call webhook |

### WebSocket
| Protocol | Endpoint | Description |
|----------|----------|-------------|
| `WS` | `/ws` | Live chain status updates |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Staff JWT login |
| `POST` | `/api/auth/verify` | Verify JWT token |

---

## 🤖 AI & ML Models

### LLM Tiers (Amazon Bedrock)

| Tier | Model ID | Use Case |
|------|----------|----------|
| Fast | `us.anthropic.claude-haiku-4.5-20251001-v1:0` | Telegram replies, outreach message generation |
| Reasoning | `us.anthropic.claude-haiku-4.5-20251001-v1:0` | Planner, conflict resolver, failure analysis |
| Quality | `us.anthropic.claude-sonnet-4-6` | Impact story generation |

### ML Models

| Model | Algorithm | Training Data | Purpose |
|-------|-----------|---------------|---------|
| Churn Predictor | XGBoost | Blood Warriors donor dataset (real labels) | Predict donor drop-off risk |
| Urgency Scorer | XGBoost | Patient transfusion history | Score patient urgency 0–10 |
| Challenge Recommender | SVD (scikit-learn) | Donor interaction matrix | Personalized re-engagement |
| Antigen Scorer | Rule-based | Clinical ISBT standards | 8-antigen compatibility (Phase 2) |

### Retraining
- **Churn model**: Monthly cron at 8 PM IST via `churn_batch.py`
- **Manual retrain**: `POST /api/admin/retrain`
- **Atomic save**: Model only replaced if validation AUC > 0.70

---

## 🔒 Data Privacy & Security

BloodBridge AI is built with **India's Digital Personal Data Protection (DPDP) Act 2023** compliance:

| Measure | Implementation |
|---------|---------------|
| **Consent Gate** | Mandatory `/start` consent before any bot tool access |
| **Row-Level Security** | RLS on `consent_records`, `donor_memory`, `donor_verifications`, `blood_chains` |
| **Data Minimization** | `donors_public` view hides phone, lat/lng, churn_score |
| **Dedicated JWT** | Separate `JWT_SECRET` (not Supabase key) with 24-hr expiry |
| **Audit Trail** | All agent decisions logged to `agent_traces` |
| **No Clinical Leaks** | Patient medical details never sent over Telegram |
| **Right to Erasure** | Supported via consent service |

### JWT Rotation
```bash
# Generate new secret
openssl rand -hex 32

# Update .env, restart container — all tokens immediately invalidated
docker restart bloodbridge
```

---

## ☁️ Deployment

### Production Architecture

```
Internet → CloudFront (CDN) → S3 (React frontend)
                                    ↓ API calls
Internet → nginx (HTTPS) → Docker (FastAPI backend) → Supabase / Neo4j / Bedrock
```

### EC2 Deployment

```bash
# 1. Bootstrap EC2 instance (Ubuntu 22.04, t3.medium recommended)
chmod +x deploy/setup-ec2.sh
./deploy/setup-ec2.sh

# 2. Configure production environment
cp deploy/.env.production.template .env.production
# Edit with production values

# 3. Deploy the application
chmod +x deploy/deploy-app.sh
./deploy/deploy-app.sh
```

### Production Safety Checks
The app enforces these checks on startup when `APP_ENV=production`:
- ❌ `DEMO_MOCK_MODE=true` → Fatal error (prevents mock data in production)
- ⚠️ `ALLOWED_ORIGINS=*` → Warning logged
- ❌ Weak Neo4j password → Fatal error

See [AWS_COMPLETE_DEPLOYMENT_GUIDE.md](AWS_COMPLETE_DEPLOYMENT_GUIDE.md) for the full walkthrough.

---

## 🧪 Testing

### Run Tests

```bash
cd BloodBridge_AI_Backend

# Run all tests
pytest

# Run specific scenario tests
python test_scenario_a.py   # Smart Matching + Antigen Safety
python test_scenario_b.py   # Autonomous Coordination + Self-Heal

# Run all 5 end-to-end scenarios
python run_scenarios_ae.py

# Compile check (verify no syntax errors)
python -m compileall agents services
```

### Test Scenarios

| Scenario | Tests | Pass Criteria |
|----------|-------|---------------|
| **A** — Smart Matching | Antigen safety, geo ranking, weighted scoring | Non-empty ranked list, antigen visibly affects order |
| **B** — Coordination | Chain repair, voice escalation, WebSocket updates | Chain never silently dies |
| **C** — Telegram Bot | OCR registration, agentic tool-calling, language detection | Bot responds via Bedrock (not template fallback) |
| **D** — Engagement | Churn tiers, impact stories, demand forecast | Personalized story (not fallback) |
| **E** — Conflict | 2 concurrent CRITICAL requests, Hungarian optimizer | No donor double-assigned |

See [TEST_PLAN.md](TEST_PLAN.md) and [DEMO_GUIDE.md](DEMO_GUIDE.md) for full details.

---

## 📖 Demo Guide

### Quick Demo (DEMO_MOCK_MODE=true)

1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `pnpm run dev`
3. Open Staff Dashboard → trigger emergency request
4. Watch the 14-node pipeline execute in real-time
5. See chain visualization update live via WebSocket

### Three-Phone Demo

For a live demo with real Telegram bots:
1. Set `THREE_PHONE_DEMO_MODE=true`
2. Seed 3 real phone numbers: `python -m data.seed_three_phones`
3. Follow [THREE_PHONE_DEMO_TEST_PLAN.md](THREE_PHONE_DEMO_TEST_PLAN.md)

---

## 🗺 Roadmap

| Phase | Status | Items |
|-------|--------|-------|
| **Current** | ✅ | ABO+Rh + geo + engagement matching, 14-node pipeline, self-healing chains, churn ML, gamification, Telegram bot, demand forecasting, DPDP compliance |
| **Phase 2** (Clinical) | ⏳ | 8-antigen phenotyping (Kell/Duffy/Kidd/Rh-E/C/MNS) for DHTR prevention — schema + scorer ready, activates with phenotype data |
| **Phase 3** (Scale) | 📋 | e-RaktKosh live API integration, LoRa offline hardware bridge, multi-region deployment, WhatsApp Business API channel |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

> ⚠️ **Important:** Always run `python -m compileall agents services` before committing to verify no syntax errors.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### *"Every drop, coordinated by AI — so no Thalassemia child waits."*

**Built with ❤️ by Team Inqilab**

DNR College of Engineering & Technology

</div>
]]>
