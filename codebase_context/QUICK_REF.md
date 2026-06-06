# ⚡ QUICK REFERENCE
> The FIRST FILE to read. Ultra-compressed. Know the project in 50 lines.

---

## Stack
**Backend:** FastAPI (Python 3.11) + LangGraph + Groq/Gemini LLMs
**Databases:** PostgreSQL (Supabase) + Neo4j (Aura) for graph matching
**Frontend:** TypeScript + React (pnpm workspace)
**Voice/SMS:** Vapi.ai (voice) + Twilio (SMS, DLT-registered for India)
**Telegram:** Agentic bot with 10+ tools, multi-turn registration, OCR
**Scheduling:** APScheduler for cron jobs, proactive outreach
**ML:** XGBoost churn model, SVD challenge recommender

---

## Run It
```bash
# Backend (Python 3.11)
cd BloodBridge_AI_Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill with real credentials
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd BloodBridge_AI_frontend
pnpm install
pnpm run build      # or pnpm run dev for dev mode
```

---

## Critical Paths
| What | Where |
|------|-------|
| FastAPI entry | `BloodBridge_AI_Backend/main.py` |
| AI pipeline (LangGraph) | `agents/graph.py` (14 nodes) |
| REST API routes | `api/{emergency, donors, patients, auth, blood_banks}.py` |
| Telegram bot service | `services/telegram_bot.py` (10+ tools, agentic) |
| DB schema | `data/supabase_schema.sql` (11 tables) |
| Neo4j graph | `data/neo4j_schema.cypher` + `agents/neo4j_match.py` |
| Config/env | `core/config.py` (Pydantic Settings) |
| Type definitions | `models/schemas.py`, `models/state.py` |

---

## Architecture
**Emergency Blood Coordination Flow:**
1. Patient needs blood → Emergency API triggered
2. Intake agent fetches patient profile + antibody flags
3. Eligibility filter checks donor medical holds
4. Antigen scorer ranks donors by blood compatibility
5. Neo4j matcher finds top 8 donors by distance + antigen score
6. Conflict resolver if incompatibilities detected
7. Planner decides outreach strategy (Telegram → Voice → SMS)
8. Outreach agent alerts donors via Telegram/Vapi/Twilio
9. Chain monitor tracks donor confirmations in real-time
10. If donor declines, repair agent auto-alerts next in chain
11. Gamification tracks lives saved, badges, leaderboards
12. Outcome logged with consent + transfusion details

**Telegram Bot Flow:**
User messages → Groq agent (tool-calling) → 10 tools (registration, emergency, history, leaderboard, etc.)
Multi-language (10 Indian languages) + language detection
DPDP 2023 privacy: sensitive fields (antibodies, hemoglobin) never sent via Telegram

---

## Core Conventions
- **All API responses:** Follow structure from `models/schemas.py`
- **Async:** async/await throughout. FastAPI dependencies use Depends()
- **Errors:** Custom HTTPException with proper status codes
- **Environment:** Read from `core/config.py` — no hardcoded secrets
- **Logging:** Use `logging.getLogger(__name__)` in each module
- **Database:** Supabase for transactional data, Neo4j for graph relationships
- **Type hints:** Full type annotations required in all function signatures
- **Auth:** JWT tokens (7 days) for staff/donors/patients from `/api/auth/login`

---

## Key Tables (Supabase PostgreSQL — 12 Total)
| Table | Purpose |
|-------|----------|
| `donors` | Blood donors (phone, blood_type, location, antigen flags, churn_score) |
| `patients` | Patients needing transfusions (blood_type, hospital, antibody flags) |
| `emergency_requests` | Emergency coordination requests (status: IN_PROGRESS/COMPLETED/ESCALATED) |
| `blood_chains` | Donor chain position + confirmation status per emergency |
| `gamification` | Badges, challenge completions, lives saved tracking |
| `donor_memory` | Interaction history for donor personalization (language prefs, donation patterns) |
| `consent_records` | DPDP 2023 consent tracking (data_storage, outreach flags) |
| `staff` | Hospital coordinators/admin staff with roles |
| `transfusion_schedule` | Scheduled transfusions for proactive outreach |
| `leaderboard_cache` | City-level rankings, lives_saved leaderboard (monthly/real-time) |
| `agent_traces` | LangGraph execution logs |
| `donor_verifications` | Blood card OCR + verification records |
| `agent_traces` | LangGraph pipeline execution logs for debugging |

---

## Key Agents (LangGraph 14-node graph)
- **Intake** → Fetch patient profile, detect language
- **Eligibility** → Check medical holds, blood type match
- **Antigen Scorer** → Score donor compatibility (0-100)
- **Urgency Scorer** → Score request urgency (critical vs routine)
- **Neo4j Matcher** → Find top 8 geographically + antigen-compatible donors
- **Conflict Resolver** → Handle antigen conflicts
- **Planner** → Choose outreach sequence (Telegram → Voice → SMS)
- **Outreach** → Send alerts via Telegram/Vapi/Twilio
- **Monitor** → Track donor confirmations, timeouts, auto-escalations
- **Repair** → Auto-alert next donor if previous declines
- **Inventory** → Low blood stock detection & alerts
- **Voice Agent** → Vapi.ai outbound call handler (Sarvam AI TTS, 10 Indian langs)
- **Gamification** → Award badges, update leaderboards
- **Outcome** → Log transfusion results, consent, reward donors

---

## Environment Variables (24 Required)
```
SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
GROQ_API_KEY, GEMINI_API_KEY
TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL, TELEGRAM_WEBHOOK_SECRET
VAPI_API_KEY, VAPI_PHONE_NUMBER_ID, VAPI_WEBHOOK_SECRET
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_DLT_SENDER_ID, TWILIO_DLT_TEMPLATE_ID_HI/EN
NTFY_TOPIC
APP_ENV, APP_HOST, APP_PORT, APP_BASE_URL, LOG_LEVEL, DEMO_MOCK_MODE, WEB_PORTAL_URL
```

---

## Current Status
- **Health:** 🟢 Stable (all agents deployed, real-time chain monitoring)
- **Test Status:** ⚠️ Integration tests in `tests/` (Supabase + Neo4j required)
- **Active Feature:** Proactive transfusion scheduling via APScheduler

---

## 🚫 Never Do
- ❌ Hardcode API keys — use `core/config.py`
- ❌ Query Supabase without exception handling — always try/catch
- ❌ Modify agents without understanding LangGraph StateGraph routing
- ❌ Add Telegram alert fields that are in SENSITIVE_FIELDS (privacy law)
- ❌ Use requests library — use httpx (async-first)
- ❌ Send medical data via unencrypted channels

---

## Next Steps
→ Read `CODEBASE_MAP.md` for complete architecture & module index
→ Read `CODEBASE_TRACKER.md` for pending TODOs and session history
→ Read source files only as needed for specific tasks
