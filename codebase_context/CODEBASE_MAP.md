# 🗺️ CODEBASE MAP
> Generated: 2026-06-06 | Scanned by: GitHub Copilot (Claude Haiku 4.5)
> WARNING: Update this file when architecture changes. Do NOT let it go stale.

---

## 📌 PROJECT OVERVIEW

| Property        | Value |
|-----------------|-------|
| **Project Name**   | BloodBridge AI |
| **Purpose**        | AI-driven autonomous blood coordination system for emergency transfusions and proactive donor outreach in India |
| **Type**           | Monorepo: Full-stack web app + Telegram bot + voice/SMS integrations |
| **Primary Language** | Python 3.11 (backend) + TypeScript 5.9 (frontend) |
| **Frameworks**     | FastAPI, LangGraph, React, Neo4j, Supabase PostgreSQL |
| **Database**       | PostgreSQL (Supabase) + Neo4j (Aura) for graph matching |
| **Entry Point**    | `BloodBridge_AI_Backend/main.py` (FastAPI) |
| **Dev Run**        | `uvicorn main:app --reload` (port 8000) |
| **Build**          | `pnpm run build` (frontend) |
| **Test**           | `pytest` (backend integration tests) |
| **Port**           | 8000 (backend), 5173 (frontend) |

---

## 🏗️ ARCHITECTURE OVERVIEW

BloodBridge AI is an **intelligent blood coordination platform** that automates emergency blood matching and proactive donor recruitment in India. The system combines **LangGraph agentic workflows**, **Neo4j graph matching**, and **multi-channel outreach** (Telegram, Voice calls, SMS) to create a real-time blood coordination ecosystem.

**Core Flow:** Emergency blood request → AI agents rank compatible donors → Neo4j graph finds geographically optimal donors → Outreach via Telegram/Voice/SMS → Real-time chain monitoring → Gamification rewards.

**Architecture Pattern:** Multi-layer microservices using **agent-based orchestration** (LangGraph) + **graph database** (Neo4j) for relationship queries + **transactional database** (PostgreSQL) for state management.

---

## 📁 FOLDER STRUCTURE

```
BloodBridge_AI/
├── BloodBridge_AI_Backend/          # FastAPI backend + LangGraph agents
│   ├── main.py                      # FastAPI app entry point, lifespan, CORS, rate limiting
│   ├── requirements.txt              # Python dependencies (FastAPI, LangGraph, Neo4j, etc.)
│   ├── .env.example                  # Environment variables template
│   ├── pyrefly.toml                  # Python interpreter configuration
│   ├── render.yaml                   # Render deployment config
│   ├── DEPLOY.md                     # Deployment guide
│   │
│   ├── core/                         # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic Settings for all env vars
│   │   ├── database.py               # Supabase client singletons (anon + admin)
│   │   ├── neo4j_client.py           # Neo4j async driver wrapper
│   │   ├── security.py               # JWT, webhook verification, HMAC validation
│   │   ├── limiter.py                # slowapi rate limiter config
│   │   └── ws_manager.py             # WebSocket connection pool
│   │
│   ├── models/                       # Data models and state definitions
│   │   ├── __init__.py
│   │   ├── schemas.py                # Pydantic request/response models
│   │   └── state.py                  # LangGraph AgentState TypedDict definitions
│   │
│   ├── agents/                       # LangGraph workflow agents (14 nodes)
│   │   ├── __init__.py
│   │   ├── graph.py                  # StateGraph compilation, routing, node registration
│   │   ├── intake.py                 # Fetch patient profile, language detection
│   │   ├── eligibility.py            # Filter donors by medical holds, blood type
│   │   ├── matching.py               # antigen_scoring_agent + urgency_scoring_agent
│   │   ├── neo4j_match.py            # Query Neo4j for geographically optimal donors
│   │   ├── conflict.py               # Detect/resolve antigen incompatibilities
│   │   ├── planner.py                # Choose outreach strategy (Telegram → Voice → SMS)
│   │   ├── outreach.py               # Alert donors via selected channels
│   │   ├── monitor.py                # Track donor confirmations, timeouts, auto-escalate
│   │   ├── repair.py                 # Auto-alert next donor on decline; inventory alerts
│   │   ├── voice.py                  # Vapi.ai voice call handler
│   │   ├── gamification.py           # Award badges, update leaderboards
│   │   ├── outcome.py                # Log transfusion results, consent, reward
│   │   └── proactive_scheduler.py    # Schedule proactive transfusions (not in graph)
│   │
│   ├── api/                          # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                   # POST /api/auth/login (all roles)
│   │   ├── emergency.py              # GET/POST /api/emergencies, /api/emergencies/{id}/*
│   │   ├── donors.py                 # GET /api/donors, GET /api/donors/{id}
│   │   ├── patients.py               # GET /api/patients, transfusion schedules
│   │   ├── blood_banks.py            # Blood bank inventory, location data
│   │   ├── admin.py                  # Admin panel API endpoints
│   │   ├── webhooks.py               # Telegram, Vapi, Twilio webhook handlers
│   │   ├── lora.py                   # LoRa-based offline mode (fallback)
│   │   └── websocket.py              # WebSocket real-time chain monitoring
│   │
│   ├── services/                     # Business logic services (non-agent)
│   │   ├── __init__.py
│   │   ├── telegram_bot.py           # Agentic Telegram bot (10+ tools, multi-language)
│   │   ├── voice_service.py          # Vapi.ai outbound calls, Sarvam AI TTS, 10 Indian langs
│   │   ├── alerts.py                 # ntfy.sh alert notifications
│   │   ├── gamification_service.py   # Badge logic, city leaderboard, challenge tracking
│   │   ├── antigen_scorer.py         # Blood compatibility scoring (ABO + Rh + minor)
│   │   ├── churn_batch.py            # XGBoost churn risk batch processing
│   │   ├── churn_predictor.py        # Churn prediction model (joblib)
│   │   ├── donor_memory.py           # Build donor interaction history for personalization
│   │   ├── consent_service.py        # DPDP 2023 privacy consent management
│   │   ├── impact_story.py           # Generate donor impact narratives
│   │   ├── ocr_service.py            # Tesseract OCR blood card extractor (10 Indian langs)
│   │   ├── blood_bank_scraper.py     # e-RaktKosh scraper (fallback blood availability)
│   │   ├── transfusion_calendar.py   # Schedule & proactive outreach for transfusion-due patients
│   │   ├── sms_service.py            # Twilio SMS dispatcher (DLT-registered)
│   │   └── lora_bridge.py            # LoRa device communication (rural fallback)
│   │
│   ├── scheduler/                    # APScheduler cron jobs
│   │   ├── __init__.py
│   │   ├── cron.py                   # Setup recurring jobs (5-min chain monitor, daily churn batch)
│   │   ├── jobs.py                   # Job handler functions (monitor_all_active_chains, etc.)
│   │   └── worker.py                 # Worker pool configuration
│   │
│   ├── ml/                           # Machine learning models
│   │   ├── __init__.py
│   │   ├── antigen_scorer.py         # Antigen compatibility scoring logic
│   │   ├── churn_predictor.py        # XGBoost churn model
│   │   ├── challenge_recommender.py  # SVD collaborative filtering for gamified challenges
│   │   ├── eligibility_filter.py     # Medical eligibility rules
│   │   ├── train_churn.py            # Training script for churn model
│   │   ├── train_urgency.py          # Training script for urgency scorer
│   │   ├── urgency_scorer.py         # Urgency classification (critical vs routine)
│   │   └── models/                   # Joblib-serialized trained models
│   │       └── churn_model.joblib, svd_challenges.joblib
│   │
│   ├── data/                         # Database schemas and seeders
│   │   ├── __init__.py
│   │   ├── supabase_schema.sql       # PostgreSQL table definitions (11 tables)
│   │   ├── neo4j_schema.cypher       # Neo4j graph constraints, indexes
│   │   ├── schema_v2_gaps.sql        # Migration/gap analysis schema
│   │   ├── generate_synthetic.py     # Synthetic data generation for testing
│   │   ├── seed_demo.py              # Demo data seeding
│   │   ├── seed_supabase.py          # Supabase initial seed
│   │   ├── seed_neo4j.py             # Neo4j initial seed (donor locations, graph relationships)
│   │   └── seed_patients.py          # Patient data seeding
│   │
│   ├── scratch/                      # Experimental/debugging scripts
│   │   ├── fix_neo4j_latlng.py
│   │   ├── inspect_graph.py
│   │   ├── test_*.py                 # Various testing scripts
│   │   └── test_phase*.py            # Phase-specific integration tests
│   │
│   ├── scripts/                      # Utility scripts
│   │   ├── seed_db.py                # Database seeding script
│   │   └── seed_patients.py          # Patient seeding
│   │
│   ├── tests/                        # Pytest integration tests
│   │   └── test_*.py                 # Test files matching src structure
│   │
│   ├── tools/                        # Utility tools (TBD)
│   │
│   └── __pycache__/                  # Python cache

├── BloodBridge_AI_frontend/         # TypeScript/React monorepo (pnpm workspace)
│   ├── package.json                  # Workspace root metadata
│   ├── pnpm-lock.yaml                # Dependency lock file
│   ├── pnpm-workspace.yaml           # Monorepo workspace config
│   ├── tsconfig.base.json            # Base TypeScript configuration
│   ├── tsconfig.json                 # Extended TypeScript configuration
│   │
│   ├── lib/                          # Shared libraries
│   │   ├── api-client-react/         # React API client (auto-generated from OpenAPI)
│   │   ├── api-spec/                 # OpenAPI spec definitions
│   │   ├── api-zod/                  # Zod type definitions for API validation
│   │   └── db/                       # Database utilities
│   │
│   ├── scripts/                      # Build and codegen scripts
│   │   └── [various build scripts]
│   │
│   ├── artifacts/                    # Build outputs
│   │   └── [compiled bundles, dist/]
│   │
│   ├── attached_assets/              # Static assets (logos, icons, etc.)
│   │   └── [images, fonts, etc.]
│   │
│   └── node_modules/                 # Node dependencies (pnpm)

├── codebase_context/                # AI memory system (THIS FOLDER)
│   ├── README.md                     # System instructions
│   ├── QUICK_REF.md                  # Ultra-compressed cheatsheet
│   ├── CODEBASE_MAP.md               # Full architecture (THIS FILE)
│   ├── CODEBASE_TRACKER.md           # Session logs + TODO list
│   └── ACTIVE_SESSION.md             # Current task context

├── complete_codebase/               # Archive/reference
│   ├── full_code.txt
│   └── full_code_before_implementation_of_v2.txt

├── [Root documentation files]
├── README.md                         # Project overview
├── MASTER_STATUS.txt                # Comprehensive status (filled)
├── TESTING_GUIDE.md
├── END_TO_END_TESTING_GUIDE.md
├── TELEGRAM_TESTING_GUIDE.md
├── BloodBridge_AI_PRD_v6_FINAL.md  # Product requirements doc
├── BloodBridge_V2_GapAnalysis_FINAL.md
├── version_2_tracker.md
└── version_2_pre-hackathon.md
```

---

## 📋 MODULE INDEX

| File Path | Purpose | Key Exports / Functions | Internal Dependencies |
|-----------|---------|------------------------|-----------------------|
| **main.py** | FastAPI app entry point, CORS, APScheduler lifespan | FastAPI app instance, lifespan context manager | all routers, core/* |
| **core/config.py** | Pydantic settings for all env vars | `Settings` class, `get_settings()` | pydantic_settings |
| **core/database.py** | Supabase client singletons | `get_supabase()`, `get_supabase_admin()` | supabase |
| **core/neo4j_client.py** | Neo4j async driver | `get_driver()`, `get_neo4j()`, `health_check()`, `close()` | neo4j async driver |
| **core/security.py** | JWT, webhook verification, HMAC, IP validation | `create_access_token()`, `verify_telegram_webhook()`, `generate_idempotency_key()` | jwt, hmac, hashlib |
| **core/limiter.py** | slowapi rate limiter | `limiter` instance | slowapi |
| **core/ws_manager.py** | WebSocket connection manager | `ws_manager` instance | fastapi.websockets |
| **models/state.py** | LangGraph AgentState + ChainNodeState | `AgentState` TypedDict, `ChainNodeState` TypedDict | typing |
| **agents/graph.py** | StateGraph compilation, 14-node workflow | `build_bloodbridge_graph()`, `run_emergency_pipeline()` | all agent nodes, models/state |
| **agents/intake.py** | Fetch patient, detect language, register request | `intake_agent()` | core/database, models/state |
| **agents/eligibility.py** | Filter by medical holds, blood type | `eligibility_agent()` | core/database, models/state |
| **agents/matching.py** | Antigen + urgency scoring | `antigen_scoring_agent()`, `urgency_scoring_agent()` | ml/*, models/state |
| **agents/neo4j_match.py** | Query Neo4j for top 8 donors | `neo4j_matching_agent()` | core/neo4j_client, models/state |
| **agents/conflict.py** | Detect & resolve antigen conflicts | `conflict_resolver_agent()` | models/state |
| **agents/planner.py** | Choose outreach strategy | `planner_agent()` | models/state, services/* |
| **agents/outreach.py** | Alert donors via Telegram/Voice/SMS | `outreach_agent()` | services/*, core/database |
| **agents/monitor.py** | Track confirmations, timeouts, escalate | `chain_monitor_agent()` | core/database, models/state |
| **agents/repair.py** | Auto-alert next donor, inventory alerts | `chain_repair_agent()`, `inventory_agent()` | core/database, services/* |
| **agents/voice.py** | Vapi.ai voice call handler | `voice_agent_node()` | services/voice_service |
| **agents/gamification.py** | Award badges, update leaderboards | `gamification_agent()` | services/gamification_service |
| **agents/outcome.py** | Log transfusion results, consent, reward | `outcome_agent()` | core/database, services/* |
| **api/auth.py** | POST /api/auth/login, signup | `login()`, `signup()` routers | core/database, core/security |
| **api/emergency.py** | GET/POST /api/emergencies, chain tracking | `list_emergencies()`, `create_emergency()`, `confirm_donation()` | agents/graph, core/database |
| **api/donors.py** | GET /api/donors, donor profiles | `list_donors()`, `get_donor()` | core/database |
| **api/patients.py** | GET /api/patients, transfusion schedules | `list_patients()`, `get_patient()` | core/database |
| **api/blood_banks.py** | Blood bank inventory, locations | `get_blood_banks()`, `update_inventory()` | core/database |
| **api/admin.py** | Admin panel API | Admin dashboard endpoints | core/database, core/security |
| **api/webhooks.py** | Telegram, Vapi, Twilio webhook handlers | `telegram_webhook()`, `vapi_webhook()`, `twilio_webhook()` | services/*, core/security |
| **api/websocket.py** | WebSocket chain monitoring | `/ws/{request_id}` | core/ws_manager |
| **services/telegram_bot.py** | Agentic Telegram bot (10+ tools) | `handle_message()`, 10 tool functions | langchain_groq, core/database |
| **services/voice_service.py** | Vapi.ai outbound calls, Sarvam AI TTS | `make_outbound_call()`, `generate_voice_script()` | httpx, gemini-api |
| **services/gamification_service.py** | Badge logic, leaderboard | `award_badge()`, `update_leaderboard()` | core/database |
| **services/donor_memory.py** | Interaction history, personalization | `build_donor_memory()`, `get_donor_context()` | core/database |
| **services/consent_service.py** | DPDP 2023 consent mgmt | `record_consent()`, `check_consent()` | core/database |
| **services/antigen_scorer.py** | Blood compatibility scoring | `score_antigen_compatibility()` | ml/* |
| **services/churn_batch.py** | XGBoost churn batch processing | `compute_churn_scores()` | ml/churn_predictor |
| **services/impact_story.py** | Generate donor impact narratives | `generate_impact_story()` | gemini-api |
| **services/ocr_service.py** | Tesseract OCR blood card extractor | `extract_blood_card()` | pytesseract, Pillow |
| **services/blood_bank_scraper.py** | e-RaktKosh scraper | `fetch_blood_inventory()` | beautifulsoup4, httpx |
| **services/transfusion_calendar.py** | Schedule + proactive outreach | `get_patients_due_in_days()`, `schedule_outreach()` | core/database |
| **services/lora_bridge.py** | LoRa device communication (rural fallback) | `send_lora_alert()`, `receive_lora_response()` | LoRa libraries |
| **scheduler/cron.py** | Setup APScheduler recurring jobs | `setup_cron_jobs()` | apscheduler |
| **scheduler/jobs.py** | Job handler functions | `monitor_all_active_chains()`, `run_churn_batch()` | agents/*, services/* |
| **ml/churn_predictor.py** | XGBoost churn model loader | `predict_churn_score()` | xgboost, joblib |
| **ml/urgency_scorer.py** | Urgency classification | `score_urgency()` | scikit-learn, joblib |
| **ml/antigen_scorer.py** | Antigen compatibility logic | `score_antigen()` | numpy, pandas |
| **data/supabase_schema.sql** | PostgreSQL table DDL (12 tables) | — | PostgreSQL |
| **data/neo4j_schema.cypher** | Neo4j graph constraints, indexes | — | Cypher |
| **data/seed_neo4j.py** | Populate Neo4j donor locations graph | `seed_neo4j()` | neo4j driver |

---

## 🗃️ DATA MODELS (12 Supabase Tables)

### Donor
```json
{
  donor_id: str,                    # Primary key (auto-generated)
  telegram_chat_id: str unique,     # Telegram registration link
  phone: str,                       # Phone number (optional, for SMS)
  password: str (nullable),         # Optional for bot-registered donors
  name: str,                        # Full name
  blood_type: str,                  # A+, A-, B+, B-, AB+, AB-, O+, O-
  city: str,                        # City of residence
  ward: str (nullable),             # Sub-city ward/district
  lat: float, lng: float,           # Geolocation (for distance matching)
  
  # Antigen flags (blood compatibility)
  kell_negative: bool,              # Kell antigen absence
  duffy_negative: bool,             # Duffy antigen absence
  kidd_negative: bool,              # Kidd antigen absence
  rh_e_negative: bool,              # Rh E antigen absence
  rh_c_negative: bool,              # Rh C antigen absence
  mns_negative: bool,               # MNS antigen absence
  
  # Medical history
  hemoglobin: float (nullable),     # Recent hemoglobin level
  last_donation_date: date,         # Last donation date (56-day gap enforcement)
  medical_hold: bool,               # Currently on medical hold
  donation_count: int,              # Total donations
  lives_saved: int,                 # Calculated from transfusions
  
  # Engagement metrics
  response_rate: float,             # Historical response rate (0-1)
  preferred_language: str,          # Hindi, English, Telugu, etc.
  churn_score: float,               # XGBoost churn risk (0-1)
  churn_risk: str,                  # HIGH, MEDIUM, LOW
  is_active: bool,                  # Account active flag
  
  # Consent flags (DPDP 2023)
  consent_data_storage: bool,       # Data storage consent
  consent_outreach: bool,           # Outreach consent
  consent_granted_at: timestamp,    # When consent was granted
  
  created_at: timestamp,
  updated_at: timestamp
}
```
**Relations:** 1:N with blood_chains, 1:N with gamification, 1:N with donor_memory

### Patient
```json
{
  patient_id: str,                  # Primary key
  name: str,
  phone: str unique,                # For login + SMS
  password: str,
  age: int,
  blood_type: str,
  hospital: str,
  ward: str (nullable),
  city: str,
  hemoglobin: float,
  transfusion_count: int,           # Lifetime transfusions
  next_transfusion_due: date,       # Scheduled transfusion date
  
  # Antibody flags (blood compatibility)
  antibody_kell: bool,
  antibody_duffy: bool,
  antibody_kidd: bool,
  antibody_rh_e: bool,
  antibody_rh_c: bool,
  antibody_mns: bool,
  kell_negative: bool,
  
  status: str,                      # CRITICAL, STABLE, OVERDUE
  is_active: bool,
  coordinator_id: str (nullable),   # Assigned coordinator
  created_at: timestamp,
  updated_at: timestamp
}
```
**Relations:** 1:N with emergency_requests, 1:N with transfusion_schedule

### EmergencyRequest
```json
{
  request_id: str,                  # Primary key (auto-generated)
  patient_id: str FK,               # Patient needing blood
  blood_type: str,                  # Required blood type
  city: str,                        # Request city
  hospital_name: str,               # Hospital name
  ward: str (nullable),
  priority: str,                    # CRITICAL, HIGH, ROUTINE
  urgency_score: float,             # AI-computed urgency (0-100)
  status: str,                      # IN_PROGRESS, COMPLETED, ESCALATED, CANCELLED
  triggered_by: str,                # Who triggered (staff, scheduler, emergency)
  request_mode: str,                # emergency OR proactive
  agent_trace_id: str (nullable),   # LangGraph execution trace ID
  idempotency_key: str unique,      # Dedup key (30-min window)
  idempotency_expires_at: timestamp,
  created_at: timestamp,
  completed_at: timestamp (nullable)
}
```
**Relations:** 1:N with blood_chains, FK to patients

### BloodChain
```json
{
  chain_id: str,                    # Primary key
  request_id: str FK,               # Emergency request
  donor_id: str FK,                 # Donor in chain
  chain_position: int,              # Position in outreach sequence (1-8)
  status: str,                      # PENDING, ALERTED, CONFIRMED, DECLINED, VOICE, SMS, COMPLETED
  antigen_score: float,             # Compatibility score (0-100)
  distance_km: float,               # Distance from hospital
  
  # Contact tracking
  alerted_at: timestamp (nullable),
  confirmed_at: timestamp (nullable),
  declined_at: timestamp (nullable),
  completed_at: timestamp (nullable),
  
  # Engagement
  attempts: int,                    # Number of alert attempts
  preferred_channel: str,           # Telegram, Voice, SMS
  
  created_at: timestamp,
  updated_at: timestamp
}
```
**Relations:** FK to emergency_requests + donors

### Gamification
```json
{
  gamification_id: str,
  donor_id: str FK,
  badge: str,                       # Gold Samaritan, Platinum Hero, etc.
  challenge_type: str,              # Weekend Warrior, City Champion, etc.
  challenge_count: int,             # Completions
  lives_saved_total: int,
  leaderboard_rank: int,            # City-level rank
  leaderboard_city: str,
  points: int,
  created_at: timestamp,
  updated_at: timestamp
}
```

### DonorMemory
```json
{
  memory_id: str,
  donor_id: str FK,
  interaction_type: str,            # alert_received, confirmed, declined, voice_call, sms
  language_used: str,               # Hindi, Telugu, etc.
  timestamp: timestamp,
  context: json,                    # Stored metadata (emergency_type, outcome, etc.)
  sentiment: str (nullable)         # positive, neutral, negative
}
```

### TransfusionSchedule
```json
{
  schedule_id: str,
  patient_id: str FK,
  scheduled_date: date,
  blood_type_needed: str,
  transfusion_due_date: date,
  status: str,                      # SCHEDULED, OUTREACH_STARTED, COMPLETED, CANCELLED
  created_at: timestamp
}
```

### ConsentRecords
```json
{
  consent_id: str,
  donor_id: str FK,
  consent_data_storage: bool,
  consent_outreach: bool,
  consent_granted_at: timestamp,
  consent_withdrawn_at: timestamp (nullable),
  version: str                      # Version of consent form (DPDP 2023)
}
```

### Staff
```json
{
  staff_id: str,
  telegram_chat_id: str unique,
  email: str unique,
  password: str,
  name: str,
  hospital: str,
  role: str,                        # Staff, Admin, Coordinator
  is_active: bool,
  created_at: timestamp
}
```

### AgentTraces
```json
{
  trace_id: str,
  request_id: str FK,
  patient_id: str,
  started_at: timestamp,
  ended_at: timestamp (nullable),
  status: str,                      # running, success, failed
  nodes_executed: json,             # Array of executed node names
  final_chain: json,                # Final donor chain
  errors: json (nullable),
  execution_time_ms: int
}
```

### LeaderboardCache
```json
{
  entry_id: str,
  donor_id: str FK,
  city: str,                        # City ranking
  lives_saved: int,                 # Total lives saved by donor
  rank: int,                        # City-level ranking
  month_year: str,                  # YYYY-MM for monthly snapshots
  updated_at: timestamp
}
```
**Purpose:** Cache city leaderboard rankings for gamification display. Updated monthly + real-time.

### DonorVerifications
```json
{
  verification_id: str,
  donor_id: str FK,
  blood_card_image_url: str,        # S3/Supabase Storage URL
  extracted_blood_type: str,        # From OCR
  extracted_antigen_flags: json,    # From OCR parsing
  verification_status: str,         # PENDING, VERIFIED, FAILED
  verified_by_staff: str (nullable),# Staff who verified
  verified_at: timestamp (nullable),
  ocr_confidence: float,            # 0-1 OCR accuracy score
  created_at: timestamp
}
```
**Purpose:** Store OCR extraction + manual verification records for blood card authenticity.

---

## 🌐 API / ROUTES

| Method | Route | Handler File | Auth Required | Description |
|--------|-------|-------------|---------------|-------------|
| **POST** | `/api/auth/login` | api/auth.py | ❌ | Login for staff/donor/patient, returns JWT |
| **POST** | `/api/auth/signup` | api/auth.py | ❌ | Register new user (donor/patient/staff) |
| **GET** | `/api/emergencies` | api/emergency.py | ✅ Staff | List all active emergencies with donor chains |
| **GET** | `/api/emergencies/{id}` | api/emergency.py | ✅ Staff | Get single emergency + full chain |
| **POST** | `/api/emergencies` | api/emergency.py | ✅ Staff | Create new emergency request (background task) |
| **GET** | `/api/emergencies/{id}/chain` | api/emergency.py | ✅ Staff | Get donor chain for emergency |
| **GET** | `/api/emergencies/{id}/trace` | api/emergency.py | ✅ Staff | Get LangGraph execution trace |
| **POST** | `/api/emergencies/{id}/confirm/{donor_id}` | api/emergency.py | ✅ Donor | Confirm donation |
| **POST** | `/api/emergencies/{id}/decline/{donor_id}` | api/emergency.py | ✅ Donor | Decline and trigger repair |
| **GET** | `/api/donors` | api/donors.py | ✅ Staff | List all donors with filters |
| **GET** | `/api/donors/{id}` | api/donors.py | ✅ Staff | Get donor profile + interaction history |
| **GET** | `/api/patients` | api/patients.py | ✅ Staff | List patients |
| **GET** | `/api/patients/{id}` | api/patients.py | ✅ Staff | Get patient profile + transfusion schedule |
| **GET** | `/api/blood-banks` | api/blood_banks.py | ✅ Staff | List blood banks + real-time inventory |
| **GET** | `/api/admin/dashboard` | api/admin.py | ✅ Admin | Admin dashboard stats |
| **POST** | `/webhook/telegram` | api/webhooks.py | ❌ | Telegram bot webhook (verified by secret) |
| **POST** | `/webhook/vapi` | api/webhooks.py | ❌ | Vapi.ai voice callback webhook |
| **POST** | `/webhook/twilio` | api/webhooks.py | ❌ | Twilio SMS webhook |
| **WS** | `/ws/{request_id}` | api/websocket.py | ✅ | WebSocket real-time chain monitoring |

---

## 🔐 AUTHENTICATION & AUTHORIZATION

**Auth Method:** JWT (HS256)
- **Token Duration:** 7 days
- **Token Storage:** Returned in response (frontend stores in localStorage or httpOnly cookie)
- **Role-based Access:** staff, donor, patient, admin

**Login Endpoint:** `POST /api/auth/login`
```json
Request:
{
  "role": "staff",                  // or "donor", "patient"
  "identifier": "email@hospital.com", // email for staff, donor_id/phone for donor/patient
  "password": "password"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": { ...user data... }
}
```

**Protected Routes:** All `/api/*` except `/api/auth/login` and `/api/auth/signup` require JWT in Authorization header.

**Webhook Verification:**
- **Telegram:** HMAC-SHA256 via X-Telegram-Bot-Api-Secret-Token header
- **Vapi:** HMAC-SHA256 via X-Vapi-Signature header
- **Twilio:** IP whitelist verification against Twilio CIDR ranges

---

## 🌍 ENVIRONMENT VARIABLES

| Variable | Purpose | Required | Example / Default |
|----------|---------|----------|-------------------|
| **SUPABASE_URL** | Supabase project URL | ✅ | https://xxxxx.supabase.co |
| **SUPABASE_KEY** | Supabase anon key (RLS enabled) | ✅ | eyJhbGc... |
| **SUPABASE_SERVICE_KEY** | Supabase service role key (RLS bypass) | ✅ | eyJhbGc... |
| **NEO4J_URI** | Neo4j Aura connection URI | ✅ | neo4j+s://xxxxx.databases.neo4j.io |
| **NEO4J_USERNAME** | Neo4j user | ✅ | neo4j |
| **NEO4J_PASSWORD** | Neo4j password | ✅ | [32-char password] |
| **GROQ_API_KEY** | Groq LLM API key | ✅ | gsk_xxxxx |
| **GEMINI_API_KEY** | Google Gemini API key | ✅ | AIzaSy... |
| **TELEGRAM_BOT_TOKEN** | Telegram bot token from @BotFather | ✅ | 1234567890:ABCdef... |
| **TELEGRAM_WEBHOOK_URL** | URL for Telegram to POST updates | ✅ | https://api.bloodbridge.app/webhook/telegram |
| **TELEGRAM_WEBHOOK_SECRET** | 32-char random secret for webhook verification | ✅ | abcd1234abcd1234abcd1234abcd1234 |
| **VAPI_API_KEY** | Vapi.ai API key | ✅ | [from dashboard] |
| **VAPI_PHONE_NUMBER_ID** | Vapi phone number resource ID | ✅ | [from dashboard] |
| **VAPI_WEBHOOK_SECRET** | 32-char secret for Vapi webhook | ✅ | [random] |
| **TWILIO_ACCOUNT_SID** | Twilio account SID | ✅ | ACxxxxx |
| **TWILIO_AUTH_TOKEN** | Twilio auth token | ✅ | [from dashboard] |
| **TWILIO_DLT_SENDER_ID** | India DLT-registered sender ID for SMS | ✅ | BLDBRG |
| **TWILIO_DLT_TEMPLATE_ID_HI** | Hindi SMS template ID (DLT registered) | ✅ | 1234567890 |
| **TWILIO_DLT_TEMPLATE_ID_EN** | English SMS template ID (DLT registered) | ✅ | 1234567891 |
| **NTFY_TOPIC** | ntfy.sh alert topic | ❌ | bloodbridge-alerts |
| **APP_ENV** | Environment (development, production, staging) | ❌ | development |
| **APP_HOST** | FastAPI host bind | ❌ | 0.0.0.0 |
| **APP_PORT** | FastAPI port | ❌ | 8000 |
| **APP_BASE_URL** | Public app URL (for Telegram deep links) | ❌ | http://localhost:8000 |
| **WEB_PORTAL_URL** | Frontend URL (for Telegram deep links) | ❌ | http://localhost:5173 |
| **LOG_LEVEL** | Logging level (DEBUG, INFO, WARNING, ERROR) | ❌ | INFO |
| **DEMO_MOCK_MODE** | Enable mock responses (true/false) | ❌ | false |

---

## 🔌 EXTERNAL INTEGRATIONS & SERVICES

| Service | Purpose | SDK / Library | Config Location |
|---------|---------|--------------|----------------|
| **Supabase PostgreSQL** | Transactional database (12 tables) | supabase-py | core/database.py |
| **Neo4j Aura** | Graph database (donor locations, relationships) | neo4j async driver | core/neo4j_client.py |
| **Groq API** | LLM for Telegram bot tool-calling | langchain-groq | services/telegram_bot.py |
| **Google Gemini** | LLM for impact stories, voice scripts | google-generativeai | services/impact_story.py, services/voice_service.py |
| **Telegram Bot API** | Donor/staff alerts and bot interface | python-telegram-bot | services/telegram_bot.py |
| **Vapi.ai** | Outbound voice calls (India-first) | httpx | services/voice_service.py |
| **Sarvam AI** | Indian TTS for voice calls | httpx (API calls) | services/voice_service.py |
| **Twilio SMS** | SMS outreach (DLT-registered for India) | twilio-python | services/sms_service.py |
| **ntfy.sh** | Push notifications for alerts | httpx | services/alerts.py |
| **Tesseract OCR** | Blood card image extraction (10 Indian langs) | pytesseract + Pillow | services/ocr_service.py |
| **e-RaktKosh API** | Indian blood bank inventory scraper (fallback) | beautifulsoup4 + httpx | services/blood_bank_scraper.py |
| **XGBoost** | Churn prediction model | xgboost + joblib | ml/churn_predictor.py |
| **scikit-learn** | ML utilities (preprocessing, metrics) | scikit-learn | ml/* |
| **LangChain** | LLM orchestration framework | langchain-core, langchain | agents/*, services/telegram_bot.py |
| **LangGraph** | Agentic workflow orchestration (14-node graph) | langgraph | agents/graph.py |

---

## 🧠 STATE MANAGEMENT

**Global State:** LangGraph `AgentState` TypedDict (immutable state passed through workflow)
- Defined in `models/state.py`
- Includes request context, patient profile, matched donors, outreach plan, outcome
- Nodes read from state, compute, return updated dict merge

**Server State:**
- **Emergency requests:** Stored in Supabase `emergency_requests` table
- **Real-time chain monitoring:** WebSocket `/ws/{request_id}` via core/ws_manager.py
- **Scheduler jobs:** APScheduler in-memory job store (persisted via Supabase)
- **Donor churn:** Batch computed via `scheduler/jobs.py:monitor_all_active_chains()` (5-min cron)

**Neo4j Graph State:**
- Donor location nodes + edges (distance relationships)
- Blood compatibility relationships
- Queried by `agents/neo4j_match.py` to find top 8 geographically optimal donors

---

## 🎨 PATTERNS & CONVENTIONS

- **Error Handling:** Try/catch in all agent nodes + service functions. Custom HTTPException with proper status codes. Logged at ERROR level with traceback.
- **Naming:** snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants, kebab-case for file names (rare).
- **Imports:** Absolute imports (no relative). All imports at module top.
- **API Responses:** All endpoints return JSON with Pydantic BaseModel validation. Error responses use HTTPException.
- **Async Pattern:** async/await throughout. No .then() chains. APScheduler for background jobs.
- **Testing Pattern:** Pytest for backend. Integration tests in `tests/` require live Supabase + Neo4j.
- **Comments:** Docstrings on all agent nodes and public functions. Inline comments for complex logic.
- **Logging:** Named loggers per module. Log at INFO for state transitions, DEBUG for verbose, ERROR for exceptions.
- **Type Hints:** Full type annotations required in all function signatures and TypedDict definitions.
- **LangGraph Nodes:** Each agent node is an async function taking `AgentState` and returning `dict` with state updates.
- **Webhook Verification:** All webhook endpoints verify HMAC signature before processing.

---

## ⚠️ GOTCHAS & IMPORTANT NOTES

- **56-day Donation Gap:** Enforce in `agents/eligibility.py` — skip donors with `last_donation_date` < 56 days ago.
- **Antigen Compatibility is Complex:** Not just ABO/Rh. Also check Kell, Duffy, Kidd, MNS antigens. Logic in `services/antigen_scorer.py`.
- **DPDP 2023 Privacy:** SENSITIVE_FIELDS (phone, antibody_flags, hemoglobin, antigen_score, etc.) MUST NOT be sent via Telegram. See `services/telegram_bot.py:SENSITIVE_FIELDS`.
- **Neo4j Async Only:** All Neo4j queries use AsyncDriver. No sync driver.
- **Supabase RLS:** Use `get_supabase()` (anon key) for RLS-protected queries. Use `get_supabase_admin()` only in trusted services/agents.
- **Idempotency:** Emergency requests use 30-min idempotency window. Same patient + blood_type + city within 30 min deduped.
- **Chain Position Limit:** Maximum 8 donors per chain. `agents/outreach.py` sends alerts to donors in sequence.
- **Telegram Webhook Secret:** Must be exactly what's configured in Telegram Bot API settings. Mismatch causes webhook verification failure.
- **Vapi Webhook Signature:** Computed as HMAC-SHA256(body, secret). Verify in `api/webhooks.py:vapi_webhook()`.
- **Donor Churn Score:** Computed daily by `scheduler/jobs.py:run_churn_batch()`. High churn (> 0.7) donors excluded from critical emergencies.
- **India-First Voice:** Vapi.ai + Sarvam AI TTS. No English-only voice calls.
- **Timezone:** All dates/timestamps stored as UTC in DB. Convert to user timezone in frontend (India Standard Time by default).
- **Medical Hold:** Donors with `medical_hold=true` are skipped in eligibility phase.

---

## 🚫 DO NOT TOUCH

- [DO NOT] Modify `.env` in git — use `.env.example` as template
- [DO] Never hardcode credentials — always read from `core/config.py`
- [DO] Never query Supabase without error handling
- [DO] Never modify Neo4j schema without backup
- [DO] Never change the LangGraph node names without updating all edge definitions
- [DO] Never send SENSITIVE_FIELDS via Telegram
- [DO] Never bypass webhook verification in production

---

## 📦 KEY DEPENDENCIES

| Package | Version | Purpose | Docs |
|---------|---------|---------|------|
| fastapi | 0.115.0 | HTTP web framework | fastapi.tiangolo.com |
| uvicorn | 0.30.6 | ASGI server | uvicorn.org |
| pydantic | 2.8.2 | Data validation | docs.pydantic.dev |
| supabase | 2.7.4 | PostgreSQL client | supabase.com/docs |
| neo4j | 5.23.1 | Graph database driver (async) | neo4j.com/docs |
| langgraph | 0.2.28 | Agentic workflow orchestration | github.com/langchain-ai/langgraph |
| langchain | 0.3.1 | LLM framework | python.langchain.com |
| langchain-groq | 0.2.0 | Groq LLM integration | — |
| langchain-google-genai | 2.0.0 | Google Gemini integration | — |
| google-generativeai | 0.7.2 | Gemini API | ai.google.dev |
| groq | 0.11.0 | Groq API client | groq.com/docs |
| xgboost | 2.1.1 | Gradient boosting (churn model) | xgboost.readthedocs.io |
| scikit-learn | 1.5.2 | ML utilities | scikit-learn.org |
| python-telegram-bot | 21.6 | Telegram Bot API wrapper | python-telegram-bot.org |
| APScheduler | 3.10.4 | Job scheduling | apscheduler.readthedocs.io |
| pytesseract | 0.3.13 | Tesseract OCR wrapper | — |
| Pillow | 10.4.0 | Image processing | pillow.readthedocs.io |
| httpx | 0.27.2 | Async HTTP client | python-httpx.org |
| slowapi | 0.1.9 | Rate limiter | — |
| python-dotenv | 1.0.1 | .env file parsing | — |

---

## 🔄 Execution Flow: Emergency Blood Request

```
User (Staff) → POST /api/emergencies
  ↓
FastAPI Validation
  ↓
APScheduler BackgroundTask: run_emergency_pipeline()
  ↓
[LangGraph 14-Node Pipeline Starts]
  ├─ intake_agent → Fetch patient profile
  ├─ eligibility_agent → Filter by medical holds
  ├─ antigen_scoring_agent → Score compatibility (parallel)
  ├─ urgency_scoring_agent → Score urgency (parallel)
  ├─ neo4j_matching_agent → Query Neo4j for top 8 donors
  ├─ conflict_resolver_agent → Check antigen conflicts
  ├─ planner_agent → Choose outreach (Telegram → Voice → SMS)
  ├─ outreach_agent → Send alerts (Telegram/Vapi/Twilio)
  ├─ chain_monitor_agent → Track responses (5-min recurring)
  │   └─ [If donor confirms] → outcome_agent (log, consent, reward)
  │   └─ [If donor declines] → repair_agent (auto-alert next)
  ├─ gamification_agent → Award badges
  └─ outcome_agent → Log final result
  ↓
Database Updated: emergency_requests, blood_chains, gamification, agent_traces
  ↓
Real-time WebSocket: `/ws/{request_id}` notifies frontend
  ↓
Telegram Bot: Donor receives alert with confirm/decline buttons
  ↓
[Parallel: Voice Calls via Vapi + SMS via Twilio for non-responders]
  ↓
[Complete] Emergency marked IN_PROGRESS → COMPLETED/ESCALATED/CANCELLED
```

---

End of CODEBASE_MAP.md. Read CODEBASE_TRACKER.md for session history and TODOs.
