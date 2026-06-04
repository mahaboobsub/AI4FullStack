\# BloodBridge AI — Backend Development Master Document  
\#\# FINAL EDITION · PRD v6+v7 Consolidated · 41 Prompts · Phase-by-Phase  
\#\#\# Team Inqilab · Blend360 Hackathon · AI for Blood Donation

\---

\#\# CONTEXT: THE PROBLEM WE ARE SOLVING

Blood Warriors is a foundation connecting voluntary blood donors with Thalassemia patients  
across India. 1,00,000+ patients need 500–700 transfusions in a lifetime.

The critical clinical truth: after 10+ transfusions, patients develop allo-antibodies against  
minor blood antigens (Kell, Duffy, Kidd, Rh subtypes). Sending "ABO-compatible" blood that  
ignores these antibodies causes Delayed Hemolytic Transfusion Reactions — potentially fatal.

Four operational failures we are fixing:  
1\. Matching    — Manual, ABO-only, ignores antibody history, no urgency scoring  
2\. Coordination — 8-person donor chains collapse silently, no auto-repair, 80% staff on calls  
3\. Engagement  — 60% donors inactive, generic reminders 15% response, no feedback loop  
4\. Scale       — 100,000 patients, 36 states, 22+ languages, patchy internet

Our AI solution:  
\* LangGraph StateGraph with 9 autonomous agents handling the full pipeline  
\* 8-antigen ISBT-weighted compatibility scorer (not just blood type)  
\* Neo4j graph database storing COMPATIBLE\_WITH edges for \<100ms matching  
\* XGBoost for urgency scoring \+ churn prediction  
\* Groq \+ Gemini for multilingual outreach \+ conflict resolution  
\* Telegram Bot as zero-install interface (500M+ users)  
\* AI voice calls via Vapi.ai for non-responsive donors (Gemini-powered assistant, Indian language voices)  
\* SMS fallback via Twilio (DLT-compliant) for donors without Telegram  
\* ProactiveSchedulerAgent — warm outreach 5–7 days BEFORE transfusion is due  
\* LoRa offline bridge — 8-byte packet protocol for zero-connectivity rural areas  
\* DPDP 2023 compliant consent management (explicit opt-in \+ right to erasure)  
\* ₹0 total deployment cost

\---

\#\# TECH STACK

Backend:      FastAPI 0.115 \+ Uvicorn \+ Python 3.11  
Agents:       LangGraph 0.2 \+ LangChain 0.3  
LLMs:         Groq (Llama-3.3-70B) · Gemini 1.5 Flash  
ML:           XGBoost 2.1 · scikit-learn SVD  
NLP:          langdetect · Tesseract OCR (pytesseract) — 10 Indian language packs  
Voice:        Vapi.ai (replaces Twilio Voice \+ gTTS — handles TTS \+ call \+ NLU natively)  
SMS:          Twilio Messages API (DLT-registered templates) — Twilio kept for SMS only  
Messaging:    python-telegram-bot 21.x  
Database:     Supabase PostgreSQL (supabase-py) · Neo4j Aura (neo4j driver)  
Storage:      Supabase Storage (OCR source images \+ audit trail assets)  
Scheduler:    APScheduler 3.x  
Alerts:       ntfy.sh (httpx)  
Scraping:     httpx \+ BeautifulSoup4 (e-RaktKosh)  
Security:     slowapi (rate limiting) · Vapi webhook verification · hmac webhook verify  
Seed Data:    Faker  
Deployment:   Render.com free tier  
Monitoring:   UptimeRobot

\---

\#\# DEVELOPMENT ORDER — CRITICAL PATH

PHASE 1 — Foundation (Day 1 Morning)  
  ├── P1-A: Project setup \+ requirements \+ folder structure \+ security.py  
  ├── P1-B: Supabase schema (11 tables \+ RLS)  
  ├── P1-C: Neo4j schema \+ constraints \+ indexes  
  └── P1-D: Synthetic data generation \+ seed script \+ ML model training

PHASE 2 — Matching Engine (Day 1 Afternoon)  
  ├── P2-A: 8-antigen ISBT compatibility scorer  
  ├── P2-B: Donor eligibility filter  
  ├── P2-C: XGBoost urgency scorer (train \+ save)  
  └── P2-D: Neo4j COMPATIBLE\_WITH edge builder \+ Cypher matcher

PHASE 3 — LangGraph Agent Pipeline (Day 1 Evening → Day 2 Morning)  
  ├── P3-A: AgentState TypedDict \+ LangGraph graph skeleton  
  ├── P3-B: IntakeAgent \+ EligibilityFilterAgent  
  ├── P3-C: AntigenScoringAgent \+ UrgencyScoringAgent (parallel)  
  ├── P3-D: Neo4jMatchingAgent \+ ConflictResolverAgent (Gemini)  
  ├── P3-E: PlannerAgent (Gemini channel strategy)  
  ├── P3-F: OutreachAgent (Groq \+ langdetect · parallel ×8 · 10 langs · consent · memory context)  
  ├── P3-G: ChainMonitorAgent (APScheduler · 5-min loop)  
  ├── P3-H: ChainRepairAgent \+ InventoryAgent (e-RaktKosh fallback)  
  ├── P3-I: OutcomeAgent \+ GamificationAgent  
  └── P3-J: ProactiveSchedulerAgent \+ TransfusionCalendarService  ← NEW

PHASE 4 — Communication Layer (Day 2 Afternoon)  
  ├── P4-A: Telegram Bot (8 commands \+ security \+ dedup \+ consent)  
  ├── P4-B: Tesseract OCR blood card extractor (10 language packs)  
  ├── P4-C: Donor memory system (Supabase donor\_memory table)  
  ├── P4-D: AI Voice Agent (Vapi.ai — replaces Twilio Voice \+ gTTS)  
  └── P4-E: SMS Fallback Service (Twilio SMS \+ DLT compliance)  ← NEW

PHASE 5 — Engagement & Continuity (Day 2 Evening)  
  ├── P5-A: XGBoost churn predictor (train \+ save \+ daily batch)  
  ├── P5-B: Gamification engine (6 badges \+ city leaderboard)  
  ├── P5-C: SVD collaborative challenge recommender  
  ├── P5-D: Gemini impact story generator (multilingual)  
  └── P5-E: Consent Management Service \+ DPDP 2023 compliance  ← NEW

PHASE 6 — API \+ Real-time (Day 3 Morning)  
  ├── P6-A: FastAPI REST endpoints (all routes \+ eligibility \+ schedule)  
  ├── P6-B: WebSocket endpoint \+ live chain broadcasting  
  ├── P6-C: ntfy.sh staff push alerts  
  └── P6-D: Bulk Donor Import API  ← NEW

PHASE 7 — External Integration (Day 3 Afternoon)  
  └── P7-A: e-RaktKosh scraper \+ 15-min Supabase cache

PHASE 8 — Deployment \+ Security (Day 3 Evening)  
  ├── P8-A: Render.com deployment config  
  ├── P8-B: E2E integration test \+ demo script  
  └── P8-C: Security hardening (webhook verification \+ rate limiting)  ← NEW

PHASE 9 — LoRa Offline Bridge (Day 3 Evening if time permits)  
  └── P9-A: LoRa offline bridge — 8-byte packet protocol \+ gateway \+ simulator  ← NEW

\---

\#\# FOLDER STRUCTURE (Build To This)

\`\`\`  
bloodbridge-backend/  
├── main.py  
├── requirements.txt  
├── .env.example  
├── render.yaml  
│  
├── core/  
│   ├── config.py  
│   ├── database.py  
│   ├── neo4j\_client.py  
│   ├── ws\_manager.py  
│   └── security.py  
│  
├── models/  
│   ├── schemas.py  
│   └── state.py  
│  
├── agents/  
│   ├── graph.py  
│   ├── intake.py  
│   ├── eligibility.py  
│   ├── matching.py  
│   ├── neo4j\_match.py  
│   ├── conflict.py  
│   ├── planner.py  
│   ├── outreach.py  
│   ├── monitor.py  
│   ├── repair.py  
│   ├── voice.py  
│   ├── gamification.py  
│   ├── outcome.py  
│   └── proactive\_scheduler.py  
│  
├── ml/  
│   ├── antigen\_scorer.py  
│   ├── urgency\_scorer.py  
│   ├── churn\_predictor.py  
│   ├── challenge\_recommender.py  
│   ├── train\_urgency.py  
│   ├── train\_churn.py  
│   └── models/  
│       ├── urgency\_model.joblib  
│       ├── churn\_model.joblib  
│       └── svd\_challenges.joblib  
│  
├── services/  
│   ├── telegram\_bot.py  
│   ├── ocr\_service.py  
│   ├── donor\_memory.py  
│   ├── voice\_service.py  
│   ├── sms\_service.py  
│   ├── consent\_service.py  
│   ├── impact\_story.py  
│   ├── blood\_bank\_scraper.py  
│   ├── lora\_bridge.py  
│   ├── transfusion\_calendar.py  
│   └── alerts.py  
│  
├── api/  
│   ├── emergency.py  
│   ├── donors.py  
│   ├── patients.py  
│   ├── blood\_banks.py  
│   ├── admin.py  
│   ├── websocket.py  
│   ├── lora.py  
│   └── webhooks.py  
│  
├── data/  
│   ├── seed\_supabase.py  
│   ├── seed\_neo4j.py  
│   └── generate\_synthetic.py  
│  
├── scheduler/  
│   ├── jobs.py  
│   └── cron.py  
│  
└── tools/  
    └── lora\_simulator.py  
\`\`\`

\---

\#\# PHASE 1 — FOUNDATION

\---

\#\#\# PROMPT P1-A — Project Setup \+ Requirements \+ Folder Structure

\*\*What this builds:\*\* The complete project skeleton — requirements.txt with all pinned versions,  
core config/database singletons, security helpers, and all empty module files so imports  
work from day one.  
\*\*Dependencies:\*\* Nothing. Build this first.  
\*\*Files created:\*\* requirements.txt, .env.example, main.py, core/config.py, core/database.py,  
               core/neo4j\_client.py, core/security.py, all empty \_\_init\_\_.py files.

\---

You are building BloodBridge AI — a FastAPI backend for blood donor coordination in India.  
Stack: FastAPI, LangGraph, LangChain, Groq, Gemini, XGBoost, scikit-learn, Neo4j, Supabase,  
python-telegram-bot, Twilio (SMS only), Vapi.ai (voice), pytesseract, APScheduler, Faker, httpx, slowapi.

TASK: Create the complete project foundation.

\*\*1. CREATE requirements.txt with these exact pinned versions:\*\*  
\`\`\`  
fastapi==0.115.0  
uvicorn\[standard\]==0.30.6  
python-dotenv==1.0.1  
pydantic==2.8.2  
pydantic-settings==2.4.0  
supabase==2.7.4  
neo4j==5.23.1  
langgraph==0.2.28  
langchain==0.3.1  
langchain-groq==0.2.0  
langchain-google-genai==2.0.0  
google-generativeai==0.8.2  
groq==0.11.0  
xgboost==2.1.1  
scikit-learn==1.5.2  
joblib==1.4.2  
langdetect==1.0.9  
python-telegram-bot==21.6  
twilio==9.2.3  
pytesseract==0.3.13  
Pillow==10.4.0  
httpx==0.27.2  
beautifulsoup4==4.12.3  
APScheduler==3.10.4  
faker==30.3.0  
numpy==1.26.4  
pandas==2.2.3  
slowapi==0.1.9  
pytz==2024.2  
\`\`\`  
NOTE: gTTS removed — Vapi.ai handles TTS natively. asyncio-mqtt removed — LoRa uses HTTP POST ingest.

\*\*2. CREATE .env.example with ALL required environment variables:\*\*  
\`\`\`  
\# Supabase  
SUPABASE\_URL=  
SUPABASE\_KEY=  
SUPABASE\_SERVICE\_KEY=

\# Neo4j Aura  
NEO4J\_URI=  
NEO4J\_USERNAME=  
NEO4J\_PASSWORD=

\# AI APIs  
GROQ\_API\_KEY=  
GEMINI\_API\_KEY=

\# Telegram  
TELEGRAM\_BOT\_TOKEN=  
TELEGRAM\_WEBHOOK\_URL=  
TELEGRAM\_WEBHOOK\_SECRET=         \# random 32-char string for webhook verification

\# Vapi.ai (Voice calls — replaces Twilio Voice)  
VAPI\_API\_KEY=                    \# from Vapi dashboard  
VAPI\_PHONE\_NUMBER\_ID=            \# from Vapi dashboard phone number settings  
VAPI\_WEBHOOK\_SECRET=             \# random 32-char string for Vapi webhook verification

\# Twilio (SMS only — DLT-registered)  
TWILIO\_ACCOUNT\_SID=  
TWILIO\_AUTH\_TOKEN=  
TWILIO\_DLT\_SENDER\_ID=            \# India DLT-registered sender ID for SMS  
TWILIO\_DLT\_TEMPLATE\_ID\_HI=       \# Hindi SMS template ID registered with DLT  
TWILIO\_DLT\_TEMPLATE\_ID\_EN=       \# English SMS template ID

\# ntfy.sh  
NTFY\_TOPIC=bloodbridge-alerts

\# App settings  
APP\_ENV=development  
APP\_HOST=0.0.0.0  
APP\_PORT=8000  
APP\_BASE\_URL=http://localhost:8000  
LOG\_LEVEL=INFO  
\`\`\`

\*\*3. CREATE core/config.py\*\* using pydantic-settings:  
   \- Settings class reading all env vars with types (str, int, bool)  
   \- get\_settings() function cached with @lru\_cache  
   \- NEVER hardcode secrets

\*\*4. CREATE core/database.py:\*\*  
   \- Supabase client singleton: get\_supabase() and get\_supabase\_admin() (using SERVICE\_KEY)  
   \- get\_supabase\_admin() bypasses RLS — used for seeding and bulk import

\*\*5. CREATE core/neo4j\_client.py:\*\*  
   \- Neo4j AsyncDriver singleton  
   \- get\_neo4j() async context manager  
   \- health\_check() async function (runs RETURN 1 AS ok)  
   \- close() function for shutdown

\*\*6. CREATE core/security.py:\*\*  
\`\`\`python  
verify\_telegram\_webhook(request, secret\_token) \-\> bool  
  \# Uses hmac.compare\_digest to check X-Telegram-Bot-Api-Secret-Token header  
  \# Returns True in dev if secret\_token not configured (safe default)

verify\_vapi\_webhook(request, secret) \-\> bool  
  \# Uses hmac.compare\_digest to check X-Vapi-Signature header  
  \# Returns True in development mode (APP\_ENV=development)

generate\_idempotency\_key(patient\_id, blood\_type, city) \-\> str  
  \# Returns SHA256 hash first 32 chars — used for duplicate emergency prevention  
  \# Same patient+blood\_type+city within 30 minutes gets the same key

is\_twilio\_ip(ip: str) \-\> bool  
  \# Checks against Twilio IP CIDR ranges (list of 10 known ranges) — used for SMS webhooks

def hash\_ip(ip: str) \-\> str  
  \# SHA256 of IP address, first 16 chars — for DPDP-compliant audit logging

async get\_current\_staff(request: Request) \-\> dict  
  \# FastAPI Depends() for staff-authenticated routes  
  \# Checks X-Staff-Token header against staff table

async get\_current\_staff\_admin(staff=Depends(get\_current\_staff)) \-\> dict  
  \# Admin-only dependency (role must be 'Admin')  
\`\`\`

\*\*7. CREATE main.py:\*\*  
   \- FastAPI app title "BloodBridge AI" version "1.0.0"  
   \- CORS middleware allow\_origins=\["\*"\] for hackathon  
   \- slowapi Limiter with get\_remote\_address  
   \- Include all routers: emergency, donors, patients, blood\_banks, admin, websocket, lora, webhooks  
   \- startup: start APScheduler, start Telegram bot polling (dev) or set webhook (prod)  
   \- shutdown: stop scheduler, close Neo4j driver  
   \- GET /health → {status: "ok", services: {fastapi, neo4j, supabase, telegram, vapi}} with latency checks

\*\*8. CREATE all empty \_\_init\_\_.py files and stub .py files with module docstrings.\*\*

IMPORTANT RULES:  
\- async/await throughout  
\- Never print() — use Python logging module  
\- All secrets from settings, never hardcoded

\---

\#\#\# PROMPT P1-B — Supabase Schema (11 Tables \+ RLS)

\*\*What this builds:\*\* Complete PostgreSQL schema — 8 core tables from v6 plus 3 new tables:  
consent\_records (DPDP 2023 compliance), donor\_verifications (antigen audit trail),  
transfusion\_schedule (proactive scheduling).  
\*\*Dependencies:\*\* P1-A  
\*\*Files created:\*\* data/supabase\_schema.sql, data/seed\_supabase.py

\---

You are building the Supabase PostgreSQL schema for BloodBridge AI.  
11 tables total — run this SQL in the Supabase SQL editor.

CREATE data/supabase\_schema.sql:

\*\*━━━ TABLE 1: donors ━━━\*\*  
\`\`\`sql  
CREATE TABLE donors (  
  donor\_id          TEXT PRIMARY KEY DEFAULT 'D-' || floor(random()\*90000+10000)::text,  
  telegram\_chat\_id  TEXT UNIQUE,  
  phone             TEXT,  
  name              TEXT NOT NULL,  
  blood\_type        TEXT NOT NULL CHECK (blood\_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),  
  city              TEXT NOT NULL,  
  ward              TEXT,  
  lat               FLOAT,  
  lng               FLOAT,  
  kell\_negative     BOOLEAN DEFAULT false,  
  duffy\_negative    BOOLEAN DEFAULT false,  
  kidd\_negative     BOOLEAN DEFAULT false,  
  rh\_e\_negative     BOOLEAN DEFAULT false,  
  rh\_c\_negative     BOOLEAN DEFAULT false,  
  mns\_negative      BOOLEAN DEFAULT false,  
  hemoglobin        FLOAT,  
  last\_donation\_date DATE,  
  medical\_hold      BOOLEAN DEFAULT false,  
  donation\_count    INT DEFAULT 0,  
  lives\_saved       INT DEFAULT 0,  
  response\_rate     FLOAT DEFAULT 0.5,  
  preferred\_language TEXT DEFAULT 'Hindi',  
  churn\_score       FLOAT DEFAULT 0.5,  
  churn\_risk        TEXT DEFAULT 'MEDIUM',  
  is\_active         BOOLEAN DEFAULT true,  
  consent\_data\_storage  BOOLEAN DEFAULT false,  
  consent\_outreach      BOOLEAN DEFAULT false,  
  consent\_granted\_at    TIMESTAMPTZ,  
  created\_at        TIMESTAMPTZ DEFAULT NOW(),  
  updated\_at        TIMESTAMPTZ DEFAULT NOW()  
);  
\`\`\`

\*\*━━━ TABLE 2: patients ━━━\*\*  
\`\`\`sql  
CREATE TABLE patients (  
  patient\_id           TEXT PRIMARY KEY,  
  name                 TEXT NOT NULL,  
  age                  INT,  
  blood\_type           TEXT NOT NULL,  
  hospital             TEXT NOT NULL,  
  ward                 TEXT,  
  city                 TEXT NOT NULL,  
  hemoglobin           FLOAT,  
  transfusion\_count    INT DEFAULT 0,  
  next\_transfusion\_due DATE,  
  antibody\_kell        BOOLEAN DEFAULT false,  
  antibody\_duffy       BOOLEAN DEFAULT false,  
  antibody\_kidd        BOOLEAN DEFAULT false,  
  antibody\_rh\_e        BOOLEAN DEFAULT false,  
  antibody\_rh\_c        BOOLEAN DEFAULT false,  
  antibody\_mns         BOOLEAN DEFAULT false,  
  kell\_negative        BOOLEAN DEFAULT false,  
  status               TEXT DEFAULT 'STABLE' CHECK (status IN ('CRITICAL','STABLE','OVERDUE')),  
  is\_active            BOOLEAN DEFAULT true,  
  coordinator\_id       TEXT,  
  created\_at           TIMESTAMPTZ DEFAULT NOW(),  
  updated\_at           TIMESTAMPTZ DEFAULT NOW()  
);  
\`\`\`

\*\*━━━ TABLE 3: emergency\_requests ━━━\*\*  
\`\`\`sql  
CREATE TABLE emergency\_requests (  
  request\_id          TEXT PRIMARY KEY DEFAULT 'REQ-' || floor(random()\*90000+10000)::text,  
  patient\_id          TEXT REFERENCES patients(patient\_id),  
  blood\_type          TEXT NOT NULL,  
  city                TEXT NOT NULL,  
  hospital\_name       TEXT NOT NULL,  
  ward                TEXT,  
  priority            TEXT DEFAULT 'ROUTINE' CHECK (priority IN ('CRITICAL','HIGH','ROUTINE')),  
  urgency\_score       FLOAT,  
  status              TEXT DEFAULT 'IN\_PROGRESS' CHECK (status IN ('IN\_PROGRESS','COMPLETED','ESCALATED','CANCELLED')),  
  triggered\_by        TEXT,  
  agent\_trace\_id      TEXT,  
  idempotency\_key     TEXT UNIQUE,  
  idempotency\_expires\_at TIMESTAMPTZ,  
  request\_mode        TEXT DEFAULT 'emergency' CHECK (request\_mode IN ('emergency','proactive')),  
  created\_at          TIMESTAMPTZ DEFAULT NOW(),  
  completed\_at        TIMESTAMPTZ,  
  notes               TEXT  
);  
\`\`\`

\*\*━━━ TABLE 4: blood\_chains ━━━\*\*  
\`\`\`sql  
CREATE TABLE blood\_chains (  
  chain\_id        SERIAL PRIMARY KEY,  
  request\_id      TEXT REFERENCES emergency\_requests(request\_id) ON DELETE CASCADE,  
  donor\_id        TEXT REFERENCES donors(donor\_id),  
  donor\_name      TEXT,  
  chain\_position  INT NOT NULL,  
  status          TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING','ALERTED','CONFIRMED','DECLINED','VOICE','SMS','COMPLETED')),  
  antigen\_score   FLOAT,  
  alerted\_at      TIMESTAMPTZ,  
  confirmed\_at    TIMESTAMPTZ,  
  declined\_at     TIMESTAMPTZ,  
  response\_method TEXT,  
  notes           TEXT,  
  UNIQUE (request\_id, chain\_position)  
);  
\`\`\`

\*\*━━━ TABLE 5: donor\_memory ━━━\*\*  
\`\`\`sql  
CREATE TABLE donor\_memory (  
  donor\_id            TEXT PRIMARY KEY REFERENCES donors(donor\_id) ON DELETE CASCADE,  
  preferred\_language  TEXT DEFAULT 'Hindi',  
  tone\_profile        TEXT DEFAULT 'warm',  
  emotional\_anchors   TEXT\[\],  
  last\_interaction    TIMESTAMPTZ,  
  total\_interactions  INT DEFAULT 0,  
  badges              TEXT\[\] DEFAULT '{}',  
  streak\_days         INT DEFAULT 0,  
  last\_response\_time\_secs INT,  
  impact\_story        TEXT,  
  last\_story\_date     DATE,  
  notes               TEXT,  
  updated\_at          TIMESTAMPTZ DEFAULT NOW()  
);  
\`\`\`

\*\*━━━ TABLE 6: gamification ━━━\*\*  
\`\`\`sql  
CREATE TABLE gamification (  
  entry\_id      SERIAL PRIMARY KEY,  
  donor\_id      TEXT REFERENCES donors(donor\_id) ON DELETE CASCADE,  
  badge\_name    TEXT NOT NULL,  
  badge\_emoji   TEXT,  
  threshold     INT,  
  awarded\_at    TIMESTAMPTZ DEFAULT NOW(),  
  notified      BOOLEAN DEFAULT false  
);

CREATE TABLE leaderboard\_cache (  
  entry\_id      SERIAL PRIMARY KEY,  
  donor\_id      TEXT REFERENCES donors(donor\_id) ON DELETE CASCADE,  
  city          TEXT NOT NULL,  
  lives\_saved   INT DEFAULT 0,  
  rank          INT,  
  month\_year    TEXT NOT NULL,  
  updated\_at    TIMESTAMPTZ DEFAULT NOW(),  
  UNIQUE (donor\_id, month\_year)  
);  
\`\`\`

\*\*━━━ TABLE 7: agent\_traces ━━━\*\*  
\`\`\`sql  
CREATE TABLE agent\_traces (  
  trace\_id      TEXT PRIMARY KEY DEFAULT 'TRC-' || floor(random()\*90000+10000)::text,  
  request\_id    TEXT REFERENCES emergency\_requests(request\_id),  
  patient\_id    TEXT,  
  started\_at    TIMESTAMPTZ DEFAULT NOW(),  
  completed\_at  TIMESTAMPTZ,  
  outcome       TEXT CHECK (outcome IN ('SUCCESS','ESCALATED','IN\_PROGRESS','FAILED')),  
  total\_ms      INT,  
  node\_count    INT,  
  nodes\_json    JSONB,  
  error\_message TEXT  
);  
\`\`\`

\*\*━━━ TABLE 8: staff ━━━\*\*  
\`\`\`sql  
CREATE TABLE staff (  
  staff\_id          SERIAL PRIMARY KEY,  
  telegram\_username TEXT UNIQUE NOT NULL,  
  telegram\_chat\_id  TEXT UNIQUE,  
  hospital          TEXT NOT NULL,  
  role              TEXT DEFAULT 'Staff' CHECK (role IN ('Admin','Coordinator','Staff')),  
  auth\_token        TEXT UNIQUE,  
  is\_active         BOOLEAN DEFAULT true,  
  added\_at          TIMESTAMPTZ DEFAULT NOW()  
);  
\`\`\`

\*\*━━━ TABLE 9 (NEW): consent\_records ━━━\*\*  
\`\`\`sql  
CREATE TABLE consent\_records (  
  consent\_id        SERIAL PRIMARY KEY,  
  donor\_id          TEXT REFERENCES donors(donor\_id) ON DELETE CASCADE,  
  consent\_type      TEXT NOT NULL CHECK (consent\_type IN (  
                      'data\_storage','outreach\_telegram','outreach\_voice',  
                      'outreach\_sms','data\_sharing\_bloodwarriors','data\_sharing\_hospitals'  
                    )),  
  action            TEXT NOT NULL CHECK (action IN ('granted','revoked')),  
  granted\_at        TIMESTAMPTZ,  
  revoked\_at        TIMESTAMPTZ,  
  channel           TEXT,  
  language          TEXT,  
  consent\_text\_hash TEXT,  
  ip\_hash           TEXT,  
  created\_at        TIMESTAMPTZ DEFAULT NOW()  
);  
CREATE INDEX idx\_consent\_donor\_type ON consent\_records(donor\_id, consent\_type);  
CREATE INDEX idx\_consent\_active ON consent\_records(donor\_id) WHERE action \= 'granted';  
\`\`\`

\*\*━━━ TABLE 10 (NEW): donor\_verifications ━━━\*\*  
\`\`\`sql  
CREATE TABLE donor\_verifications (  
  verification\_id   SERIAL PRIMARY KEY,  
  donor\_id          TEXT REFERENCES donors(donor\_id) ON DELETE CASCADE,  
  antigen\_flag      TEXT NOT NULL,  
  flag\_value        BOOLEAN NOT NULL,  
  verification\_type TEXT NOT NULL CHECK (verification\_type IN (  
                      'self\_reported','ocr\_card','lab\_confirmed','staff\_manual'  
                    )),  
  confidence        FLOAT,  
  source\_document   TEXT,  
  verified\_by       TEXT,  
  verified\_at       TIMESTAMPTZ DEFAULT NOW(),  
  notes             TEXT  
);  
CREATE INDEX idx\_verif\_donor ON donor\_verifications(donor\_id);  
\`\`\`

\*\*━━━ TABLE 11 (NEW): transfusion\_schedule ━━━\*\*  
\`\`\`sql  
CREATE TABLE transfusion\_schedule (  
  schedule\_id         SERIAL PRIMARY KEY,  
  patient\_id          TEXT REFERENCES patients(patient\_id) ON DELETE CASCADE,  
  scheduled\_date      DATE NOT NULL,  
  advance\_days        INT DEFAULT 5,  
  hospital            TEXT NOT NULL,  
  blood\_type          TEXT NOT NULL,  
  status              TEXT DEFAULT 'PENDING' CHECK (status IN (  
                        'PENDING','OUTREACH\_STARTED','DONOR\_CONFIRMED','COMPLETED','MISSED'  
                      )),  
  request\_id          TEXT REFERENCES emergency\_requests(request\_id),  
  outreach\_started\_at TIMESTAMPTZ,  
  created\_by          TEXT,  
  created\_at          TIMESTAMPTZ DEFAULT NOW(),  
  updated\_at          TIMESTAMPTZ DEFAULT NOW()  
);  
CREATE INDEX idx\_schedule\_date ON transfusion\_schedule(scheduled\_date);  
CREATE INDEX idx\_schedule\_status ON transfusion\_schedule(status);  
CREATE INDEX idx\_schedule\_patient ON transfusion\_schedule(patient\_id);  
\`\`\`

\*\*━━━ ALL INDEXES ━━━\*\*  
\`\`\`sql  
CREATE INDEX idx\_donors\_city\_blood ON donors(city, blood\_type);  
CREATE INDEX idx\_donors\_kell ON donors(kell\_negative) WHERE kell\_negative \= true;  
CREATE INDEX idx\_donors\_consent ON donors(consent\_data\_storage, consent\_outreach);  
CREATE INDEX idx\_chains\_request ON blood\_chains(request\_id);  
CREATE INDEX idx\_chains\_status ON blood\_chains(status);  
CREATE INDEX idx\_emergency\_status ON emergency\_requests(status);  
CREATE INDEX idx\_emergency\_idempotency ON emergency\_requests(idempotency\_key) WHERE idempotency\_key IS NOT NULL;  
CREATE INDEX idx\_traces\_request ON agent\_traces(request\_id);  
\`\`\`

\*\*━━━ ROW LEVEL SECURITY ━━━\*\*  
\`\`\`sql  
ALTER TABLE donors ENABLE ROW LEVEL SECURITY;  
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;  
ALTER TABLE emergency\_requests ENABLE ROW LEVEL SECURITY;  
ALTER TABLE consent\_records ENABLE ROW LEVEL SECURITY;  
ALTER TABLE donor\_verifications ENABLE ROW LEVEL SECURITY;  
\`\`\`

\*\*━━━ TRIGGERS ━━━\*\*  
\`\`\`sql  
CREATE OR REPLACE FUNCTION update\_updated\_at()  
RETURNS TRIGGER AS $$ BEGIN NEW.updated\_at \= NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER donors\_updated\_at BEFORE UPDATE ON donors FOR EACH ROW EXECUTE FUNCTION update\_updated\_at();  
CREATE TRIGGER patients\_updated\_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update\_updated\_at();  
CREATE TRIGGER schedule\_updated\_at BEFORE UPDATE ON transfusion\_schedule FOR EACH ROW EXECUTE FUNCTION update\_updated\_at();  
\`\`\`

Now CREATE data/seed\_supabase.py using Faker to generate:  
\- 500 synthetic donors (Indian names, cities, blood types, antigen flags)  
  Cities: Hyderabad(40%), Mumbai(20%), Chennai(15%), Bangalore(15%), Delhi(10%)  
  Blood types: O+(38%) B+(32%) A+(21%) AB+(9%) negatives at 15% each  
  kell\_negative: 92%, duffy\_negative: 68%, kidd\_negative: 74%  
  churn\_score: beta distribution  
  preferred\_language: correlated with city (Hyderabad=Telugu 60%/Hindi 40%, Chennai=Tamil 80%)  
\- Consent records: ALL 500 donors pre-consented (data\_storage \+ outreach\_telegram \+ outreach\_sms)  
  channel='staff\_manual', language='en', note 'demo\_seed\_pre\_consented'  
\- Verification records: 70% of kell\_negative donors \= 'lab\_confirmed', 30% \= 'self\_reported'  
\- 50 Thalassemia patients (age 3-18, hemoglobin 4.0-8.5, antibody flags based on tx\_count)  
\- Transfusion schedule: 3 upcoming entries per patient (due in 3, 25, 50 days)  
\- 3 hospital staff members with auth\_token \= uuid4()  
\- Donor memory entries for all 500 donors  
\- Gamification entries for top donors

Script must be idempotent (skip if data exists). Print progress counts.

\---

\#\#\# PROMPT P1-C — Neo4j Schema \+ Constraints \+ Indexes

\*\*What this builds:\*\* Graph database schema with 4 node types and 4 relationship types.  
Pre-computed COMPATIBLE\_WITH edges enable \<100ms matching queries.  
\*\*Dependencies:\*\* P1-A, P1-B (Supabase must be seeded first)  
\*\*Files created:\*\* data/neo4j\_schema.cypher, data/seed\_neo4j.py

\---

You are building the Neo4j Aura graph database schema for BloodBridge AI.

WHY NEO4J: PostgreSQL JOINs across 500 donors × 50 patients × 8 antigen dimensions \= O(n²).  
Neo4j traverses COMPATIBLE\_WITH edges in O(1) — top-8 donors in \<100ms.

CREATE data/neo4j\_schema.cypher:

\*\*━━━ NODE TYPES (4) ━━━\*\*  
\`\`\`  
(:Donor { donor\_id, name, blood\_type, city, ward, lat, lng,  
          kell\_negative, duffy\_negative, kidd\_negative, rh\_e\_negative, rh\_c\_negative, mns\_negative,  
          donation\_count, churn\_score, is\_active, telegram\_chat\_id, preferred\_language })

(:Patient { patient\_id, name, blood\_type, hospital, city, ward, lat, lng,  
            antibody\_kell, antibody\_duffy, antibody\_kidd, antibody\_rh\_e, antibody\_rh\_c,  
            kell\_negative, hemoglobin, status, transfusion\_count })

(:Hospital { hospital\_id, name, city, ward, lat, lng, contact })

(:BloodBank { bank\_id, name, city, lat, lng, contact,  
              units\_b\_pos, units\_o\_pos, units\_a\_pos, units\_ab\_pos,  
              units\_b\_neg, units\_o\_neg, units\_a\_neg, units\_ab\_neg,  
              updated\_at })  
\`\`\`

\*\*━━━ RELATIONSHIP TYPES (4) ━━━\*\*  
\`\`\`  
(:Donor)-\[:IN\_CHAIN { request\_id, chain\_position, status, alerted\_at, confirmed\_at }\]-\>(:Patient)  
(:Donor)-\[:COMPATIBLE\_WITH { antigen\_score:float, kell\_safe:bool, duffy\_safe:bool, kidd\_safe:bool, last\_computed:datetime }\]-\>(:Patient)  
(:Patient)-\[:ADMITTED\_AT\]-\>(:Hospital)  
(:Hospital)-\[:NEAR\_BANK { distance\_km:float }\]-\>(:BloodBank)  
\`\`\`

\*\*━━━ CONSTRAINTS \+ INDEXES ━━━\*\*  
\`\`\`cypher  
CREATE CONSTRAINT donor\_id\_unique IF NOT EXISTS FOR (d:Donor) REQUIRE d.donor\_id IS UNIQUE;  
CREATE CONSTRAINT patient\_id\_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient\_id IS UNIQUE;  
CREATE CONSTRAINT hospital\_id\_unique IF NOT EXISTS FOR (h:Hospital) REQUIRE h.hospital\_id IS UNIQUE;  
CREATE INDEX donor\_city IF NOT EXISTS FOR (d:Donor) ON (d.city);  
CREATE INDEX donor\_blood\_type IF NOT EXISTS FOR (d:Donor) ON (d.blood\_type);  
CREATE INDEX patient\_blood\_type IF NOT EXISTS FOR (p:Patient) ON (p.blood\_type);  
CREATE POINT INDEX donor\_location IF NOT EXISTS FOR (d:Donor) ON (d.location);  
\`\`\`

\*\*━━━ THE KEY MATCHING CYPHER QUERY ━━━\*\*  
\`\`\`cypher  
MATCH (p:Patient {patient\_id: $patient\_id})  
MATCH (d:Donor)-\[c:COMPATIBLE\_WITH\]-\>(p)  
WHERE d.is\_active \= true  
  AND d.blood\_type \= p.blood\_type  
  AND (NOT p.antibody\_kell OR d.kell\_negative \= true)  
  AND (NOT p.antibody\_duffy OR d.duffy\_negative \= true)  
  AND (NOT p.antibody\_kidd OR d.kidd\_negative \= true)  
WITH d, c,  
     point.distance(  
       point({latitude: d.lat, longitude: d.lng}),  
       point({latitude: p.lat, longitude: p.lng})  
     ) AS distance\_m  
WHERE d.last\_donation\_date IS NULL OR date() \- d.last\_donation\_date \>= 56  
ORDER BY c.antigen\_score DESC, distance\_m ASC  
LIMIT 8  
RETURN d.donor\_id, d.name, d.telegram\_chat\_id, d.phone, d.preferred\_language,  
       c.antigen\_score, d.churn\_score, distance\_m / 1000 AS distance\_km  
\`\`\`

CREATE data/seed\_neo4j.py that:  
1\. Reads all donors and patients from Supabase  
2\. Creates/merges Donor and Patient nodes for all records  
3\. Creates 8 Hospital nodes (Hyderabad hospitals)  
4\. Creates 8 BloodBank nodes with realistic unit counts  
5\. For EVERY (donor, patient) pair where blood\_type matches:  
   \- Calls antigen\_scorer.compute\_antigen\_score(donor, patient)  
   \- Creates COMPATIBLE\_WITH edge with score (only if score \>= 0.60)  
6\. Creates ADMITTED\_AT edges (each patient → their hospital)  
7\. Creates NEAR\_BANK edges (hospital → nearby blood banks with distance\_km)  
8\. Prints: "Graph: 500 Donor nodes, 50 Patient nodes, \~4200 COMPATIBLE\_WITH edges"

IMPORTANT: O(n²) computation runs ONCE at seed time. After seeding all queries are O(1).

\---

\#\#\# PROMPT P1-D — Synthetic Data Generation \+ ML Model Training

\*\*What this builds:\*\* 500-donor synthetic dataset \+ 1000-sample training data \+ trains both  
XGBoost models \+ SVD challenge matrix. All .joblib files committed so models load instantly.  
\*\*Dependencies:\*\* P1-A, P1-B (schema exists)  
\*\*Files created:\*\* data/generate\_synthetic.py, ml/models/urgency\_model.joblib,  
               ml/models/churn\_model.joblib, ml/models/svd\_challenges.joblib

\---

You are building the synthetic data generation pipeline for BloodBridge AI hackathon demo.

CREATE data/generate\_synthetic.py:

\*\*━━━ SECTION 1: DONOR DATA (500 donors) ━━━\*\*  
Use Faker(locale='en\_IN'). Generate with realistic Indian distributions:  
Cities: Hyderabad(40%), Mumbai(20%), Chennai(15%), Bangalore(15%), Delhi(10%)  
Blood types: O+(38%), B+(32%), A+(21%), AB+(9%), negatives at 15% of each  
kell\_negative: 92%, duffy\_negative: 68%, kidd\_negative: 74%  
donation\_count: weighted — most 1-5, power donors 10-25  
last\_donation\_date: 0-365 days ago, 30% never donated  
hemoglobin: 11.5–16.5 g/dL  
churn\_score: beta distribution  
preferred\_language: city-correlated (Hyderabad=Telugu 60%/Hindi 40%, Chennai=Tamil 80%)

\*\*━━━ SECTION 2: PATIENT DATA (50 patients) ━━━\*\*  
Thalassemia Major profile:  
age: 3–18 years  
transfusion\_count: 10–250 (older patients have more)  
antibody flags: \>20 transfusions → 40% chance of each antibody  
hemoglobin: 4.0–8.5 g/dL (pre-transfusion)  
next\_transfusion\_due: \-30 to \+7 days from today (many overdue)  
status: CRITICAL if Hgb \< 6 OR overdue \> 14d, OVERDUE if \> 0d past due

\*\*━━━ SECTION 3: URGENCY MODEL TRAINING DATA (1000 samples) ━━━\*\*  
Features: \[hemoglobin, days\_since\_transfusion, has\_cardiac\_flag, age, transfusion\_count, antibody\_count\]  
Labels (urgency\_score 0-10):  
\`\`\`python  
base \= 10 \- (hemoglobin / 16.5) \* 4  
overdue \= min(days\_since\_transfusion / 30, 3\)  
cardiac \= 2.0 if has\_cardiac\_flag else 0  
urgency\_score \= min(10, base \+ overdue \+ cardiac \+ gauss(0, 0.3))  
priority \= "CRITICAL" if \>= 7.5 else "HIGH" if \>= 5.0 else "ROUTINE"  
\`\`\`

\*\*━━━ SECTION 4: CHURN MODEL TRAINING DATA (1000 samples) ━━━\*\*  
Features: \[days\_since\_donation, response\_time\_decay, missed\_alerts, avg\_response\_lag,  
           kell\_negative\_flag, city\_blood\_scarcity\_score, badge\_count, chain\_position\_avg\]  
Labels (churn\_probability 0-1):  
\`\`\`python  
base   \= (days\_since\_donation / 180\) \* 0.35  
resp   \= (1 \- response\_rate) \* 0.20  
missed \= (missed\_alerts / 10\) \* 0.15  
lag    \= min(avg\_response\_lag / 3600, 1\) \* 0.12  
kell   \= \-0.08 if kell\_negative\_flag else 0  
badge  \= \-(badge\_count \* 0.03)  
churn  \= clip(base \+ resp \+ missed \+ lag \+ kell \+ badge \+ gauss(0, 0.05), 0, 1\)  
\`\`\`

\*\*━━━ SECTION 5: TRAIN AND SAVE ALL THREE MODELS ━━━\*\*  
\`\`\`python  
\# Urgency  
XGBRegressor(n\_estimators=100, max\_depth=4, learning\_rate=0.1, random\_state=42)  
joblib.dump(model, 'ml/models/urgency\_model.joblib')  
\# Print: "Urgency model trained. MAE: {:.3f}"

\# Churn  
XGBRegressor(n\_estimators=100, max\_depth=4, learning\_rate=0.1, random\_state=42)  
joblib.dump(model, 'ml/models/churn\_model.joblib')  
\# Print: "Churn model trained. R²: {:.3f}"

\# SVD  
TruncatedSVD(n\_components=10, random\_state=42)  
\# 500 donors × 10 challenge types interaction matrix  
joblib.dump({'svd':svd,'matrix':matrix,'latent':latent}, 'ml/models/svd\_challenges.joblib')  
\# Print: "SVD challenge recommender trained."  
\`\`\`

Print full summary table at end. Script must complete in under 2 minutes on laptop.  
\---

\#\# PHASE 2 — CORE MATCHING ENGINE

\---

\#\#\# PROMPT P2-A — 8-Antigen ISBT Compatibility Scorer

\*\*What this builds:\*\* Clinically accurate compatibility scorer using ISBT penalty weights.  
The medical core of the entire system.  
\*\*Dependencies:\*\* P1-A  
\*\*Files created:\*\* ml/antigen\_scorer.py

\---

You are building the 8-antigen blood compatibility scorer for BloodBridge AI.

CLINICAL CONTEXT: Thalassemia patients develop allo-antibodies from repeated transfusions.  
Ignoring minor antigen mismatches causes Delayed Hemolytic Transfusion Reactions — fatal risk.

CREATE ml/antigen\_scorer.py:

\`\`\`python  
ANTIGEN\_PENALTIES \= {  
    'kell':  0.35,   \# Most immunogenic after ABO — severe DHTR risk  
    'duffy': 0.25,   \# High immunogenic — prevalent in Indian population  
    'kidd':  0.20,   \# Moderate — delayed reactions, hard to detect  
    'rh\_e':  0.10,   \# Rh subtype — common in alloimmunized patients  
    'rh\_c':  0.05,   \# Rh subtype  
    'mns':   0.03,   \# Lower clinical significance  
    'abo':   0.02,   \# Residual ABO scoring  
}

def compute\_antigen\_score(donor: dict, patient: dict) \-\> float:  
    """  
    Score 0.0–1.0. 1.0 \= perfect match. 0.0 \= dangerous mismatch.

    Logic:  
    1\. Start with score \= 1.0  
    2\. If blood\_type mismatch → return 0.0 immediately (unsafe — ABO incompatibility)  
    3\. For each antigen: if patient has antibody AND donor is NOT antigen-negative → subtract penalty  
    4\. Special: if patient.kell\_negative=True AND not donor.kell\_negative → subtract 0.35  
    5\. Return max(0.0, round(score, 2))  
    """

def get\_eligibility\_flags(donor: dict) \-\> dict:  
    """Return which antigens this donor can safely provide."""  
    return { 'kell\_safe':donor.get('kell\_negative',False), 'duffy\_safe':..., ... }

def explain\_score(donor: dict, patient: dict, score: float) \-\> str:  
    """Human-readable explanation for Admin trace viewer."""  
\`\`\`

Add \_\_main\_\_ block with 4 test cases validating clinical accuracy.

\---

\#\#\# PROMPT P2-B — Donor Eligibility Filter

\*\*What this builds:\*\* Pre-screening gate filtering medically ineligible donors before  
expensive ML scoring. Based on WHO \+ NBTC India guidelines.  
\*\*Dependencies:\*\* P1-A  
\*\*Files created:\*\* ml/eligibility\_filter.py

\---

You are building the donor eligibility filter for BloodBridge AI.

CLINICAL RULES (WHO \+ NBTC India):  
\- Minimum 56 days between whole blood donations  
\- Minimum hemoglobin: 12.5 g/dL women, 13.0 g/dL men (use 12.5 as safe threshold)  
\- No active medical hold flag  
\- Blood type must match patient need  
\- Donor must be active (not deactivated)

CREATE ml/eligibility\_filter.py:

\`\`\`python  
check\_donor\_eligibility(donor: dict, patient: dict) \-\> dict  
    \# Returns: { 'eligible':bool, 'reason':str|None, 'days\_until\_eligible':int|None }  
    \# Checks in order (return on first failure for efficiency):  
    \# 1\. is\_active check  
    \# 2\. medical\_hold check  
    \# 3\. blood\_type match  
    \# 4\. 56-day gap: days\_since \= (date.today() \- last\_donation\_date).days; if \< 56 → fail  
    \# 5\. hemoglobin threshold  
    \# 6\. All pass → eligible

filter\_eligible\_donors(donors: list\[dict\], patient: dict) \-\> list\[dict\]  
    \# Filter list, sort by days\_since\_donation DESC (longest gap first — most ready)  
    \# Log: "Eligibility filter: 312/500 eligible for P-10234"

get\_eligibility\_summary(donors, patient) \-\> dict  
    \# Returns counts by rejection reason for admin/trace viewer  
\`\`\`

Handle None last\_donation\_date gracefully (treat as always eligible on gap check).

\---

\#\#\# PROMPT P2-C — XGBoost Urgency Scorer

\*\*What this builds:\*\* ML model converting patient clinical parameters into urgency score.  
Loads from pre-trained .joblib — zero training at runtime.  
\*\*Dependencies:\*\* P1-D (models pre-trained)  
\*\*Files created:\*\* ml/urgency\_scorer.py, ml/train\_urgency.py

\---

You are building the XGBoost urgency scorer for BloodBridge AI.

CREATE ml/urgency\_scorer.py:

\`\`\`python  
URGENCY\_FEATURES \= \['hemoglobin','days\_overdue','has\_cardiac\_flag','age','transfusion\_count','antibody\_count'\]

class UrgencyScorer:  
    MODEL\_PATH \= 'ml/models/urgency\_model.joblib'

    def \_load\_model(self): \# load .joblib or warn \+ use rule-based fallback

    def \_extract\_features(self, patient: dict) \-\> np.ndarray:  
        \# hemoglobin, max(0, days since next\_transfusion\_due), has\_cardiac\_flag,  
        \# age, transfusion\_count, sum(antibody flags)

    def score(self, patient: dict) \-\> dict:  
        """Returns: {'urgency\_score':8.7, 'priority':'CRITICAL', 'features':{...}}"""  
        \# Rule-based fallback if model not loaded:  
        \# raw \= (10 \- hgb/16.5\*4) \+ min(overdue/30, 3\) \+ cardiac\*2  
        \# priority \= CRITICAL if \>= 7.5, HIGH if \>= 5.0, else ROUTINE  
\`\`\`

Also CREATE ml/train\_urgency.py — standalone training script with MAE, RMSE, confusion matrix.

\---

\#\#\# PROMPT P2-D — Neo4j Matching Query \+ COMPATIBLE\_WITH Edge Builder

\*\*What this builds:\*\* Neo4jMatchingAgent query layer returning top-8 donors in \<100ms.  
\*\*Dependencies:\*\* P1-C (Neo4j seeded), P2-A (antigen scorer)  
\*\*Files created:\*\* agents/neo4j\_match.py

\---

You are building the Neo4j matching query layer for BloodBridge AI.

CREATE agents/neo4j\_match.py:

\`\`\`python  
class Neo4jMatcher:

    MATCH\_QUERY \= """  
    MATCH (p:Patient {patient\_id: $patient\_id})  
    MATCH (d:Donor)-\[c:COMPATIBLE\_WITH\]-\>(p)  
    WHERE d.is\_active \= true  
      AND d.blood\_type \= p.blood\_type  
      AND (NOT p.antibody\_kell OR d.kell\_negative \= true)  
      AND (NOT p.antibody\_duffy OR d.duffy\_negative \= true)  
      AND (NOT p.antibody\_kidd OR d.kidd\_negative \= true)  
    WITH d, c,  
         point.distance(  
             point({latitude: d.lat, longitude: d.lng}),  
             point({latitude: p.lat, longitude: p.lng})  
         ) AS distance\_m  
    ORDER BY c.antigen\_score DESC, distance\_m ASC  
    LIMIT 8  
    RETURN d.donor\_id, d.name, d.telegram\_chat\_id, d.phone,  
           d.preferred\_language, d.churn\_score, d.blood\_type,  
           c.antigen\_score, c.kell\_safe, distance\_m / 1000 AS distance\_km  
    """

    \# UPDATE\_CHAIN\_STATUS\_QUERY — update IN\_CHAIN edge status  
    \# CREATE\_CHAIN\_EDGES\_QUERY — UNWIND chain\_nodes, MERGE IN\_CHAIN edges  
    \# STALE\_ALERTED\_QUERY — find ALERTED nodes older than $timeout\_minutes

    async def find\_top\_donors(patient\_id: str) \-\> list\[dict\]  
        \# Log: "Neo4j match: 8 donors found in 67ms for P-10234"

    async def create\_chain(request\_id, patient\_id, chain\_nodes)  
    async def update\_chain\_status(request\_id, donor\_id, patient\_id, status)  
    async def get\_stale\_alerted\_nodes(timeout\_minutes=7) \-\> list\[dict\]  
    async def rebuild\_edges\_for\_donor(donor\_id: str)  
\`\`\`

\---

\#\# PHASE 3 — LANGGRAPH AGENT PIPELINE

\---

\#\#\# PROMPT P3-A — AgentState TypedDict \+ LangGraph Graph Skeleton

\*\*What this builds:\*\* Shared state object for all 9 agents. LangGraph StateGraph wiring.  
The single invoke() that runs the entire pipeline.  
\*\*Dependencies:\*\* P1-A, P2-A, P2-B, P2-C, P2-D  
\*\*Files created:\*\* models/state.py, agents/graph.py

\---

You are building the LangGraph agent pipeline skeleton for BloodBridge AI.

CREATE models/state.py:

\`\`\`python  
from typing import TypedDict, Optional, Literal, Annotated  
from langgraph.graph.message import add\_messages

class ChainNodeState(TypedDict):  
    donor\_id: str; donor\_name: str; chain\_position: int  
    status: Literal\['PENDING','ALERTED','CONFIRMED','DECLINED','VOICE','SMS','COMPLETED'\]  
    antigen\_score: float; telegram\_chat\_id: Optional\[str\]; phone: Optional\[str\]  
    preferred\_language: str; distance\_km: float; alerted\_at: Optional\[str\]; confirmed\_at: Optional\[str\]

class AgentState(TypedDict):  
    \# Input  
    request\_id: str; patient\_id: str; blood\_type: str; city: str  
    hospital\_name: str; ward: Optional\[str\]; triggered\_by: str; language: str  
    request\_mode: Literal\['emergency','proactive'\]  
    days\_until\_due: Optional\[int\]  
    \# Patient data  
    patient: Optional\[dict\]; patient\_antibody\_flags: dict  
    \# Matching  
    eligible\_donors: list\[dict\]; scored\_donors: list\[dict\]  
    urgency\_result: dict; matched\_donors: list\[dict\]  
    \# Conflict  
    conflict\_detected: bool; conflict\_resolution: Optional\[str\]  
    \# Planning  
    outreach\_plan: list\[dict\]; channel\_strategy: str  
    \# Chain state  
    chain: list\[ChainNodeState\]  
    chain\_confirmed\_count: int; chain\_declined\_count: int  
    \# Monitoring  
    chain\_break\_detected: bool; stale\_positions: list\[int\]  
    \# Consent tracking  
    donors\_consent\_checked: bool  
    non\_consented\_donors: list\[str\]  
    \# Outcomes  
    outcome: Optional\[Literal\['SUCCESS','ESCALATED','IN\_PROGRESS','FAILED'\]\]  
    badges\_awarded: list\[str\]; impact\_story: Optional\[str\]  
    \# Tracing  
    trace\_id: str; node\_timings: dict; errors: list\[str\]  
\`\`\`

CREATE agents/graph.py:

\`\`\`python  
def build\_bloodbridge\_graph() \-\> CompiledGraph:  
    graph \= StateGraph(AgentState)  
    \# 14 nodes: intake, eligibility, antigen\_score, urgency\_score, neo4j\_match,  
    \#           conflict, planner, outreach, monitor, repair, inventory, voice,  
    \#           gamification, outcome  
    \# Edges:  
    \# intake → eligibility  
    \# eligibility → antigen\_score AND urgency\_score (parallel)  
    \# antigen\_score → neo4j\_match; urgency\_score → neo4j\_match (join)  
    \# neo4j\_match → conflict (if conflict\_detected) OR planner  
    \# conflict → planner → outreach → monitor  
    \# monitor conditional: complete→outcome, repair→repair, voice→voice, inventory→inventory, wait→monitor  
    \# repair → outreach; voice → monitor; inventory → outcome  
    \# outcome → gamification → END  
    return graph.compile()

def route\_after\_monitor(state: AgentState) \-\> str:  
    if state.get('outcome') in \['SUCCESS','ESCALATED'\]: return 'complete'  
    stale \= state.get('stale\_positions', \[\])  
    if len(stale) \> 3: return 'inventory'  
    if stale: return 'repair'  
    return 'wait'

async def run\_emergency\_pipeline(request\_data: dict) \-\> AgentState:  
    """Main entry point called by FastAPI. Returns final AgentState."""  
    initial\_state: AgentState \= {  
        'request\_id': request\_data\['request\_id'\],  
        'patient\_id': request\_data\['patient\_id'\],  
        'blood\_type': request\_data\['blood\_type'\],  
        'city': request\_data\['city'\],  
        'hospital\_name': request\_data\['hospital\_name'\],  
        'ward': request\_data.get('ward'),  
        'triggered\_by': request\_data.get('triggered\_by','staff'),  
        'language': 'hi',  
        'request\_mode': request\_data.get('request\_mode','emergency'),  
        'days\_until\_due': request\_data.get('days\_until\_due'),  
        'patient': None, 'eligible\_donors': \[\], 'scored\_donors': \[\], 'matched\_donors': \[\],  
        'chain': \[\], 'chain\_confirmed\_count': 0, 'chain\_declined\_count': 0,  
        'conflict\_detected': False, 'conflict\_resolution': None,  
        'outreach\_plan': \[\], 'chain\_break\_detected': False, 'stale\_positions': \[\],  
        'urgency\_result': {}, 'patient\_antibody\_flags': {},  
        'donors\_consent\_checked': False, 'non\_consented\_donors': \[\],  
        'outcome': None, 'badges\_awarded': \[\], 'impact\_story': None,  
        'trace\_id': f'TRC-{random.randint(1000,9999)}', 'node\_timings': {}, 'errors': \[\]  
    }  
    return await get\_graph().ainvoke(initial\_state)  
\`\`\`

\---

\#\#\# PROMPT P3-B — IntakeAgent \+ EligibilityFilterAgent

\*\*What this builds:\*\* First two pipeline agents. IntakeAgent fetches patient data \+ detects  
language. EligibilityFilterAgent screens all 500 donors to eligible candidates.  
\*\*Dependencies:\*\* P3-A, P2-B  
\*\*Files created:\*\* agents/intake.py, agents/eligibility.py

\---

CREATE agents/intake.py — \`async def intake\_agent(state)\`:  
1\. Record start time  
2\. Fetch patient from Supabase → state\['patient'\]  
3\. Extract antibody flags → state\['patient\_antibody\_flags'\]  
4\. langdetect on trigger\_text → state\['language'\] (default 'hi')  
5\. Upsert emergency\_request in Supabase (status='IN\_PROGRESS')  
6\. Create agent\_trace record  
7\. Record timing state\['node\_timings'\]\['intake\_node'\]

CREATE agents/eligibility.py — \`async def eligibility\_agent(state)\`:  
1\. Fetch donors WHERE blood\_type=state\['blood\_type'\] AND city=state\['city'\] AND is\_active=true  
   ORDER BY last\_donation\_date ASC NULLS FIRST LIMIT 200  
2\. If local \< 8: fetch additional from other cities (same blood\_type)  
3\. Run filter\_eligible\_donors(donors, state\['patient'\])  
4\. Log count. Store in state\['eligible\_donors'\]  
5\. If zero: state\['errors'\].append(...) state\['outcome'\]='ESCALATED'

Target: \<200ms (no LLM)

\---

\#\#\# PROMPT P3-C — AntigenScoringAgent \+ UrgencyScoringAgent (Parallel)

\*\*What this builds:\*\* Two agents running in parallel. Antigen scorer runs on all eligible donors.  
Urgency scorer runs XGBoost on patient's clinical data.  
\*\*Dependencies:\*\* P3-A, P3-B, P2-A, P2-C  
\*\*Files created:\*\* agents/matching.py

\---

CREATE agents/matching.py:

\`\`\`python  
async def antigen\_scoring\_agent(state):  
    for donor in state\['eligible\_donors'\]:  
        score \= compute\_antigen\_score(donor, state\['patient'\])  
        donor\['antigen\_score'\] \= score  
        donor\['antigen\_flags'\] \= get\_eligibility\_flags(donor)  
    \# Sort by antigen\_score DESC → state\['scored\_donors'\]  
    \# Target: \<200ms for 200 donors

async def urgency\_scoring\_agent(state):  
    result \= get\_urgency\_scorer().score(state\['patient'\])  
    state\['urgency\_result'\] \= result  
    \# Update emergency\_request urgency\_score+priority in Supabase  
    \# If priority \== 'CRITICAL': send ntfy.sh critical alert IMMEDIATELY (before chain)  
\`\`\`

Module-level singletons for both scorers.

\---

\#\#\# PROMPT P3-D — Neo4jMatchingAgent \+ ConflictResolverAgent

\*\*What this builds:\*\* Neo4jMatchingAgent executes graph query. ConflictResolverAgent uses  
Gemini to resolve priority when two CRITICAL patients share a rare donor.  
\*\*Dependencies:\*\* P3-C, P2-D  
\*\*Files created:\*\* agents/neo4j\_match.py (completes), agents/conflict.py

\---

\`\`\`python  
async def neo4j\_matching\_agent(state):  
    \# 1\. Run matcher.find\_top\_donors(state\['patient\_id'\])  
    \# 2\. If zero: escalate  
    \# 3\. Build chain ChainNodeState list  
    \# 4\. Check conflict: other IN\_PROGRESS CRITICAL requests sharing our matched donors  
    \#    → state\['conflict\_detected'\] \= True if found  
    \# 5\. Write IN\_CHAIN edges to Neo4j \+ blood\_chains to Supabase  
    \# 6\. Broadcast WebSocket {type:'chain\_started', request\_id, chain\_summary}  
\`\`\`

CREATE agents/conflict.py — \`async def conflict\_resolver\_agent(state)\`:  
\`\`\`  
Gemini prompt — strict JSON output:  
  SYSTEM: Clinical triage AI. Two Thalassemia patients need same rare donor.  
          Respond ONLY with valid JSON.  
  USER: {conflict\_type, donor dict, patient\_a dict, patient\_b dict, question}  
Expected: {priority\_patient\_id, secondary\_patient\_id, justification, confidence, recommendation}  
TIMEOUT: 3 seconds hard limit → fallback: higher urgency\_score wins  
Reorder chain: prioritized patient's donors first  
\`\`\`

\---

\#\#\# PROMPT P3-E — PlannerAgent (Gemini)

\*\*What this builds:\*\* Gemini decides optimal outreach strategy per donor — channel, tone,  
personalization based on donor memory.  
\*\*Dependencies:\*\* P3-D, services/donor\_memory.py  
\*\*Files created:\*\* agents/planner.py

\---

CREATE agents/planner.py — \`async def planner\_agent(state)\`:  
\`\`\`python  
    for donor in state\['chain'\]:  
        \# Fetch donor\_memory from Supabase

        \# Channel determination:  
        \# If request\_mode \== 'proactive': chain size \= 5, tone \= 'warm\_advance', timeouts \= 48h  
        \# If request\_mode \== 'emergency': chain size \= 8, tone \= 'urgent', timeout \= 7min

        \# Channel routing (3-tier):  
        \# Tier 1: telegram\_chat\_id AND consent 'outreach\_telegram' → 'telegram'  
        \# Tier 2: phone AND consent 'outreach\_voice' AND 8am-8pm IST → 'voice\_queue'  
        \# Tier 3: phone AND consent 'outreach\_sms' → 'sms\_queue'

    \# Batch ALL 8 donors into ONE Gemini call (not 8 separate calls)  
    \# Gemini returns per-donor: {tone, opening\_hook, key\_message, include\_badge\_mention}  
    \# FALLBACK: if Gemini fails → use warm\_urgent tone for all  
    \# Target: \<1.5 seconds total  
\`\`\`

\---

\#\#\# PROMPT P3-F — OutreachAgent (Groq \+ langdetect · Parallel Fan-out ×8)

\*\*What this builds:\*\* Sends personalized Telegram messages to 8 donors simultaneously.  
Groq Llama-3.3-70B for fast multilingual generation. Consent check before every send.  
Explicit donor memory context injection into every LLM call.  
10-language fallback templates. SMS routing for donors without Telegram.  
\*\*Dependencies:\*\* P3-E, services/telegram\_bot.py, services/consent\_service.py, services/donor\_memory.py  
\*\*Files created:\*\* agents/outreach.py

\---

CREATE agents/outreach.py:

\`\`\`python  
OUTREACH\_SYSTEM\_PROMPT \= """You are BloodBridge AI — emergency blood donation coordinator India.  
Generate a concise Telegram message requesting blood donation.  
MUST: be in donor's language, under 150 words, include blood type \+ hospital \+ urgency,  
reference donation history if provided, end with "Reply YES to confirm".  
10 supported languages. Plain text only — no markdown, no emojis in body."""

FALLBACK\_TEMPLATES \= {  
    'hi': "🩸 URGENT: {blood\_type} blood needed at {hospital}. Kya aap donate kar sakte hain? Reply YES",  
    'te': "🩸 URGENT: {hospital} lo {blood\_type} blood avasaram. Donate chestagara? Reply YES",  
    'ta': "🩸 URGENT: {hospital} ல {blood\_type} blood தேவை. Donate செய்வீர்களா? Reply YES",  
    'en': "🩸 URGENT: {blood\_type} blood needed at {hospital}. Can you donate? Reply YES",  
    'kn': "🩸 URGENT: {hospital} ನಲ್ಲಿ {blood\_type} ರಕ್ತ ಬೇಕು. Donate ಮಾಡುತ್ತೀರಾ? Reply YES",  
    'ml': "🩸 URGENT: {hospital} ൽ {blood\_type} രക്തം ആവശ്യം. Donate ചെയ്യുമോ? Reply YES",  
    'mr': "🩸 URGENT: {hospital} मध्ये {blood\_type} रक्त हवे. Donate कराल? Reply YES",  
    'bn': "🩸 URGENT: {hospital}এ {blood\_type} রক্ত চাই। Donate করবেন? Reply YES",  
    'gu': "🩸 URGENT: {hospital}માં {blood\_type} blood જોઈએ. Donate? Reply YES",  
    'pa': "🩸 URGENT: {hospital}ਵਿੱਚ {blood\_type} ਖੂਨ ਚਾਹੀਦਾ। Donate? Reply YES",  
}

async def generate\_outreach\_message(plan: dict, state: AgentState) \-\> str:  
    """  
    CRITICAL: Before building Groq prompt, fetch and inject donor memory context.  
    memory\_context \= await build\_memory\_context\_for\_llm(plan\['donor\_id'\])  
    This ensures personalization uses persistent tone\_profile, emotional\_anchors,  
    donation history, and preferred language from donor\_memory table.  
    Inject memory\_context into the Groq user prompt alongside plan data.  
    """  
    memory\_context \= await build\_memory\_context\_for\_llm(plan\['donor\_id'\])  
    \# Build Groq prompt with: plan, state emergency details, memory\_context  
    \# Call Groq Llama-3.3-70B with OUTREACH\_SYSTEM\_PROMPT  
    \# Return generated message string

async def outreach\_agent(state):  
    \# CONSENT CHECK — before any send  
    for plan in outreach\_plan:  
        has\_consent \= await consent\_service.check\_consent(donor\_id, f'outreach\_{channel}')  
        if not has\_consent:  
            state\['non\_consented\_donors'\].append(donor\_id)  
            continue  \# skip — not a failure

    \# PARALLEL FAN-OUT — all consented donors simultaneously  
    messages \= await asyncio.gather(\*\[  
        generate\_outreach\_message(plan, state) for plan in consented\_plans  
    \], return\_exceptions=True)

    \# For each successful message:  
    \# If channel='telegram': send via Telegram  
    \# If channel='sms\_queue': add to sms\_batch (sent by SMSService)  
    \# Update blood\_chains status='ALERTED' (or 'SMS')  
    \# Update Neo4j IN\_CHAIN status='ALERTED'

    \# Broadcast WebSocket {type:'outreach\_sent', request\_id, alerted\_count}  
    \# Log: "OutreachAgent: 7/8 messages sent (1 no-consent skipped)"  
    \# Target: all 8 generated and sent in \<3 seconds  
\`\`\`

\---

\#\#\# PROMPT P3-G — ChainMonitorAgent (APScheduler)

\*\*What this builds:\*\* Background monitoring every 5 minutes detecting stale ALERTED nodes  
(\>7 min without response). The heartbeat of the system.  
\*\*Dependencies:\*\* P3-F, P2-D  
\*\*Files created:\*\* agents/monitor.py, scheduler/jobs.py, scheduler/cron.py

\---

CREATE agents/monitor.py — \`async def chain\_monitor\_agent(state)\`:  
1\. Query Neo4j stale ALERTED nodes for this request\_id  
2\. Query blood\_chains CONFIRMED count  
3\. If confirmed \>= 1: state\['outcome'\]='SUCCESS'; return  
4\. If all 8 declined/stale: state\['outcome'\]='ESCALATED'  
5\. state\['stale\_positions'\] \= \[stale chain positions\]  
6\. state\['chain\_break\_detected'\] \= len(stale) \> 0  
7\. Broadcast WebSocket {type:'chain\_monitor\_update', ...}

CREATE scheduler/jobs.py:

\`\`\`python  
async def monitor\_all\_active\_chains():  
    """Every 5 min. Check all IN\_PROGRESS requests for stale nodes. Trigger repair."""

async def run\_nightly\_churn\_batch():  
    """Daily 8 PM IST. Score all donors. Dispatch CRITICAL=voice, HIGH=outreach, MEDIUM=challenge."""

async def run\_proactive\_outreach():  
    """Daily 7 AM IST. Fetch patients due in 5-7 days. Start warm outreach pipelines."""  
    from services.transfusion\_calendar import get\_patients\_due\_in\_days, mark\_schedule\_outreach\_started  
    patients\_due \= await get\_patients\_due\_in\_days(advance\_days=5)  
    for patient in patients\_due:  
        if not already\_has\_active\_request(patient\['patient\_id'\]):  
            \# CRITICAL: capture returned state to get request\_id for schedule update  
            result \= await run\_emergency\_pipeline({  
                'patient\_id': patient\['patient\_id'\],  
                'blood\_type': patient\['blood\_type'\],  
                'city': patient\['city'\],  
                'hospital\_name': patient\['hospital'\],  
                'request\_mode': 'proactive',  
                'days\_until\_due': patient\['days\_until\_due'\]  
            })  
            \# Update transfusion\_schedule with the created request\_id  
            request\_id \= result.get('request\_id')  
            if request\_id and patient.get('schedule\_id'):  
                await mark\_schedule\_outreach\_started(patient\['schedule\_id'\], request\_id)

async def cleanup\_old\_voice\_files():  
    """Daily 2 AM IST. Delete voice audio files from Supabase Storage \> 24 hours old."""

async def keep\_alive\_ping():  
    """Every 4 min. GET /health to prevent Render.com cold starts."""  
\`\`\`

CREATE scheduler/cron.py:  
\`\`\`python  
scheduler.add\_job(monitor\_all\_active\_chains, IntervalTrigger(minutes=5), id='chain\_monitor')  
scheduler.add\_job(run\_nightly\_churn\_batch, CronTrigger(hour=20, minute=0), id='churn\_batch')  
scheduler.add\_job(run\_proactive\_outreach, CronTrigger(hour=7, minute=0), id='proactive\_outreach')  
scheduler.add\_job(cleanup\_old\_voice\_files, CronTrigger(hour=2, minute=0), id='voice\_cleanup')  
scheduler.add\_job(keep\_alive\_ping, IntervalTrigger(minutes=4), id='keep\_alive')  
\`\`\`

\---

\#\#\# PROMPT P3-H — ChainRepairAgent \+ InventoryAgent

\*\*What this builds:\*\* ChainRepairAgent auto-alerts next donor when one declines (\< 5 seconds).  
InventoryAgent scrapes e-RaktKosh when entire chain fails.  
\*\*Dependencies:\*\* P3-G, services/blood\_bank\_scraper.py, services/alerts.py  
\*\*Files created:\*\* agents/repair.py

\---

CREATE agents/repair.py:

\`\`\`python  
async def chain\_repair\_agent(state):  
    for stale\_position in state\['stale\_positions'\]:  
        \# Find next donor NOT in chain, lowest churn\_score, blood\_type match, 56-day OK  
        \# If found:  
        \#   Add to blood\_chains, create IN\_CHAIN Neo4j edge  
        \#   Generate repair message (Groq, shorter/more urgent tone)  
        \#   Send Telegram  
        \#   Broadcast WebSocket {type:'chain\_repaired', new\_donor\_name, position}  
        \# If NOT found after 3 repair attempts: escalate to InventoryAgent  
    \# Log: "ChainRepair: position {pos} repaired with {name} in {elapsed}ms"

async def inventory\_agent(state):  
    \# 1\. Call blood\_bank\_scraper.get\_nearest\_banks\_with\_stock(city, blood\_type)  
    \# 2\. Alert staff via ntfy.sh: "⚠️ CHAIN FAILED — nearest banks: {names}"  
    \# 3\. Update emergency\_request status='ESCALATED'  
    \# 4\. Send Telegram to staff: bank list \+ distances \+ contacts  
    \# 5\. state\['outcome'\] \= 'ESCALATED'  
\`\`\`

\---

\#\#\# PROMPT P3-I — OutcomeAgent \+ GamificationAgent

\*\*What this builds:\*\* OutcomeAgent records final result and closes all records.  
GamificationAgent awards badges, updates leaderboard, generates Gemini impact story.  
\*\*Dependencies:\*\* P3-H, services/impact\_story.py  
\*\*Files created:\*\* agents/outcome.py, agents/gamification.py

\---

CREATE agents/outcome.py — \`async def outcome\_agent(state)\`:  
1\. Update emergency\_request: status=outcome, completed\_at=NOW  
2\. Update blood\_chains: confirmed → COMPLETED, pending/alerted → released  
3\. Update patient: transfusion\_count \+= confirmed\_count  
4\. For each confirmed donor: donation\_count+1, lives\_saved+1, last\_donation\_date=today,  
   churn\_score=0.1 (just donated), update donor\_memory  
5\. Complete agent\_trace: outcome, total\_ms, nodes\_json  
6\. Broadcast WebSocket {type:'emergency\_completed', request\_id, patient\_id, outcome}  
7\. If request\_mode='proactive': call transfusion\_calendar.mark\_schedule\_completed()

\`\`\`python  
BADGE\_RULES \= {  
    'blood\_starter': {'threshold': 1,  'emoji': '🌱'},  
    'life\_saver':    {'threshold': 5,  'emoji': '❤️'},  
    'blood\_hero':    {'threshold': 10, 'emoji': '🦸'},  
    'rare\_guardian': {'condition': 'kell\_negative AND donation\_count\>=3', 'emoji': '💎'},  
    'city\_champion': {'condition': 'rank\_1\_in\_city', 'emoji': '🏆'},  
    'crisis\_hero':   {'condition': 'confirmed\_within\_2\_hours\_CRITICAL', 'emoji': '⚡'},  
}  
\`\`\`

CREATE agents/gamification.py — \`async def gamification\_agent(state)\`:  
1\. Check badge eligibility for each confirmed donor  
2\. Award new badges: insert gamification table \+ update donor\_memory.badges  
3\. Send Telegram badge notification in donor's language  
4\. Update leaderboard\_cache for city  
5\. Generate Gemini impact story (services/impact\_story.py)  
6\. Broadcast WebSocket {type:'badge\_awarded', donor\_id, donor\_name, badge\_name}

\---

\#\#\# PROMPT P3-J — ProactiveSchedulerAgent \+ TransfusionCalendarService \[NEW\]

\*\*What this builds:\*\* The most critical missing operational feature. Thalassemia patients have  
KNOWN transfusion schedules. This agent starts warm outreach 5-7 days BEFORE — handling 90%  
of real Blood Warriors workflows. Emergency pipeline \= 10% (unplanned crises).  
\*\*Dependencies:\*\* P1-B (transfusion\_schedule table), P3-F, P4-C  
\*\*Files created:\*\* agents/proactive\_scheduler.py, services/transfusion\_calendar.py

\---

You are building the ProactiveSchedulerAgent for BloodBridge AI.

CLINICAL CONTEXT: Thalassemia patients transfuse every 21-28 days on a known schedule.  
Blood Warriors' daily work is finding donors BEFORE crisis, not during it.  
Without this agent the system is reactive-only — missing 90% of real use cases.

CREATE services/transfusion\_calendar.py:

\`\`\`python  
async def get\_patients\_due\_in\_days(advance\_days: int \= 5\) \-\> list\[dict\]:  
    """Fetch patients from transfusion\_schedule WHERE  
    scheduled\_date BETWEEN today AND today+advance\_days AND status='PENDING'  
    Include schedule\_id in returned dict for mark\_schedule\_outreach\_started()."""

async def mark\_schedule\_outreach\_started(schedule\_id: int, request\_id: str):  
    """Update status='OUTREACH\_STARTED', outreach\_started\_at=NOW, request\_id=request\_id"""

async def mark\_schedule\_completed(schedule\_id: int):  
    """Update status='COMPLETED'"""

async def get\_upcoming\_schedule(days: int \= 30\) \-\> list\[dict\]:  
    """Dashboard calendar view — all upcoming, sorted by scheduled\_date ASC"""

async def create\_schedule\_entry(patient\_id, scheduled\_date, hospital, advance\_days, created\_by):  
    """Staff creates schedule entry via dashboard POST /api/schedule"""

async def auto\_generate\_schedule\_from\_history(patient\_id: str):  
    """Gemini infers transfusion interval from patient history.  
    Prompt: 'Patient had transfusions on \[dates\]. What is their interval?  
    When should next 3 be?' Creates schedule entries automatically."""  
\`\`\`

CREATE agents/proactive\_scheduler.py:

Proactive mode differences from emergency pipeline:  
\- Tone: 'warm\_advance' (not 'urgent') — friendly reminder, no panic  
\- Urgency score: capped at 4.0 (never CRITICAL)  
\- Priority: always 'ROUTINE' or 'HIGH'  
\- Chain size: 5 donors (not 8\) — less pressure needed in advance  
\- Voice call timeout: 48 hours (not 7 minutes)  
\- Message: "Aarav ki transfusion 5 din mein hai" not "EMERGENCY CRITICAL"

The APScheduler 7 AM IST job (already defined in P3-G scheduler/jobs.py):  
1\. get\_patients\_due\_in\_days(5)  
2\. Skip patients already with IN\_PROGRESS request  
3\. For each: run\_emergency\_pipeline() with request\_mode='proactive', capture result  
4\. Call mark\_schedule\_outreach\_started(schedule\_id, result\['request\_id'\])  
5\. Log: "Proactive: 3 patients due in 5 days, outreach started for all 3"  
\---

\#\# PHASE 4 — COMMUNICATION LAYER

\---

\#\#\# PROMPT P4-A — Telegram Bot Setup \+ Commands \[UPDATED\]

\*\*What this builds:\*\* Complete Telegram Bot with security, duplicate prevention, consent flow,  
and eligibility re-check on confirmation.  
\*\*Dependencies:\*\* P3-I (full pipeline), P5-E (consent service)  
\*\*Files created:\*\* services/telegram\_bot.py

\---

You are building the Telegram Bot for BloodBridge AI.

WEBHOOK SECURITY — add to webhook handler:  
\`\`\`python  
from core.security import verify\_telegram\_webhook  
if not verify\_telegram\_webhook(request, settings.TELEGRAM\_WEBHOOK\_SECRET):  
    raise HTTPException(status\_code=403, detail="Invalid webhook signature")  
\`\`\`

DUPLICATE EMERGENCY PREVENTION — in /emergency handler:  
\`\`\`python  
idem\_key \= generate\_idempotency\_key(patient\_id, blood\_type, city)  
\# Check: existing \= SELECT request\_id,status FROM emergency\_requests  
\#                   WHERE idempotency\_key=idem\_key AND idempotency\_expires\_at \> NOW()  
\# If exists: "⚠️ This emergency is already active: {request\_id}"  — return, NO duplicate  
\`\`\`

CONSENT ONBOARDING — in /start and /register handlers:  
1\. Send consent message in detected language (from consent\_service.CONSENT\_TEXTS)  
2\. Do NOT store any data until consent granted  
3\. On HAAN/YES/HA: consent\_service.grant\_consent(donor\_id, \['data\_storage','outreach\_telegram'\])  
   THEN create donor record  
4\. On NO: "Understood. We will not store your data." — stop

ELIGIBILITY RE-CHECK ON YES — critical new step:  
\`\`\`  
When donor says YES/HAAN:  
1\. Re-validate eligibility BEFORE marking CONFIRMED  
2\. If no longer eligible: "Thank you\! Unfortunately not eligible right now: {reason}"  
   Update chain status='DECLINED' reason='eligibility\_failed\_on\_confirm'  
   Trigger chain repair  
3\. Only mark CONFIRMED if eligibility passes  
\`\`\`

COMMANDS (10):  
\`\`\`  
/start        → welcome \+ new user onboarding with consent flow  
/emergency \[type\] \[city\] \[ward\]  → staff only, security check, dedup check, trigger pipeline  
/status \[request\_id\]             → chain status table with emojis  
/confirm \[request\_id\]            → staff only → OutcomeAgent → GamificationAgent  
/impact                          → donor's Gemini impact story from donor\_memory  
/badges                          → current badges \+ progress to next badge  
/register \[blood\_type\]           → donor onboarding (or photo → OCR)  
/leaderboard                     → top-5 for donor's city this month  
/consent                         → shows donor's current consent settings per type  
/revoke \[type\]                   → revoke sms|voice|all — calls consent\_service.revoke\_consent()  
/mydata                          → data export (DPDP right to access)  
/deletedata                      → right to erasure (confirm with typing CONFIRM)  
\`\`\`

PHOTO HANDLER → route to ocr\_service.extract\_blood\_type\_from\_image()  
TEXT YES/NO HANDLER → check eligibility → update chain → chain repair if NO  
POLLING (dev) vs WEBHOOK (prod) based on APP\_ENV  
All handlers: try/except, rate limit 1 emergency per 5 min per chat\_id  
\#\#\# 🚨 CRITICAL UPGRADE: CONVERT TO LANGGRAPH AGENTIC TOOL-CALLING BOT  
Do NOT build a rigid \`if text.startswith('/emergency')\` command router.   
Build a TRUE AGENTIC TELEGRAM BOT using LangGraph's \`create\_react\_agent\` and LangChain Tool-Calling.   
The bot must understand natural language, autonomously select backend tools, execute them, and reply naturally.

\*\*1. DEFINE AGENT TOOLS (LangChain \`@tool\` decorators)\*\*  
Wrap your core backend functions as tools the LLM can call. Use Pydantic for strict argument schemas so the LLM doesn't hallucinate parameters.  
\`\`\`python  
from langchain\_core.tools import tool  
from pydantic import BaseModel, Field  
from langchain\_groq import ChatGroq  
from langgraph.prebuilt import create\_react\_agent

class EmergencyInput(BaseModel):  
    blood\_type: str \= Field(description="Blood type needed, e.g., B+, O-")  
    hospital: str \= Field(description="Hospital name, e.g., KIMS Secunderabad")  
    patient\_id: str \= Field(description="Patient ID, e.g., P-10234")  
    city: str \= Field(description="City name, e.g., Hyderabad")

@tool(args\_schema=EmergencyInput)  
async def trigger\_blood\_emergency(blood\_type: str, hospital: str, patient\_id: str, city: str) \-\> str:  
    """Use this tool ONLY when an authorized hospital staff member requests an emergency blood transfusion.   
    This will autonomously trigger the 8-donor LangGraph matching pipeline."""  
    \# 1\. Verify user role is 'Staff' or 'Admin' (check Supabase via telegram\_chat\_id)  
    \# 2\. Call run\_emergency\_pipeline({'blood\_type': blood\_type, ...}) as a BackgroundTask  
    \# 3\. Return IMMEDIATELY: f"🚨 Emergency initiated for {patient\_id}. 8 donors are being alerted. I will update you as they confirm."

class StatusInput(BaseModel):  
    patient\_id: str \= Field(description="Patient ID to check status for")

@tool(args\_schema=StatusInput)  
async def check\_chain\_status(patient\_id: str) \-\> str:  
    """Use this tool to check the real-time status of a blood donation chain."""  
    \# Query Supabase/Neo4j for chain nodes.   
    \# Return formatted string: e.g., "Patient P-10234: 3 donors confirmed ✅, 2 alerted ⏳, 3 pending."

@tool  
async def get\_my\_impact() \-\> str:  
    """Use this tool when a donor asks about their stats, badges, or lives saved."""  
    \# Fetch from Supabase donor\_memory using the chat\_id from the agent state.  
    \# Return formatted string with lives saved, badges, and streak.

2\. BUILD THE LANGGRAPH REACT AGENT  
Create a dedicated agent for Telegram interactions. It must have access to the tools and the user's persistent memory.  
\# Initialize LLM with tool calling capability (Groq is fastest for Telegram)  
llm \= ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)  
tools \= \[trigger\_blood\_emergency, check\_chain\_status, get\_my\_impact\]

TELEGRAM\_AGENT\_SYSTEM\_PROMPT \= """You are the BloodBridge AI Assistant on Telegram.  
You help hospital staff coordinate emergencies and donors track their impact.  
RULES:  
1\. ALWAYS check the user's role provided in the context. If a DONOR tries to trigger an emergency, politely deny and explain they can only view their impact.  
2\. Reply in the user's preferred language (provided in context).  
3\. Keep responses under 150 words. Use emojis appropriately (🩸, 🚨, ✅).  
4\. If a tool returns a success message, relay it warmly.  
"""

\# Compile the agent  
telegram\_agent \= create\_react\_agent(llm, tools, state\_modifier=TELEGRAM\_AGENT\_SYSTEM\_PROMPT)  
3\. THE HYBRID TELEGRAM WEBHOOK HANDLER (CRITICAL FOR HACKATHON)  
You must handle "Chain Responses" (YES/NO) deterministically, and use the Agent for everything else.  
@router.post("/webhook/telegram")  
async def telegram\_webhook(request: Request):  
    update \= Update.de\_json(await request.json(), bot)  
    chat\_id \= update.effective\_chat.id  
    user\_text \= (update.message.text or "").strip()  
      
    \# Send "typing..." action immediately (Agent thinking takes 2-4 seconds)  
    await bot.send\_chat\_action(chat\_id, "typing")  
      
    \# 1\. FETCH USER CONTEXT  
    user\_context \= await get\_user\_context(chat\_id) \# Fetches role, language, name, active\_chain\_status  
      
    \# 2\. DETERMINISTIC ROUTE: ACTIVE CHAIN RESPONSES (YES/NO/HAAN)  
    \# If the donor is currently ALERTED in a chain, DO NOT use the LLM.   
    \# Process the YES/NO deterministically to prevent LLM hallucination from breaking the chain.  
    if user\_context.get('active\_chain\_status') \== 'ALERTED' and user\_text.lower() in \['yes', 'haan', 'ha', 'ok', 'no', 'nahi'\]:  
        await handle\_deterministic\_chain\_response(chat\_id, user\_text, user\_context)  
        return {"ok": True}

    \# 3\. AGENTIC ROUTE: FREE TEXT & COMMANDS  
    \# Inject user context into the agent state so tools know who is talking  
    agent\_state \= {  
        "messages": \[HumanMessage(content=f"\[User Role: {user\_context.role}\] \[Language: {user\_context.lang}\] \[Name: {user\_context.name}\] {user\_text}")\],  
    }  
      
    \# Invoke the LangGraph Agent  
    try:  
        result \= await telegram\_agent.ainvoke(agent\_state, config={"timeout": 8.0})  
        final\_response \= result\["messages"\]\[-1\].content  
    except Exception as e:  
        \# Fallback if LLM times out or fails  
        final\_response \= "🩸 Namaste\! I am currently assisting many donors. Please type /help for commands."  
          
    await bot.send\_message(chat\_id, final\_response, parse\_mode="Markdown")  
4\. HANDLING ASYNC PIPELINES (CRITICAL FOR DEMO)  
When the Agent calls trigger\_blood\_emergency, the LangGraph pipeline takes 5-10 seconds.  
The Telegram webhook WILL TIMEOUT if you wait for it.  
The Tool must return IMMEDIATELY with "Pipeline started".  
The actual pipeline runs as a FastAPI BackgroundTask.  
When the pipeline finishes (or a donor confirms), the OutcomeAgent or ChainMonitor sends a PROACTIVE Telegram message to the staff/donor via bot.send\_message().

\#\#\#\# 1\. The "Hybrid Router" (Already included in the patch, but understand why it's there)  
\*   \*\*The Problem:\*\* If a donor gets an alert saying "B+ blood needed, reply YES", and they reply "Haan", you \*\*DO NOT\*\* want the LangChain LLM to interpret that. LLMs can be unpredictable. If the LLM replies, "That's great that you said yes\! How is your day?", the chain breaks.  
\*   \*\*The Fix:\*\* The patch includes a deterministic check. If the user has an \`ALERTED\` chain node, the bot bypasses the LLM entirely and runs the strict \`handle\_deterministic\_chain\_response()\` function. The LLM Agent is \*only\* used for free-text chat, \`/status\`, \`/mystats\`, and natural language emergency triggering.

\#\#\#\# 2\. Tool Permission Enforcement (Role-Based Access)  
\*   \*\*The Problem:\*\* The LLM might let a random donor trigger an emergency if they ask nicely ("Please find blood for my friend").  
\*   \*\*The Fix:\*\* Notice in the \`trigger\_blood\_emergency\` tool definition, I added a comment: \`\# 1\. Verify user role is 'Staff'\`. The tool itself must query Supabase to check if the \`telegram\_chat\_id\` belongs to a Staff member. If not, the tool returns an error message to the LLM, and the LLM politely tells the donor they aren't authorized.

\#\#\#\# 3\. Keep the OCR (Photo) Handler Outside the Agent  
\*   \*\*The Problem:\*\* LangChain text agents don't natively process image bytes without complex multimodal setups.  
\*   \*\*The Fix:\*\* In your \`telegram\_bot.py\`, keep the \`MessageFilter.PHOTO\` handler completely separate. If a user sends a photo, route it directly to \`ocr\_service.extract\_blood\_type\_from\_image()\`. Don't pass photos to the LangGraph text agent.

\#\#\#\# 4\. Update \`requirements.txt\` (Already in P1-A, but verify)  
Ensure your AI coder knows that \`langchain-core\`, \`langgraph\`, and \`langchain-groq\` are doing the heavy lifting here. They are already in your \`requirements.txt\` from Phase 1, so no new packages are needed\!

\---

\#\#\# PROMPT P4-B — Tesseract OCR Blood Card Extractor \[UPDATED\]

\*\*What this builds:\*\* Extracts blood type from blood group card photo.  
10 Indian language packs. Verification record created. Antigen flag extraction attempt.  
\*\*Dependencies:\*\* P4-A  
\*\*Files created:\*\* services/ocr\_service.py

\---

You are building the Tesseract OCR blood card extractor for BloodBridge AI.

Tesseract language packs to install (add to Dockerfile/render build):  
\`\`\`  
apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-tel  
               tesseract-ocr-tam tesseract-ocr-kan tesseract-ocr-mal tesseract-ocr-mar  
               tesseract-ocr-ben tesseract-ocr-guj tesseract-ocr-pan  
\`\`\`

\`\`\`python  
TESSERACT\_LANG \= 'eng+hin+tel+tam+kan+mal+mar+ben+guj+pan'  
\`\`\`

CREATE services/ocr\_service.py:

\`\`\`python  
def extract\_blood\_type\_from\_image(image\_bytes: bytes) \-\> dict:  
    """  
    Returns: {blood\_type, confidence, raw\_text, method, kell\_negative}

    Steps:  
    1\. PIL Image.open(BytesIO(image\_bytes))  
    2\. Preprocess: grayscale → contrast enhance(2.0) → threshold  
    3\. pytesseract.image\_to\_string(image, lang=TESSERACT\_LANG)  
    4\. Regex patterns (English \+ 8 Indian languages):  
       r'\\b(A|B|AB|O)\[+-\]\\b'  
       r'\\b(A|B|AB|O)\\s\*(positive|negative|pos|neg)\\b'  
       r'Blood\\s\*Grp\\s\*\[:\\-\]?\\s\*(A|B|AB|O)\[+-\]'  
       r'रक्त समूह\\s\*\[:\\-\]?\\s\*(A|B|AB|O)\[+-\]'  
       r'రక్త సమూహం\\s\*\[:\\-\]?\\s\*(A|B|AB|O)\[+-\]'  
       r'இரத்த வகை\\s\*\[:\\-\]?\\s\*(A|B|AB|O)\[+-\]'  
    5\. Normalize: "B positive" → "B+", "O negative" → "O-"  
    6\. Validate against known blood types

    Confidence: standard pattern=0.95, labeled=0.85, fuzzy=0.65, not found=0.0

    KELL EXTRACTION (attempt):  
    KELL\_PATTERNS \= \[r'Kell\\s\*(positive|negative|pos|neg)', r'K\\s\*(pos|neg|\\+|-)', r'Kell-negative'\]  
    If found AND confidence \> 0.85: include 'kell\_negative' in result \+ update donor record

    FALLBACK: If confidence \< 0.6 → Gemini Vision (base64 inline image)  
    "What is the blood group shown? Reply ONLY with the blood type (A+, B-, O+, etc.)"

    AFTER EXTRACTION: create donor\_verifications record:  
    { donor\_id, antigen\_flag:'blood\_type\_confirmed', flag\_value:True,  
      verification\_type:'ocr\_card', confidence:result\['confidence'\], notes:raw\_text\[:100\] }  
    """  
\`\`\`

\---

\#\#\# PROMPT P4-C — Donor Memory System

\*\*What this builds:\*\* Persistent memory layer injected into every LLM prompt for personalization.  
\*\*Dependencies:\*\* P1-B (donor\_memory table)  
\*\*Files created:\*\* services/donor\_memory.py

\---

CREATE services/donor\_memory.py:

\`\`\`python  
async def get\_memory(donor\_id: str) \-\> dict:  
    """Fetch from Supabase donor\_memory. Return defaults if new donor."""

async def update\_memory\_after\_interaction(donor\_id: str, interaction\_type: str, metadata: dict):  
    """interaction\_type: outreach\_sent|confirmed|declined|badge\_earned|voice\_call  
    Updates: total\_interactions, last\_interaction, streak\_days(if confirmed),  
    tone\_profile(shift to formal after 3 declines), badges, last\_response\_time\_secs"""

async def build\_memory\_context\_for\_llm(donor\_id: str) \-\> str:  
    """Compact context string for injection into Groq/Gemini prompts.  
    Called explicitly by OutreachAgent, VoiceAgent, and ImpactStoryService before LLM calls.  
    "Donor: Rahul Kumar | Language: Hindi | Tone: warm | Anchors: \[saved child\]  
     13 donations, 87% response rate, 68 days ago | Streak: 7 months" """

async def detect\_and\_update\_language(donor\_id: str, message\_text: str):  
    """langdetect on incoming message. Update preferred\_language if confidence \> 0.8.  
    Only languages: hi,te,ta,en,kn,ml,mr,bn,gu,pa"""

async def add\_emotional\_anchor(donor\_id: str, anchor: str):  
    """Append anchor. Max 5 kept (oldest removed). Used in future outreach personalization."""  
\`\`\`

\---

\#\#\# PROMPT P4-D — AI Voice Agent (Vapi.ai — replaces Twilio Voice \+ gTTS)

\*\*What this builds:\*\* Voice call system for 7-min no-response donors. Vapi.ai replaces all  
of gTTS, Supabase Storage audio upload, TwiML generation, and Twilio Voice call management.  
Vapi handles TTS natively with Indian language voices, manages the call, captures speech,  
and sends a structured webhook result. Safe calling hours (8am-9pm IST). Consent check.  
\*\*Dependencies:\*\* P4-C, P3-G  
\*\*Files created:\*\* services/voice\_service.py, agents/voice.py

\---

You are building the AI Voice Agent for BloodBridge AI using Vapi.ai.

WHAT VAPI.AI REPLACES vs PREVIOUS APPROACH:  
\- REMOVED: generate\_audio\_file() — gTTS MP3 generation  
\- REMOVED: Supabase Storage audio upload \+ public URL generation  
\- REMOVED: TwiML XML generation (\<Play\>, \<Gather\> tags)  
\- REMOVED: POST /webhook/twilio/voice — TwiML endpoint  
\- REMOVED: POST /webhook/twilio/voice-response — Twilio SpeechResult NLU  
\- REMOVED: twilio client.calls.create()  
\- ADDED: Single httpx POST to https://api.vapi.ai/call/phone  
\- ADDED: Vapi assistant config (firstMessage \+ model \+ voice) in request body  
\- ADDED: POST /webhook/vapi/call-result — handles Vapi webhook JSON result

CREATE services/voice\_service.py:

\`\`\`python  
import httpx  
from services.donor\_memory import build\_memory\_context\_for\_llm  
from services.consent\_service import ConsentService  
from core.config import get\_settings  
import pytz  
from datetime import datetime

VAPI\_CALL\_ENDPOINT \= "https://api.vapi.ai/call/phone"

VAPI\_VOICE\_CONFIG \= {  
    \# Vapi voice IDs for Indian languages — use PlayHT or ElevenLabs voices via Vapi  
    'hi': {'provider': 'playht', 'voiceId': 'hindi-female-warm'},  
    'te': {'provider': 'playht', 'voiceId': 'telugu-female'},  
    'ta': {'provider': 'playht', 'voiceId': 'tamil-female'},  
    'en': {'provider': 'playht', 'voiceId': 'jennifer'},  
    'kn': {'provider': 'playht', 'voiceId': 'kannada-female'},  
    'ml': {'provider': 'playht', 'voiceId': 'malayalam-female'},  
    'mr': {'provider': 'playht', 'voiceId': 'marathi-female'},  
    'bn': {'provider': 'playht', 'voiceId': 'bengali-female'},  
}

async def generate\_voice\_script(donor: dict, emergency: dict, memory\_context: str) \-\> str:  
    """  
    Gemini generates 40-50 word spoken script in donor's language.  
    Injects memory\_context \= await build\_memory\_context\_for\_llm(donor\['donor\_id'\])  
    Natural speech (no lists, no emojis). Ends with clear YES/NO instruction.

    Example Hindi output:  
    "Namaste Rahul bhai. BloodBridge AI se baat kar raha hoon.  
    KIMS hospital mein B positive khoon ki zarurat hai — ek 7 saal ke bache ke liye.  
    Kya aap aaj donate kar sakte hain? Haan ke liye 1 dabaiye ya 'haan' boliye."  
    """  
    settings \= get\_settings()  
    memory\_context \= await build\_memory\_context\_for\_llm(donor\['donor\_id'\])  
    \# Call Gemini with donor language, emergency details, and memory\_context  
    \# Return spoken script string

async def make\_vapi\_call(phone: str, donor: dict, emergency: dict, request\_id: str) \-\> dict:  
    """  
    SAFE HOURS CHECK (8 AM – 9 PM IST):  
    now\_ist \= datetime.now(pytz.timezone('Asia/Kolkata'))  
    if now\_ist.hour \< 8 or now\_ist.hour \>= 21:  
        \# Store in voice\_queue for 8 AM delivery  
        return {'status': 'QUEUED', 'reason': 'outside\_safe\_hours'}

    CONSENT CHECK:  
    if not await consent\_service.check\_consent(donor\['donor\_id'\], 'outreach\_voice'):  
        return {'status': 'NO\_CONSENT'}

    SCRIPT GENERATION:  
    script \= await generate\_voice\_script(donor, emergency, memory\_context='')

    BUILD VAPI ASSISTANT CONFIG:  
    assistant \= {  
        'firstMessage': script,  
        'model': {  
            'provider': 'google',  
            'model': 'gemini-1.5-flash',  
            'systemPrompt': (  
                f"You are BloodBridge AI calling a blood donor in India. "  
                f"Language: {donor\['preferred\_language'\]}. "  
                f"Listen for YES/HAAN/HA (confirm) or NO/NAHI/NA (decline). "  
                f"If unclear ask once: 'Aap donate karenge? Please YES ya NO boliye.' "  
                f"After response say thank you and end call."  
            ),  
        },  
        'voice': VAPI\_VOICE\_CONFIG.get(donor.get('language\_code','hi'),  
                                        VAPI\_VOICE\_CONFIG\['en'\]),  
        'endCallMessage': 'Shukriya. BloodBridge AI. Dhanyavaad.',  
    }

    MAKE VAPI CALL:  
    async with httpx.AsyncClient(timeout=10.0) as client:  
        response \= await client.post(  
            VAPI\_CALL\_ENDPOINT,  
            headers={  
                'Authorization': f'Bearer {settings.VAPI\_API\_KEY}',  
                'Content-Type': 'application/json',  
            },  
            json={  
                'phoneNumberId': settings.VAPI\_PHONE\_NUMBER\_ID,  
                'customer': {'number': phone},  
                'assistant': assistant,  
                'metadata': {  
                    'request\_id': request\_id,  
                    'donor\_id': donor\['donor\_id'\],  
                    'chain\_action': 'donation\_request'  
                }  
            }  
        )  
    if response.status\_code \== 201:  
        call\_data \= response.json()  
        return {'status': 'INITIATED', 'call\_id': call\_data\['id'\]}  
    else:  
        return {'status': 'FAILED', 'error': response.text}  
    """  
\`\`\`

CREATE Vapi webhook handler in api/webhooks.py:

\`\`\`python  
POST /webhook/vapi/call-result:  
    """  
    WEBHOOK SECURITY:  
    from core.security import verify\_vapi\_webhook  
    if settings.APP\_ENV \== 'production':  
        if not verify\_vapi\_webhook(request, settings.VAPI\_WEBHOOK\_SECRET):  
            raise HTTPException(status\_code=403)

    Vapi sends JSON body with:  
    \- message.type: 'end-of-call-report'  
    \- message.call.id: call\_id  
    \- message.transcript: full conversation transcript  
    \- message.summary: call summary  
    \- message.metadata: {request\_id, donor\_id, chain\_action}

    KEYWORD NLU — run against message.transcript:  
    YES\_KEYWORDS \= \['yes','haan','ha','ji haan','okay','ok','thik','aane','aamaa','1','haa'\]  
    NO\_KEYWORDS  \= \['no','nahi','na','nahi aata','illay','illai','2','nako'\]

    transcript\_lower \= body\['message'\]\['transcript'\].lower()  
    is\_yes \= any(kw in transcript\_lower for kw in YES\_KEYWORDS)

    If YES:  
        eligibility re-check (same as Telegram YES handler)  
        if eligible: mark chain CONFIRMED → gamification trigger  
        else: mark DECLINED (eligibility\_failed) → chain repair  
    If NO:  
        mark chain DECLINED → chain repair  
    If unclear (neither keyword found):  
        mark as timeout → chain repair  
      
    Broadcast WebSocket {type:'voice\_call\_result', donor\_id, result}  
    """  
\`\`\`

CREATE agents/voice.py — \`async def voice\_agent(state)\`:  
\`\`\`python  
async def voice\_agent(state):  
    for chain\_node in state\['chain'\]:  
        if chain\_node\['status'\] \== 'ALERTED' and chain\_node.get('phone'):  
            donor \= await get\_donor(chain\_node\['donor\_id'\])  
            result \= await make\_vapi\_call(  
                phone=chain\_node\['phone'\],  
                donor=donor,  
                emergency={'blood\_type': state\['blood\_type'\], 'hospital\_name': state\['hospital\_name'\]},  
                request\_id=state\['request\_id'\]  
            )  
            if result\['status'\] \== 'INITIATED':  
                \# Update chain status='VOICE' (shows 📞 in dashboard)  
                await update\_chain\_status(state\['request\_id'\], chain\_node\['donor\_id'\], 'VOICE')  
                \# Broadcast WebSocket {type:'voice\_call\_active', donor\_id, donor\_name}  
                await ws\_manager.broadcast('voice\_call\_active', {  
                    'donor\_id': chain\_node\['donor\_id'\],  
                    'donor\_name': chain\_node\['donor\_name'\]  
                })  
            elif result\['status'\] \== 'QUEUED':  
                logging.info(f"Voice call queued for {chain\_node\['donor\_id'\]} — outside safe hours")  
            elif result\['status'\] \== 'NO\_CONSENT':  
                logging.info(f"Voice call skipped — no consent: {chain\_node\['donor\_id'\]}")  
\`\`\`

\---

\#\#\# PROMPT P4-E — SMS Fallback Service \[NEW\]

\*\*What this builds:\*\* Twilio SMS for donors with no Telegram. DLT-compliant for India.  
10-language templates under 160 chars each.  
\*\*Dependencies:\*\* P1-A (Twilio config), P5-E (consent check)  
\*\*Files created:\*\* services/sms\_service.py

\---

You are building the SMS fallback service for BloodBridge AI.

INDIA CONTEXT: Commercial SMS requires DLT (Distributed Ledger Technology) registration.  
Sender ID and template must be pre-registered with TRAI DLT portal.  
Hackathon: register "BLOODBR" sender ID \+ one English template on Airtel/Jio DLT.  
Development mode: skip DLT headers for testing.

NOTE: Twilio is kept ONLY for SMS (DLT compliance). Voice is handled by Vapi.ai.

CREATE services/sms\_service.py:

\`\`\`python  
SMS\_TEMPLATES \= {  
    'hi': "BloodBridge: {hospital} mein {blood\_type} blood ki zarurat hai. Donate karen? Reply YES. \-BloodBridge",  
    'te': "BloodBridge: {hospital} lo {blood\_type} blood avasaram. Donate chestagara? Reply YES.",  
    'ta': "BloodBridge: {hospital} ல {blood\_type} blood தேவை. Donate செய்க Reply YES.",  
    'en': "BloodBridge Alert: {blood\_type} blood needed urgently at {hospital}. Reply YES to confirm.",  
    'kn': "BloodBridge: {hospital} ನಲ್ಲಿ {blood\_type} ರಕ್ತ ಬೇಕು. Donate ಮಾಡಿ? Reply YES.",  
    'ml': "BloodBridge: {hospital}ൽ {blood\_type} രക്തം ആവശ്യം. Reply YES.",  
    'mr': "BloodBridge: {hospital} मध्ये {blood\_type} रक्त हवे. Donate कराल? Reply YES.",  
    'bn': "BloodBridge: {hospital}এ {blood\_type} রক্ত চাই। Reply YES.",  
    'gu': "BloodBridge: {hospital}માં {blood\_type} blood જોઈએ. Reply YES.",  
    'pa': "BloodBridge: {hospital}ਵਿੱਚ {blood\_type} ਖੂਨ ਚਾਹੀਦਾ। Reply YES.",  
}

class SMSService:  
    async def send\_donation\_request(phone, donor\_id, language, blood\_type, hospital, request\_id) \-\> dict:  
        \# 1\. consent\_service.check\_consent(donor\_id, 'outreach\_sms') — return no\_consent if fails  
        \# 2\. Build message from template  
        \# 3\. Twilio client.messages.create(to, from\_=TWILIO\_DLT\_SENDER\_ID, body, messaging\_service\_sid if prod)  
        \# 4\. Update blood\_chains status='SMS', response\_method='sms'  
        \# 5\. Return {success:bool, sid:str, error:str|None}

    async def handle\_incoming\_sms(from\_number: str, body: str) \-\> dict:  
        YES\_KEYWORDS \= \['yes','haan','ha','ji','ok','okay','1','aane','aamaa','aahe'\]  
        NO\_KEYWORDS  \= \['no','nahi','na','nai','illay','2','nako'\]  
        \# Find donor by phone → process same as Telegram YES/NO handler (with eligibility re-check)  
        \# Return TwiML SMS reply  
\`\`\`

POST /webhook/twilio/sms in api/webhooks.py:  
\`\`\`python  
\# Twilio signature verification for SMS (is\_twilio\_ip check)  
\# Handle incoming SMS reply → sms\_service.handle\_incoming\_sms → TwiML response  
\`\`\`

\---

\#\# PHASE 5 — ENGAGEMENT & CONTINUITY

\---

\#\#\# PROMPT P5-A — XGBoost Churn Predictor \+ Daily Batch

\*\*What this builds:\*\* Churn prediction system running nightly, identifying at-risk donors  
3 weeks early and dispatching tiered interventions.  
\*\*Dependencies:\*\* P1-D (models pre-trained)  
\*\*Files created:\*\* ml/churn\_predictor.py, services/churn\_batch.py

\---

CREATE ml/churn\_predictor.py:

\`\`\`python  
FEATURES \= \['days\_since\_donation','response\_time\_decay','missed\_alerts','avg\_response\_lag',  
            'kell\_negative\_flag','city\_blood\_scarcity\_score','badge\_count','chain\_position\_avg'\]

class ChurnPredictor:  
    def predict\_churn(donor) \-\> dict:  
        \# Returns: {churn\_score, churn\_risk, top\_risk\_factor}

    def predict\_batch(donors) \-\> list\[dict\]:  
        \# numpy vectorized, 500 donors \<50ms

    def \_extract\_features(self, donor) \-\> np.ndarray: ...

    def get\_risk\_tier(churn\_score) \-\> Literal\['CRITICAL','HIGH','MEDIUM','LOW'\]: ...

    def explain\_top\_risk\_factor(donor) \-\> str: ...  
\`\`\`

CREATE services/churn\_batch.py — \`async def run\_nightly\_churn\_batch()\`:  
1\. Fetch all active donors (batch 500\)  
2\. ChurnPredictor.predict\_batch()  
3\. Bulk update churn\_score \+ churn\_risk in Supabase  
4\. Dispatch:  
   \- CRITICAL (\>0.75): trigger VoiceAgent via Vapi.ai  
   \- HIGH (\>0.50): Gemini personalized outreach → Telegram  
   \- MEDIUM (\>0.25): unlock next SVD challenge → send notification  
   \- LOW: no action  
5\. Log: "Churn: 500 scored | CRITICAL:12 | HIGH:35 | MEDIUM:78 | LOW:375"

\---

\#\#\# PROMPT P5-B — Gamification Engine

\*\*What this builds:\*\* Complete gamification — 6 badge types, city leaderboard,  
badge notifications in all 10 languages.  
\*\*Dependencies:\*\* P1-B (gamification tables), P4-A (Telegram)  
\*\*Files created:\*\* services/gamification\_service.py

\---

CREATE services/gamification\_service.py:

\`\`\`python  
BADGES \= {  
    'blood\_starter': {  
        'emoji': '🌱', 'threshold\_type': 'donation\_count', 'threshold': 1,  
        'message\_hi': 'Shukriya\! Pehli baar donate kiya\! 🌱',  
        'message\_te': 'ధన్యవాదాలు\! మొదటిసారి donate చేసారు\! 🌱',  
        'message\_en': 'Thank you\! Your first donation starts an incredible journey\! 🌱'  
    },  
    'life\_saver':    {'emoji': '❤️', 'threshold': 5,  'message\_hi': '5 zindagiyan bachayi\! ❤️'},  
    'blood\_hero':    {'emoji': '🦸', 'threshold': 10, 'message\_hi': 'Blood Hero\! 10 donate karke itihash\! 🦸'},  
    'rare\_guardian': {'emoji': '💎', 'condition': 'kell\_negative AND donation\_count\>=3'},  
    'city\_champion': {'emoji': '🏆', 'condition': 'rank\_1\_in\_city'},  
    'crisis\_hero':   {'emoji': '⚡', 'condition': 'confirmed within 2 hours of CRITICAL alert'},  
}

async def check\_and\_award\_badges(donor\_id, donor) \-\> list\[str\]:  
    """Check all rules, award new badges, insert gamification table, update donor\_memory"""

async def send\_badge\_notification(donor\_id, badge\_name, language):  
    """Telegram notification in donor's language"""

async def update\_leaderboard(city, donor\_id, lives\_saved):  
    """Supabase RANK() OVER (PARTITION BY city ORDER BY lives\_saved DESC) → upsert leaderboard\_cache"""

async def get\_city\_leaderboard(city: str) \-\> list\[dict\]:  
    """Top-10 from leaderboard\_cache (fast, pre-computed)"""

async def get\_next\_badge\_progress(donor: dict) \-\> dict:  
    """Returns: {current\_badge, next\_badge, current, target, remaining}"""  
\`\`\`

\---

\#\#\# PROMPT P5-C — SVD Challenge Recommender

\*\*What this builds:\*\* Collaborative filtering for personalized donor challenges.  
\*\*Dependencies:\*\* P1-D (SVD model trained)  
\*\*Files created:\*\* ml/challenge\_recommender.py

\---

CREATE ml/challenge\_recommender.py:

\`\`\`python  
CHALLENGES \= {  
    'double\_donor', 'referral\_hero', 'city\_drive', 'streak\_keeper', 'midnight\_hero',  
    'rare\_blood\_run', 'young\_saver', 'multilingual', 'comeback\_kid', 'speed\_response'  
}  \# 10 challenge types with name \+ description \+ emoji

class ChallengeRecommender:  
    MODEL\_PATH \= 'ml/models/svd\_challenges.joblib'

    def recommend\_challenges(donor\_id, top\_k=3) \-\> list\[dict\]:  
        """  
        Algorithm: latent vector → cosine similarity → similar donors → their completed challenges  
        Cold start: profile-based vector if donor not in training data  
        Exclude already-completed challenges  
        Returns: \[{challenge\_id, name, emoji, relevance\_score}\]  
        """

async def unlock\_challenge\_for\_donor(donor\_id: str):  
    """Get recommendation → send Telegram challenge unlock notification"""  
\`\`\`

\---

\#\#\# PROMPT P5-D — Gemini Impact Story Generator

\*\*What this builds:\*\* Personalized 3-sentence emotional story after confirmed donation.  
In donor's language. Delayed 2 hours for reflection effect.  
\*\*Dependencies:\*\* P4-C, P4-A  
\*\*Files created:\*\* services/impact\_story.py

\---

CREATE services/impact\_story.py:

\`\`\`python  
LANGUAGE\_MAP \= {  
    'hi':'Hindi','te':'Telugu','ta':'Tamil','en':'English',  
    'kn':'Kannada','ml':'Malayalam','mr':'Marathi','bn':'Bengali','gu':'Gujarati','pa':'Punjabi'  
}

async def generate\_impact\_story(donor: dict, patient: dict, language: str) \-\> str:  
    """  
    Gemini 1.5 Flash — 3 sentences max. Personal, authentic, NOT corporate.  
    Injects memory context: await build\_memory\_context\_for\_llm(donor\['donor\_id'\])  
    Anonymized (no patient last name/patient\_id in story). In correct script.  
    Example Hindi:  
    "Aapke ek baar dene se ek 7 saal ke Aarav ki 142vi transfusion poori hui.  
    Uski maa ne kaha — 'ek anjaana farishta tha jo aya aur chala gaya.'  
    Woh farishta aap hain, {donor.name} bhai."  
    Store in donor\_memory.impact\_story  
    """

async def send\_impact\_story\_via\_telegram(donor\_id: str, story: str):  
    """  
    2-hour delayed send (not immediate — feels like a reflection moment)  
    APScheduler: add\_job(send, 'date', run\_date=now+timedelta(hours=2), args=\[donor\_id,story\])  
    """  
\`\`\`

\---

\#\#\# PROMPT P5-E — Consent Management Service \+ DPDP 2023 \[NEW\]

\*\*What this builds:\*\* India's Digital Personal Data Protection Act 2023 compliance layer.  
Consent collection, revocation, audit trail, right to erasure.  
\*\*Dependencies:\*\* P1-B (consent\_records table)  
\*\*Files created:\*\* services/consent\_service.py

\---

You are building the DPDP 2023 consent management service for BloodBridge AI.

LEGAL: India's DPDP Act 2023 requires explicit consent for personal data processing,  
right to withdraw anytime, right to erasure, and maintained consent records.  
Our system processes blood type, hemoglobin, antibody flags, phone — all health-adjacent.  
Special category data requires explicit consent (Section 9).

CREATE services/consent\_service.py:

\`\`\`python  
import hashlib

\# Consent texts shown to donors in each language before any data is stored  
CONSENT\_TEXTS: dict \= {  
    'hi': "BloodBridge AI aapka naam, phone number, aur blood type store karega taaki "  
          "aapko blood donation ke liye contact kar sake. Kya aap agree karte hain? "  
          "DPDP Act 2023 ke anusar aap kabhi bhi consent wapas le sakte hain. Reply HAAN ya NA.",  
    'te': "BloodBridge AI మీ పేరు, ఫోన్ నంబర్, బ్లడ్ టైప్ స్టోర్ చేస్తుంది. "  
          "Blood donation కోసం మిమ్మల్ని contact చేయడానికి. మీరు agree అవుతారా? "  
          "DPDP Act 2023 కింద మీరు ఎప్పుడైనా consent తీసుకోవచ్చు. Reply HAAN లేదా NA.",  
    'ta': "BloodBridge AI உங்கள் பெயர், தொலைபேசி எண், இரத்த வகை சேமிக்கும். "  
          "இரத்த தானத்திற்கு உங்களை தொடர்புகொள்ள. ஒப்புக்கொள்கிறீர்களா? "  
          "DPDP Act 2023 படி எப்போதும் சம்மதத்தை திரும்பப் பெறலாம். Reply HAAN அல்லது NA.",  
    'en': "BloodBridge AI will store your name, phone number, and blood type to contact "  
          "you for blood donation requests. Do you agree? Under DPDP Act 2023 you can "  
          "withdraw consent at any time. Reply YES or NO.",  
    'kn': "BloodBridge AI ನಿಮ್ಮ ಹೆಸರು, ಫೋನ್ ನಂಬರ್, ರಕ್ತದ ಗುಂಪು ಸಂಗ್ರಹಿಸುತ್ತದೆ. "  
          "ರಕ್ತ ದಾನಕ್ಕಾಗಿ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಲು. ಒಪ್ಪಿಗೆ ಇದೆಯೇ? Reply HAAN ಅಥವಾ NA.",  
    'ml': "BloodBridge AI നിങ്ങളുടെ പേര്, ഫോൺ നമ്പർ, രക്ത ഗ്രൂപ്പ് സ്റ്റോർ ചെയ്യും. "  
          "രക്ത ദാനത്തിനായി നിങ്ങളെ ബന്ധപ്പെടാൻ. സമ്മതിക്കുന്നുവോ? Reply HAAN അല്ലെങ്കിൽ NA.",  
    'mr': "BloodBridge AI तुमचे नाव, फोन नंबर, रक्त प्रकार साठवेल. "  
          "रक्तदानासाठी तुमच्याशी संपर्क साधण्यासाठी. तुम्ही सहमत आहात का? Reply HAAN किंवा NA.",  
    'bn': "BloodBridge AI আপনার নাম, ফোন নম্বর, রক্তের গ্রুপ সংরক্ষণ করবে। "  
          "রক্ত দানের জন্য আপনাকে যোগাযোগ করতে। সম্মতি দেন? Reply HAAN বা NA.",  
    'gu': "BloodBridge AI તમારું નામ, ફોન નંબર, બ્લડ ટાઇપ સ્ટોર કરશે. "  
          "Blood donation માટે તમારો સંપર્ક કરવા. સંમતિ આપો? Reply HAAN અથવા NA.",  
    'pa': "BloodBridge AI ਤੁਹਾਡਾ ਨਾਮ, ਫ਼ੋਨ ਨੰਬਰ, ਬਲੱਡ ਟਾਈਪ ਸਟੋਰ ਕਰੇਗਾ. "  
          "ਖੂਨ ਦਾਨ ਲਈ ਤੁਹਾਡੇ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ. ਕੀ ਤੁਸੀਂ ਸਹਿਮਤ ਹੋ? Reply HAAN ਜਾਂ NA.",  
}

\# SHA256 hash of each consent text — stored in consent\_records for audit trail  
CONSENT\_TEXT\_HASHES: dict \= {  
    lang: hashlib.sha256(text.encode('utf-8')).hexdigest()  
    for lang, text in CONSENT\_TEXTS.items()  
}

class ConsentService:

    async def grant\_consent(donor\_id, consent\_types: list\[str\], channel, language, ip\_hash=None) \-\> bool:  
        """INSERT consent\_records for each type. Update donor summary flags.  
        consent\_text\_hash \= CONSENT\_TEXT\_HASHES.get(language, CONSENT\_TEXT\_HASHES\['en'\])  
        Used during /register, /start, and staff bulk import."""

    async def revoke\_consent(donor\_id, consent\_type='all') \-\> bool:  
        """INSERT revocation record. Stop outreach immediately.  
        If revoking 'data\_storage': set donor.is\_active=False"""

    async def check\_consent(donor\_id, consent\_type) \-\> bool:  
        """Fast check — latest record for donor+type. True if action='granted'.  
        SELECT action FROM consent\_records  
        WHERE donor\_id=$1 AND consent\_type=$2  
        ORDER BY created\_at DESC LIMIT 1"""

    async def get\_consent\_summary(donor\_id) \-\> dict:  
        """All consent statuses for dashboard display and /consent command"""

    async def erase\_donor\_data(donor\_id, requested\_by) \-\> dict:  
        """RIGHT TO ERASURE — DPDP Section 12\.  
        1\. Check no active IN\_PROGRESS emergency  
        2\. Delete: donor\_memory, gamification, consent\_records, donor\_verifications  
        3\. Anonymize donor (keep: donation\_count, blood\_type for aggregate stats):  
           UPDATE donors SET name='\[DELETED\]', phone=NULL, telegram\_chat\_id=NULL,  
           lat=NULL, lng=NULL, is\_active=FALSE WHERE donor\_id=$1  
        4\. Log to erasure\_log table (retained 7 years per DPDP)  
        Returns: {success, donor\_id, erased\_at}"""

    async def export\_donor\_data(donor\_id) \-\> dict:  
        """RIGHT TO ACCESS — DPDP Section 11\. All stored data, structured format."""

consent\_service \= ConsentService()  \# module-level singleton  
\`\`\`

New API endpoints in api/donors.py:  
\`\`\`  
GET  /api/donors/{id}/consent          → consent summary  
POST /api/donors/{id}/consent/revoke   → revoke {type: 'all'|'sms'|'voice'|...}  
DELETE /api/donors/{id}/data           → right to erasure  
GET  /api/donors/{id}/my-data          → right to access / data export  
\`\`\`

\---

\#\# PHASE 6 — API \+ REAL-TIME

\---

\#\#\# PROMPT P6-A — FastAPI REST Endpoints (All Routes) \[UPDATED\]

\*\*What this builds:\*\* All REST endpoints consumed by Next.js frontend. Matches lib/api.ts exactly.  
Includes new eligibility check, schedule endpoints, and real analytics computation.  
\*\*Dependencies:\*\* All Phase 1-5  
\*\*Files created:\*\* api/emergency.py, api/donors.py, api/patients.py, api/blood\_banks.py, api/admin.py

\---

You are building all FastAPI REST endpoints for BloodBridge AI.  
All responses MUST match TypeScript interfaces in lib/api.ts exactly.

CREATE api/emergency.py:  
\`\`\`  
GET  /api/emergencies              → list\[Emergency\] (active, with chain)  
GET  /api/emergencies/{id}         → Emergency  
POST /api/emergencies              → {requestId} — validates → creates record → run\_emergency\_pipeline() as BackgroundTask  
                                     Apply @limiter.limit("5/hour")  
                                     Check idempotency key before creating  
POST /api/emergencies/{id}/confirm → {success: bool}  
GET  /api/emergencies/{id}/chain   → list\[ChainNode\]  
GET  /api/emergencies/{id}/trace   → AgentTrace  
\`\`\`

CREATE api/donors.py:  
\`\`\`  
GET  /api/donors                   → list\[Donor\] (sortBy, riskFilter query params)  
GET  /api/donors/{id}              → Donor  
GET  /api/donors/{id}/eligibility  → eligibility check dict  
POST /api/donors/{id}/voice        → {callSid: str} — @limiter.limit("10/hour")  
                                     NOTE: now calls voice\_service.make\_vapi\_call() internally  
                                     Returns Vapi call\_id as callSid for frontend display  
POST /api/donors/{id}/outreach     → {messageId: str}  
GET  /api/leaderboard              → list\[LeaderboardEntry\] (city query param)  
GET  /api/donors/{id}/consent      → consent summary  
POST /api/donors/{id}/consent/revoke → {success: bool}  
DELETE /api/donors/{id}/data       → {success: bool} (DPDP erasure)  
GET  /api/donors/{id}/my-data      → donor data export  
POST /api/donors/bulk-import       → import report — @limiter.limit("3/day")  
\`\`\`

CREATE api/patients.py:  
\`\`\`  
GET  /api/patients/{id}            → PatientProfile  
\`\`\`

CREATE api/blood\_banks.py:  
\`\`\`  
GET  /api/blood-banks              → list\[BloodBank\] (city, bloodType params)  
POST /api/blood-banks/refresh      → {success: bool, updated\_at: str}  
\`\`\`

CREATE api/admin.py:  
\`\`\`  
GET  /api/health                   → real latency checks to all 9 services including Vapi.ai  
GET  /api/traces                   → list\[AgentTrace\] (last 5\)  
GET  /api/analytics                → REAL computed EngagementMetrics (not mock):  
                                     Chain success rate, avg response time,  
                                     churn distribution, language distribution,  
                                     proactive vs emergency ratio  
POST /api/models/retrain           → {jobId: str}  
GET  /api/config                   → current agent config from Supabase  
PUT  /api/config                   → {success: bool}  
GET  /api/staff                    → list\[Staff\]  
POST /api/staff                    → {success: bool}  
DELETE /api/staff/{username}       → {success: bool}  
GET  /api/schedule                 → list\[ScheduleEntry\] (days, status params)  
POST /api/schedule                 → create schedule entry  
\`\`\`

RULES: Pydantic response models, async DB calls, FastAPI Depends() for auth,  
HTTPException with proper status codes, BackgroundTasks for pipeline invocation.

\---

\#\#\# PROMPT P6-B — WebSocket Endpoint \+ Live Chain Broadcasting

\*\*What this builds:\*\* FastAPI WebSocket server pushing real-time events to Next.js dashboard.  
\*\*Dependencies:\*\* P6-A  
\*\*Files created:\*\* api/websocket.py, core/ws\_manager.py

\---

CREATE core/ws\_manager.py:

\`\`\`python  
class ConnectionManager:  
    active\_connections: list\[WebSocket\] \= \[\]

    async def connect(ws): await ws.accept(); append  
    def disconnect(ws): remove  
    async def broadcast(event\_type, data):  
        message \= json.dumps({type:event\_type, data:data, timestamp:utcnow})  
        \# For each connection: send\_text(message), remove dead connections

ws\_manager \= ConnectionManager()  \# Singleton — imported by all agents  
\`\`\`

Event types (matching useEmergencySocket in frontend):  
\`\`\`  
chain\_update, new\_emergency, chain\_break, voice\_call\_active,  
emergency\_completed, blood\_stock\_update, badge\_awarded, chain\_repaired  
\`\`\`

CREATE api/websocket.py:  
\`\`\`python  
@app.websocket("/ws/emergency")  
\# → accept connection → send initial\_state with active emergencies  
\# → keep alive: ping/pong every 30s  
\# → handle WebSocketDisconnect  
\`\`\`

\---

\#\#\# PROMPT P6-C — ntfy.sh Staff Push Alerts

\*\*What this builds:\*\* Zero-cost push notifications for staff. Instant alerts for chain breaks,  
CRITICAL patients, and escalations.  
\*\*Dependencies:\*\* P6-A  
\*\*Files created:\*\* services/alerts.py

\---

CREATE services/alerts.py:

\`\`\`python  
ALERT\_CONFIGS \= {  
    'critical':    {'priority': 5, 'tags': \['rotating\_light','drop\_of\_blood'\]},  
    'chain\_break': {'priority': 4, 'tags': \['warning','chains'\]},  
    'escalation':  {'priority': 4, 'tags': \['hospital','warning'\]},  
    'success':     {'priority': 2, 'tags': \['white\_check\_mark','drop\_of\_blood'\]},  
    'info':        {'priority': 2, 'tags': \['information\_source'\]},  
}

async def send\_alert(title, message, level='info', actions=None):  
    """httpx.AsyncClient POST to ntfy.sh/{NTFY\_TOPIC} with headers.  
    Actions: \[{view, label, url}\] for dashboard deeplink button"""

\# Pre-built functions:  
async def alert\_critical\_patient(patient\_id, blood\_type, hospital): ...  
async def alert\_chain\_break(patient\_id, position): ...  
async def alert\_escalation(patient\_id, blood\_banks): ...  
async def alert\_success(patient\_id, donor\_name): ...  
async def alert\_lora\_received(gateway\_id, rssi, patient\_id): ...  
\`\`\`

\---

\#\#\# PROMPT P6-D — Bulk Donor Import API \[NEW\]

\*\*What this builds:\*\* CSV import for Blood Warriors' existing 3,855 donor database.  
Validates, deduplicates, builds Neo4j edges for imported donors.  
\*\*Dependencies:\*\* P2-A (antigen scorer), P5-E (consent service)  
\*\*Files created:\*\* api/donors.py addition

\---

You are building the bulk donor import API for BloodBridge AI.

ADD to api/donors.py:

\`\`\`  
POST /api/donors/bulk-import (Admin only, @limiter.limit("3/day")):  
    file: UploadFile — CSV  
    grant\_consent: bool query param — True if offline consent already obtained

Required CSV columns: name, phone, blood\_type, city  
Optional: ward, kell\_negative, preferred\_language, donation\_count,  
          duffy\_negative, kidd\_negative, hemoglobin, last\_donation\_date

Processing steps:  
  1\. Read \+ decode CSV (handle UTF-8 and UTF-8-BOM)  
  2\. Validate headers — 422 if required columns missing  
  3\. For each row:  
     a. Validate blood\_type (must be A+/A-/B+/B-/AB+/AB-/O+/O-)  
     b. Normalize phone (+91 prefix for India, strip spaces)  
     c. Duplicate check: SELECT 1 FROM donors WHERE phone=normalized\_phone  
        → add to skipped\_duplicates if exists  
     d. donor\_id \= 'D-IMP-' \+ hashlib.md5(phone.encode()).hexdigest()\[:6\]  
     e. Add to insert\_batch  
  4\. Bulk insert in batches of 50  
  5\. If grant\_consent=True: consent\_service.grant\_consent() for each imported donor  
     channel='staff\_manual', note='offline\_consent\_provided'  
  6\. Create donor\_verifications records for antigen flags in CSV (verification\_type='staff\_manual')  
  7\. Background task: build\_neo4j\_edges\_for\_new\_donors(new\_donor\_ids)  
  8\. Return import report:  
     { imported, skipped\_duplicates, skipped\_invalid, consent\_granted,  
       neo4j\_edge\_build:'in\_progress', errors:\[{row, phone, reason}\], import\_id }

async def build\_neo4j\_edges\_for\_new\_donors(donor\_ids):  
    \# Background task. For each new donor × each patient with matching blood\_type:  
    \# compute antigen score → create COMPATIBLE\_WITH edge if \> 0\.  
    \# Log every 50 donors. Update import\_jobs Supabase table for progress polling.

GET /api/donors/import-status/{import\_id} → {status, donors\_processed, edges\_created}  
\`\`\`

\---

\#\# PHASE 7 — EXTERNAL INTEGRATION

\---

\#\#\# PROMPT P7-A — e-RaktKosh Scraper \+ Supabase Cache

\*\*What this builds:\*\* Scraper for India's national blood bank portal.  
15-minute Supabase cache. Mock data fallback for demo safety.  
\*\*Dependencies:\*\* P6-A  
\*\*Files created:\*\* services/blood\_bank\_scraper.py

\---

CREATE services/blood\_bank\_scraper.py:

\`\`\`python  
MOCK\_BLOOD\_BANKS \= \[  
    \# 8 Hyderabad blood banks pre-populated:  
    \# Nizam's Institute, Apollo Jubilee, KIMS Secunderabad, Care Hospitals,  
    \# Yashoda, Global Hospital, Rainbow Children's, Continental Hospital  
    \# Each with realistic units per blood type \+ lat/lng \+ contact \+ distance\_km  
\]

async def get\_blood\_banks\_for\_city(city, blood\_type=None) \-\> list\[dict\]:  
    \# Priority: 1\) Supabase cache (\< 15 min TTL) → 2\) scrape e-RaktKosh → 3\) MOCK\_BLOOD\_BANKS

async def scrape\_eraktkosh(city) \-\> list\[dict\]:  
    \# httpx timeout=10s, User-Agent='Mozilla/5.0'  
    \# URL: eraktkosh.in portal  
    \# BeautifulSoup4 parse blood unit table  
    \# Return \[\] on any exception (triggers mock fallback)

async def update\_neo4j\_blood\_banks(banks):  
    \# MERGE BloodBank nodes with fresh unit counts

async def get\_nearest\_banks\_with\_stock(city, blood\_type) \-\> list\[dict\]:  
    """Used by InventoryAgent. Banks with \>0 units sorted by distance."""  
\`\`\`

\---

\#\# PHASE 8 — DEPLOYMENT \+ SECURITY

\---

\#\#\# PROMPT P8-A — Render.com Deployment Configuration

\*\*What this builds:\*\* Complete Render.com deployment config, DEPLOY.md checklist.  
\*\*Dependencies:\*\* All Phase 1-7  
\*\*Files created:\*\* render.yaml, DEPLOY.md

\---

CREATE render.yaml:  
\`\`\`yaml  
type: web  
name: bloodbridge-api  
env: python  
plan: free  
buildCommand: |  
  pip install \-r requirements.txt  
  python data/generate\_synthetic.py  
startCommand: uvicorn main:app \--host 0.0.0.0 \--port $PORT  
healthCheckPath: /health  
autoDeploy: true  
envVars:  
  \- key: PYTHON\_VERSION  
    value: 3.11.0  
  \- key: APP\_ENV  
    value: production  
\# All secrets via Render dashboard, not render.yaml  
\`\`\`

CREATE DEPLOY.md with pre-deploy checklist:  
\`\`\`  
□ python data/generate\_synthetic.py — train models \+ generate seed data  
□ python data/seed\_supabase.py — 500 donors \+ 50 patients  
□ python data/seed\_neo4j.py — graph \+ COMPATIBLE\_WITH edges  
□ verify: ls ml/models/ → 3 .joblib files  
□ test: uvicorn main:app → curl localhost:8000/health  
□ Set Telegram webhook: POST .../setWebhook?url={RENDER\_URL}/webhook/telegram\&secret\_token={SECRET}  
□ Set Vapi.ai webhook URL in Vapi dashboard → {RENDER\_URL}/webhook/vapi/call-result  
□ Set DLT template IDs for SMS (Twilio SMS — if SMS needed for demo)  
□ Add VAPI\_API\_KEY and VAPI\_PHONE\_NUMBER\_ID to Render environment vars  
\`\`\`

\---

\#\#\# PROMPT P8-B — Complete Integration Test Script \+ Demo Script

\*\*What this builds:\*\* E2E test validating every component. Demo script for pitch day.  
\*\*Dependencies:\*\* All Phase 1-8  
\*\*Files created:\*\* tests/test\_e2e\_pipeline.py, demo\_run.py

\---

CREATE tests/test\_e2e\_pipeline.py (pytest-asyncio, mock Groq/Gemini/Vapi/Twilio):

\`\`\`python  
\# test\_full\_emergency\_pipeline():  
\#     Asserts: patient loaded, eligible\_donors\>0, scored\_donors\>0,  
\#     urgency in \[CRITICAL/HIGH/ROUTINE\], chain=8 donors, positions unique 1-8,  
\#     all antigen\_scores 0-1, neo4j\_matching \< 200ms, WS events broadcast

\# test\_antigen\_scorer\_clinical\_accuracy():  
\#     Kell-pos donor \+ Anti-Kell patient → 0.65  
\#     All-safe donor \+ multi-antibody patient → 1.0  
\#     Blood type mismatch → 0.0  
\#     Duffy+Kidd risk → 0.55

\# test\_chain\_repair(): donor declines → repair activates next donor

\# test\_proactive\_scheduler():  
\#     Insert patient due in 4 days → run job → request with request\_mode='proactive'  
\#     Verify 'warm\_advance' tone, schedule status='OUTREACH\_STARTED', request\_id set

\# test\_consent\_flow():  
\#     No consent → donor skipped in outreach (in non\_consented\_donors)  
\#     Grant consent → donor IS alerted  
\#     Revoke → skipped again

\# test\_outreach\_memory\_injection():  
\#     Verify build\_memory\_context\_for\_llm() is called before Groq prompt for each donor  
\#     Memory context appears in generated message (donor name reference)

\# test\_vapi\_voice\_call():  
\#     Mock Vapi POST endpoint → returns {id: 'vapi-call-123'}  
\#     Chain status updates to 'VOICE'  
\#     POST /webhook/vapi/call-result with 'haan' in transcript → chain CONFIRMED  
\#     POST /webhook/vapi/call-result with 'nahi' in transcript → chain DECLINED \+ repair

\# test\_lora\_ingest():  
\#     encode\_lora\_packet → POST /api/lora/ingest → request created → pipeline started  
\#     Invalid checksum → 422 response

\# test\_sms\_fallback():  
\#     Donor with phone but no telegram\_chat\_id → channel='sms'  
\#     Simulate YES reply via /webhook/twilio/sms → chain CONFIRMED

\# test\_bulk\_import():  
\#     Valid CSV 10 donors → 10 imported, neo4j edge build triggered  
\#     Same CSV again → 10 skipped\_duplicates, 0 imported  
\#     Invalid blood\_type row → error in report

\# test\_consent\_text\_hashes():  
\#     CONSENT\_TEXT\_HASHES has entry for all 10 languages  
\#     Hash is SHA256 hexdigest of correct length (64 chars)  
\#     Stored in consent\_records.consent\_text\_hash after grant  
\`\`\`

CREATE demo\_run.py — standalone demo script:  
\`\`\`  
Prints beautiful formatted trace showing each agent activating with timings.  
Example output:  
🔴 BLOODBRIDGE AI — DEMO RUN  
════════════════════════════  
🚨 Emergency: B+ at KIMS · Patient: P-10234 · Aarav, Age 7  
\[IntakeAgent\]        120ms ✓ Patient loaded — Hgb 4.1 g/dL  
\[EligibilityFilter\]   89ms ✓ 147/312 donors eligible  
\[AntigenScoring\]     156ms ✓ Top: 0.99 (Lakshmi Devi — Kell-safe)  
\[UrgencyScoring\]     203ms ✓ Score: 8.7/10 — CRITICAL  
\[Neo4jMatch\]          78ms ✓ 8-donor chain from graph edges  
\[PlannerAgent\]      1100ms ✓ warm\_urgent tone, Telegram-first \+ donor memory injected  
\[OutreachAgent\]     2340ms ✓ 8 msgs parallel (Hindi/Telugu) with memory context  
\[ChainMonitor\]       5min ⏳ D1 confirmed in 4 min  
\[VoiceAgent\]         \--- ✓ Vapi.ai call initiated for D3 (stale 7min)  
✅ SUCCESS — 1 donor confirmed in 6m 14s  
🏆 Badge: Rahul Kumar — Crisis Hero ⚡  
📖 Impact story scheduled for 2 hours  
\`\`\`

\---

\#\#\# PROMPT P8-C — Security Hardening \[NEW\]

\*\*What this builds:\*\* Webhook verification, rate limiting, IP whitelist, staff auth.  
Completes the security surface.  
\*\*Dependencies:\*\* P1-A (core/security.py stub), P4-A, P4-D  
\*\*Files created:\*\* core/security.py (full implementation)

\---

You are building the security hardening layer for BloodBridge AI.

COMPLETE core/security.py (replace stub):

\`\`\`python  
def verify\_telegram\_webhook(request, secret\_token) \-\> bool:  
    """Compare X-Telegram-Bot-Api-Secret-Token header using hmac.compare\_digest.  
    Returns True in dev if secret\_token not configured."""

def verify\_vapi\_webhook(request, secret) \-\> bool:  
    """Compare X-Vapi-Signature header using hmac.compare\_digest.  
    Returns True if APP\_ENV=development."""

async def verify\_twilio\_sms\_signature(request, auth\_token) \-\> bool:  
    """twilio.request\_validator.RequestValidator.validate(url, params, signature).  
    Used for SMS webhook only. Returns True if APP\_ENV=development."""

def generate\_idempotency\_key(patient\_id, blood\_type, city) \-\> str:  
    """SHA256(f"{patient\_id}:{blood\_type}:{city}")\[:32\]"""

TWILIO\_IP\_RANGES \= \[  
    "54.172.60.0/23","54.244.51.0/24","54.171.127.192/26","103.252.195.0/24",  
    "54.65.63.192/26","54.169.127.128/26","54.252.254.64/26","54.252.253.0/23",  
    "177.71.206.192/26","52.215.127.0/24"  
\]  
def is\_twilio\_ip(ip) \-\> bool:  
    """Check ipaddress.ip\_network CIDR membership — used for Twilio SMS webhooks"""

def hash\_ip(ip) \-\> str:  
    """SHA256(ip)\[:16\] — DPDP-compliant audit logging"""

async def get\_current\_staff(request) \-\> dict:  
    """X-Staff-Token header → lookup staff table auth\_token"""

async def get\_current\_staff\_admin(staff=Depends(get\_current\_staff)) \-\> dict:  
    """Admin role required"""  
\`\`\`

ADD to main.py:  
\`\`\`python  
from slowapi import Limiter, \_rate\_limit\_exceeded\_handler  
from slowapi.util import get\_remote\_address  
from slowapi.errors import RateLimitExceeded

limiter \= Limiter(key\_func=get\_remote\_address)  
app.state.limiter \= limiter  
app.add\_exception\_handler(RateLimitExceeded, \_rate\_limit\_exceeded\_handler)  
\`\`\`

Route rate limits:  
\`\`\`  
POST /api/emergencies      → @limiter.limit("5/hour")  
POST /donors/bulk-import   → @limiter.limit("3/day")  
POST /donors/{id}/voice    → @limiter.limit("10/hour")  
\`\`\`

\---

\#\# PHASE 9 — LORA OFFLINE BRIDGE

\---

\#\#\# PROMPT P9-A — LoRa Offline Bridge \+ Gateway Simulator \[NEW\]

\*\*What this builds:\*\* 8-byte packet protocol for zero-connectivity rural areas. Gateway bridge  
endpoint. Software simulator for demo day. Architecture documentation.  
\*\*Dependencies:\*\* P6-A (emergency creation), P1-A (config)  
\*\*Files created:\*\* api/lora.py, services/lora\_bridge.py, tools/lora\_simulator.py

\---

You are building the LoRa offline bridge for BloodBridge AI.

DEMO STRATEGY: No LoRa hardware available during hackathon.  
Build: complete architecture \+ lora\_simulator.py that sends the same packet over HTTP.  
Run simulator during demo: "LoRa emergency received from rural health post — no internet required"

\*\*━━━ 8-BYTE LORA PACKET PROTOCOL ━━━\*\*  
\`\`\`  
Byte layout (optimised for LoRa SF12 51-byte/packet constraint):  
  \[0\]   blood\_type\_code  — 0=A+, 1=A-, 2=B+, 3=B-, 4=AB+, 5=AB-, 6=O+, 7=O-  
  \[1-3\] patient\_id\_hash  — first 3 bytes of MD5(patient\_id)  
  \[4\]   urgency\_flags    — bit0=CRITICAL, bit1=kell\_negative\_needed,  
                           bit2=paediatric, bit3=antibody\_present  
  \[5\]   city\_code        — 0=Hyderabad, 1=Mumbai, 2=Chennai, 3=Bangalore,  
                           4=Delhi, 5=Kolkata, 6=Pune, 7=rural\_other  
  \[6-7\] checksum         — CRC16/CCITT-FALSE of bytes 0-5  
\`\`\`

Why 8 bytes: multiple redundant retransmits fit within one LoRa transmission window.

CREATE services/lora\_bridge.py:

\`\`\`python  
BLOOD\_TYPE\_CODES \= {0:'A+',1:'A-',2:'B+',3:'B-',4:'AB+',5:'AB-',6:'O+',7:'O-'}  
CITY\_CODES \= {0:'Hyderabad',1:'Mumbai',2:'Chennai',3:'Bangalore',  
              4:'Delhi',5:'Kolkata',6:'Pune',7:'rural\_other'}

def compute\_crc16(data: bytes) \-\> int:  
    """CRC16/CCITT-FALSE algorithm — must match what LoRa gateway hardware uses."""  
    crc \= 0xFFFF  
    for byte in data:  
        crc ^= byte \<\< 8  
        for \_ in range(8):  
            crc \= (crc \<\< 1\) ^ 0x1021 if crc & 0x8000 else crc \<\< 1  
        crc &= 0xFFFF  
    return crc

def decode\_lora\_packet(packet\_bytes: bytes) \-\> dict:  
    """Decode 8-byte packet. Validate CRC16. Return decoded dict.  
    Returns: {blood\_type, patient\_id\_hash, urgency, kell\_negative\_needed,  
              paediatric, antibody\_present, city, checksum\_valid, raw\_hex}"""

def encode\_lora\_packet(blood\_type, patient\_id, urgency, city, flags) \-\> bytes:  
    """Encode to 8-byte packet. Used by lora\_simulator.py."""

async def resolve\_patient\_from\_hash(patient\_id\_hash: str, blood\_type: str) \-\> dict:  
    """SELECT \* FROM patients WHERE LEFT(MD5(patient\_id),6)=hash AND blood\_type=blood\_type"""  
\`\`\`

CREATE api/lora.py:

\`\`\`python  
POST /api/lora/ingest:  
    """Body: {packet\_hex, gateway\_id, rssi}  
    1\. Decode hex → bytes  
    2\. decode\_lora\_packet → check checksum\_valid  
    3\. resolve\_patient\_from\_hash  
    4\. Create emergency\_request  
    5\. run\_emergency\_pipeline() as background task  
    6\. alert\_lora\_received(gateway\_id, rssi, patient\_id)  
    Return: {request\_id, patient\_id, blood\_type, decoded, pipeline:'started'}"""

GET /api/lora/gateways → list of known gateways with last-seen timestamps  
\`\`\`

CREATE tools/lora\_simulator.py (standalone — NOT part of FastAPI):  
\`\`\`python  
"""  
Run: python tools/lora\_simulator.py \--blood B+ \--city rural\_other \--urgency CRITICAL

Simulates a LoRa field device at a rural health post sending emergency packet to API.  
Same packet format as real LoRa gateway would send.  
"""  
import argparse, httpx  
from services.lora\_bridge import encode\_lora\_packet

\# Parse args: \--blood, \--city, \--urgency, \--patient, \--url  
\# Encode packet → packet\_hex  
\# Print: packet details, bytes, blood type, city  
\# httpx.post({url}/api/lora/ingest, json={packet\_hex, gateway\_id:'GW-RURAL-01', rssi:-102})  
\# Print API response \+ "Emergency pipeline started. Check dashboard."  
\`\`\`

\*\*━━━ LORA ARCHITECTURE (include in README) ━━━\*\*  
\`\`\`  
\[Rural field device — RFM95 LoRa module 865 MHz India band\]  
  └─ 8-byte emergency packet, range 15km open terrain, 3-5km forest

        ↓ LoRa RF (no internet required)

\[LoRa Gateway — Raspberry Pi 4 \+ RAK2245 HAT at hospital/taluka office\]  
  └─ Receives packet, validates CRC, POSTs to BloodBridge API via WiFi/4G

        ↓ HTTPS POST to /api/lora/ingest

\[BloodBridge API — Render.com\]  
  └─ Decodes, runs LangGraph pipeline, alerts donor chain  
\`\`\`

Coverage: Tribal health posts Jharkhand, Adivasi communities Odisha,  
hill stations Uttarakhand — where 4G/3G doesn't reach field health workers.

\---

\#\# QUICK REFERENCE — FINAL BUILD ORDER

\*\*Day 1:\*\*  
\`\`\`  
09:00  P1-A  Project setup (requirements \+ security.py \+ config \+ stubs)  
10:00  P1-B  Supabase schema 11 tables (run SQL in dashboard)  
11:00  P1-C  Neo4j schema \+ constraints  
12:00  P1-D  Synthetic data \+ train all 3 ML models  
13:00  P2-A  8-antigen ISBT scorer  
14:00  P2-B  Donor eligibility filter  
15:00  P2-C  XGBoost urgency scorer  
16:00  P2-D  Neo4j matching query  
17:00  P3-A  AgentState \+ LangGraph graph (proactive mode fields)  
18:00  P3-B  IntakeAgent \+ EligibilityFilterAgent  
19:00  P3-C  AntigenScoringAgent \+ UrgencyScoringAgent (parallel)  
20:00  P3-D  Neo4jMatchingAgent \+ ConflictResolverAgent  
21:00  P3-E  PlannerAgent (3-tier channel routing \+ proactive mode)  
22:00  P3-F  OutreachAgent (10 langs \+ consent check \+ memory context injection) ← CRITICAL PATH DONE  
\`\`\`

\*\*Day 2:\*\*  
\`\`\`  
09:00  P3-G  ChainMonitorAgent \+ APScheduler (5 jobs) — proactive captures request\_id  
10:00  P3-H  ChainRepairAgent \+ InventoryAgent  
11:00  P3-I  OutcomeAgent \+ GamificationAgent  
11:30  P3-J  ProactiveSchedulerAgent \+ TransfusionCalendarService (30 min)  
12:00  P4-A  Telegram Bot (security \+ dedup \+ consent \+ eligibility re-check)  
13:00  P4-B  OCR (10 language packs \+ verification records)  
14:00  P4-C  Donor memory system (build\_memory\_context\_for\_llm)  
15:00  P4-D  Voice Agent — Vapi.ai (make\_vapi\_call \+ /webhook/vapi/call-result)  
16:00  P4-E  SMS Service (Twilio SMS only, DLT compliant) (45 min)  
16:45  P5-A  Churn predictor \+ daily batch  
17:30  P5-B  Gamification engine (6 badges \+ leaderboard)  
18:15  P5-C  SVD challenge recommender  
19:00  P5-D  Impact story generator  
19:30  P5-E  Consent management \+ DPDP 2023 — with CONSENT\_TEXT\_HASHES (45 min)  
\`\`\`

\*\*Day 3:\*\*  
\`\`\`  
09:00  P6-A  All FastAPI REST endpoints (+ eligibility \+ schedule \+ DPDP)  
10:00  P6-B  WebSocket endpoint \+ live broadcasting  
10:30  P6-C  ntfy.sh alerts  
11:00  P6-D  Bulk donor import API (45 min)  
11:45  P7-A  e-RaktKosh scraper \+ 15-min cache  
12:30  P8-A  Render.com deployment  
13:00  P8-B  E2E tests \+ demo script (Vapi mock \+ memory injection test)  
13:30  P8-C  Security hardening (full core/security.py \+ rate limits) (30 min)  
14:00  P9-A  LoRa bridge \+ simulator (45 min)  
15:00        Seed all production data (run all seed scripts)  
16:00        Demo dry-run (run lora\_simulator.py live)  
17:00        Backup checks: ensure all mock fallbacks work  
\`\`\`

\---

\#\# DEMO DAY SURVIVAL GUIDE

\*\*MOCK THESE IF TIME SHORT (safe fallbacks):\*\*  
1\. blood\_bank\_scraper.py → return MOCK\_BLOOD\_BANKS directly  
2\. voice\_service.py → log "Vapi voice call simulated (dev mode)" instead of real API call  
3\. agents/conflict.py → urgency\_score comparison fallback (skip Gemini if rate-limited)  
4\. services/sms\_service.py → log "SMS sent (dev mode)" if DLT not registered  
5\. services/consent\_service.py → auto-grant already done in seed script for all 500 donors

\*\*NEVER MOCK THESE (must work live for demo):\*\*  
1\. agents/graph.py → full LangGraph pipeline must run end-to-end  
2\. ml/antigen\_scorer.py → 8-antigen scoring is your medical credibility  
3\. services/telegram\_bot.py → live Telegram demo is the strongest impression  
4\. api/websocket.py → real-time chain dot animation must work live  
5\. ml/models/\*.joblib → pre-trained, must load at startup (never train live)  
6\. tools/lora\_simulator.py → run this live during pitch for the LoRa demo moment  
7\. services/donor\_memory.py → build\_memory\_context\_for\_llm() must inject real memory into Groq  
8\. services/consent\_service.py → CONSENT\_TEXT\_HASHES must match 10 languages

\*\*DEMO SEQUENCE (2 minutes):\*\*  
\`\`\`  
Step 1: python tools/lora\_simulator.py \--blood B+ \--city rural\_other \--urgency CRITICAL  
        Show: "LoRa emergency packet — 8 bytes — CRC valid — from rural health post"  
Step 2: Dashboard WebSocket shows chain activating in real-time  
Step 3: Telegram phone rings — receives Hindi personalized message (with donor memory)  
Step 4: Say YES → chain dot turns green → badge fires → Sonner toast  
Step 5: Show /api/analytics → real numbers from seeded data  
Step 6: Show Neo4j graph — patient diamond \+ colored donor circles  
\`\`\`

THE WINNING MOMENT: LoRa simulator running live \+ dashboard showing  
"Emergency received from rural health post via LoRa mesh — no internet required"  
while other teams show WhatsApp chatbots. Rural last-mile is our moat.

\*\*CRITICAL PRE-DEMO CHECKS:\*\*  
\`\`\`  
\* curl bloodbridge-api.onrender.com/health → all services green (includes vapi check)  
\* python tools/lora\_simulator.py → packet decoded, pipeline starts, dashboard updates  
\* Send /register to Telegram bot → consent flow works in Hindi (stores CONSENT\_TEXT\_HASHES)  
\* Send /emergency B+ Hyderabad → chain activates, dashboard chain dots animate  
\* Send YES from donor phone → dot turns green, badge fires, WebSocket updates  
\* POST /api/donors/bulk-import with test CSV → import report correct  
\* Verify CONSENT\_TEXT\_HASHES has 10 entries and each is 64-char SHA256 hex  
\* Verify run\_proactive\_outreach() populates transfusion\_schedule.request\_id correctly  
\* Verify OutreachAgent generates messages referencing donor's donation history (memory injection)  
\`\`\`

\---

\*BloodBridge AI — Backend Development Master Document FINAL EDITION\*  
\*Team Inqilab · Blend360 Hackathon · 41 Build Prompts · Phase-by-Phase\*  
\*FastAPI \+ LangGraph \+ Neo4j \+ Supabase \+ Groq \+ Gemini \+ XGBoost \+ Telegram \+ Vapi.ai \+ LoRa\*  
\*₹0 Deployment · DPDP 2023 Compliant · 15/15 Problem Criteria Addressed\*  
\*9 Autonomous LangGraph Agents · 11 Supabase Tables · 4 Neo4j Node Types\*  
\*Proactive Scheduling · SMS Fallback (Twilio) · Voice Calls (Vapi.ai) · LoRa Rural Bridge · Consent Management\*

\*\*Changes from v6:\*\*  
\- \*\*Vapi.ai replaces Twilio Voice \+ gTTS\*\* — P4-D fully rewritten, /webhook/vapi/call-result added  
\- \*\*gTTS and asyncio-mqtt removed\*\* from requirements.txt  
\- \*\*TWILIO\_PHONE\_NUMBER removed\*\* from .env — Vapi.ai has its own phone number ID  
\- \*\*VAPI\_API\_KEY \+ VAPI\_PHONE\_NUMBER\_ID \+ VAPI\_WEBHOOK\_SECRET added\*\* to .env  
\- \*\*P3-F fixed\*\* — OutreachAgent now explicitly calls build\_memory\_context\_for\_llm() per donor  
\- \*\*P3-G fixed\*\* — run\_proactive\_outreach() captures result, extracts request\_id, calls mark\_schedule\_outreach\_started()  
\- \*\*P5-E fixed\*\* — CONSENT\_TEXT\_HASHES dict fully defined with SHA256 of all 10 language consent texts  
