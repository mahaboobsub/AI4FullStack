# BloodBridge AI — PRD v5.0
## Definitive · Agentic AI · LangGraph · Full-Stack · Free-Tier-First · Zero-AWS

**Team:** Inqilab | DNR College of Engineering and Technology
**Members:** Marre Dinesh (Full-Stack + AI Lead) · Sheik Mahaboob Subhani (Full-Stack + AI)
**Hackathon:** Blend360 — AI for Blood Donation & Care Coordination
**Dev window:** 2–3 days pre-hackathon + demo day
**Deployment:** 100% free cloud — Render.com + Supabase + Vercel + Telegram (₹0 total)
**AI Dev tool:** AI Antigravity (accelerated code generation throughout)
**Demo cost:** ₹0 on free-tier path

---

## CHANGELOG: v4 → v5

| # | Change | Reason |
|---|---|---|
| 1 | **LangGraph replaces custom ReAct loop** | Production-grade agent orchestration, stateful graph, built-in retry/fallback |
| 2 | **WhatsApp → Telegram (confirmed)** | Zero approval, zero cost, 2-min setup via @BotFather, Bot API is free forever |
| 3 | **Full-Stack Web App added** | Complete React/Next.js dashboard + FastAPI backend — not just a Telegram bot |
| 4 | **All agents are autonomous LangGraph nodes** | True agentic AI workflow — every agent is a stateful graph node with memory |
| 5 | **Node.js decision resolved** | Node.js NOT needed — FastAPI handles all backend including WebSocket for real-time dashboard |
| 6 | **Frontend expanded to 5 dashboard UIs** | Emergency OC, Neo4j Graph, Blood Map, Donor Engagement, Admin Config |
| 7 | **Full technology stack listed** | Every library, tool, service with version and role |
| 8 | **Detailed feature data-flows added** | Every feature has step-by-step data flow |
| 9 | **Database architecture expanded** | Supabase schema + Neo4j schema + Redis (in-memory) fully specified |

---

## MASTER ALIGNMENT MATRIX

### A — Problem Statement Coverage (15/15)

| # | Requirement | BloodBridge AI Solution | Agent | Built in 3 days? |
|---|---|---|---|---|
| 1 | Matching donors to patients — manual effort | 8-antigen scorer + Neo4j COMPATIBLE_WITH | MatchingAgent (LangGraph) | ✓ |
| 2 | Coordinating across multiple stakeholders | LangGraph StateGraph orchestration | PlannerAgent (LangGraph) | ✓ |
| 3 | Maintaining engagement — difficult | Churn prediction → personalized AI voice call | ChurnAgent + OutreachAgent | ✓ |
| 4 | Scaling across cities and organizations | Render.com serverless + Telegram zero-install | Scale infra | ✓ Architecture |
| 5 | Stay connected at the right time | Chain monitor → ntfy.sh staff alerts | ChainMonitorAgent | ✓ |
| 6 | Intuitive adaptive interactions across languages | langdetect → Groq/Gemini in detected language | Multilingual layer | ✓ |
| 7 | Remember and respond over repeated interactions | Supabase donor_memory per phone number | Donor Memory Store | ✓ |
| 8 | Identify and prioritize right donors | XGBoost urgency scorer → priority queue | MatchingAgent | ✓ |
| 9 | Anticipate availability / willingness | XGBoost churn predictor — 3-week advance warning | ChurnAgent | ✓ |
| 10 | Encourage continued donor participation | Gamification: badges, leaderboard, challenges | GamificationAgent | ✓ |
| 11 | Build long-term engagement mechanisms | scikit-learn SVD + persistent donor memory | OutreachAgent | ✓ |
| 12 | Feedback loops that feel responsive and human | /confirm → badge → "Shukriya" Telegram | OutcomeTrackerAgent | ✓ |
| 13 | Work across large diverse population | Telegram (500M+ users), zero app download | Channel strategy | ✓ |
| 14 | Adapt to language, accessibility, infrastructure | 10+ Indian languages via langdetect | langdetect + gTTS | ✓ |
| 15 | Ensure efficiency while expanding to regions | Render.com auto-scale, per-ward routing | Render + City Router | ✓ Architecture |

### B — Evaluator Gaps All Closed (8/8)

| Evaluator Gap | How v5 Closes It |
|---|---|
| Only ABO matching | 8-antigen weighted scorer + Neo4j COMPATIBLE_WITH edges with antigen_score |
| No antibody history stored | Patient Supabase record: antibody_flags[], needs_kell_neg, needs_duffy_neg |
| No urgency scoring | XGBoost urgency model: Hgb + days_since_tx + flags → CRITICAL/HIGH/ROUTINE |
| No conflict resolver | Gemini LLM: 2 patients + 1 rare donor → JSON priority + justification |
| No chain break recovery | ChainMonitorAgent auto-repair: DECLINED → next donor alerted in seconds |
| No closed feedback loop | /confirm → outcome → Neo4j + Supabase + badge + leaderboard + model data |
| Donor eligibility not verified | Rule engine: 56-day gap, Hgb threshold, medical hold flag — before any alert |
| Stateless chatbot | Supabase donor_memory per phone: lang, tone, context, past anchors |

---

## PART 1 — PROBLEM CONTEXT

### 1.1 Clinical Reality of Thalassemia

Thalassemia Major patients require lifelong transfusions — 500–700 per lifetime. After 10+ transfusions, patients develop allo-antibodies against minor blood antigens (Kell, Duffy, Kidd, Rh subtypes). Sending ABO-compatible blood that ignores these antibodies triggers a Delayed Hemolytic Transfusion Reaction — potentially fatal. Simple blood type matching is clinically insufficient for this patient population.

### 1.2 Operational Scale

| Metric | Value |
|---|---|
| Patients in network | 100,000+ |
| Transfusions per lifetime | 500–700 |
| Monthly coordination events | 6,000+ |
| Current active donor rate | ~40% |
| Staff time on manual coordination | ~80% |
| Donors per Blood Bridge chain | 8–10 |
| Generic broadcast reminder response rate | 15% |
| Personalized AI call response rate (target, projected) | 67%* |

*Projected based on personalization design. Will be validated in pilot with Blood Warriors' 40,000 donor records.

### 1.3 The Four Core Problems

**Problem A — Matching:** Manual lookup + broadcast messaging. No antigen phenotyping. No antibody history. No urgency scoring. No conflict resolution when 2 critical patients need 1 rare donor.

**Problem B — Coordination:** Blood Bridge chains of 8–10 donors collapse when 1 node fails. 80% staff time consumed by manual follow-up. No automated chain repair. No fallback to blood bank stock.

**Problem C — Engagement:** 40% donors inactive. Generic reminders get 15% response rate. Donors don't see their impact and drift away. No personalization, no emotional feedback loop.

**Problem D — Scale:** 36 states, 22+ languages, patchy infrastructure. Partner organizations have no integration point.

---

## PART 2 — SOLUTION OVERVIEW

### 2.1 What BloodBridge AI Is

A full-stack agentic AI platform with LangGraph-orchestrated autonomous agents, a Neo4j graph database, and a complete React web dashboard — automating emergency blood donor coordination end-to-end: from patient Telegram request or dashboard entry to transfusion confirmation — accessible via Telegram with zero installation, or via the web dashboard for staff.

### 2.2 Why Node.js Is NOT Needed

> **Decision: FastAPI only for backend. No Node.js.**

Here is the rationale:

| Concern | Why FastAPI Handles It |
|---|---|
| Real-time dashboard updates | FastAPI supports WebSocket natively — `fastapi.WebSocket` |
| Telegram webhook | `python-telegram-bot` + FastAPI POST endpoint — no Express needed |
| LangGraph agents | LangGraph is a Python library — runs natively in FastAPI |
| ML inference | XGBoost, scikit-learn, all Python — would need a Python sidecar anyway if Node.js |
| Neo4j driver | `neo4j` Python driver — official, full-featured |
| Supabase client | `supabase-py` — full CRUD + auth |
| Background jobs | APScheduler + Render.com cron — Python native |
| Performance | FastAPI with Uvicorn is async and handles 10K+ req/min on free tier |

**Node.js would add:** a second runtime, two deployment services, inter-process HTTP calls, duplicated environment variables, and coordination overhead — with zero benefit. FastAPI + Python is the single correct choice for an AI-heavy backend.

### 2.3 Confirmed Technology Stack

#### Frontend
| Technology | Version | Role |
|---|---|---|
| **Next.js** | 14.x (App Router) | Full-stack React framework — SSR + CSR, routing, API routes for lightweight proxying |
| **React** | 18.x | UI component library |
| **TypeScript** | 5.x | Type safety across all frontend code |
| **Tailwind CSS** | 3.x | Utility-first styling — fast development |
| **shadcn/ui** | Latest | Pre-built accessible components (cards, tables, badges, dialogs) |
| **react-force-graph** | 1.x | Neo4j Blood Bridge chain visualization — 3D/2D graph rendering |
| **Leaflet.js + react-leaflet** | 4.x | Blood availability map — Hyderabad blood banks |
| **Recharts** | 2.x | Analytics charts — donation trends, churn distribution, urgency histogram |
| **Socket.io-client** | 4.x | WebSocket client → FastAPI WebSocket server for live dashboard updates |
| **Axios** | 1.x | HTTP client for REST API calls to FastAPI backend |
| **Vercel** | — | Hosting, CDN, CI/CD from GitHub, free tier (100 GB bandwidth) |

#### Backend
| Technology | Version | Role |
|---|---|---|
| **FastAPI** | 0.115.x | Async Python web framework — all REST endpoints + WebSocket server |
| **Uvicorn** | 0.30.x | ASGI server — runs FastAPI on Render.com |
| **LangGraph** | 0.2.x | Agentic AI orchestration — StateGraph for all 8 autonomous agents |
| **LangChain** | 0.3.x | LLM abstraction layer — Groq + Gemini unified interface, tool calling |
| **Groq SDK** | 0.10.x | Llama-3.3-70B — fast LLM for Telegram real-time responses |
| **Google Generative AI SDK** | 0.7.x | Gemini 1.5 Flash — reasoning, conflict resolution, outreach |
| **python-telegram-bot** | 21.5 | Telegram Bot API — all 8 commands + free-text handler + photo OCR |
| **neo4j Python driver** | 5.21.x | Neo4j Aura Free — graph queries, chain management |
| **supabase-py** | 2.7.x | Supabase PostgreSQL — all structured data + donor memory |
| **XGBoost** | 2.1.x | Churn predictor + urgency scorer — both models |
| **scikit-learn** | 1.5.x | SVD matrix factorization for challenge recommendations |
| **joblib** | 1.4.x | ML model serialization (.joblib files in repo) |
| **langdetect** | 1.0.9 | Offline language detection — 55 languages, runs in-process |
| **pytesseract + Pillow** | 0.3.13 / 10.4.x | Tesseract OCR — blood group card photo → blood type |
| **gTTS** | 2.5.x | Google TTS — Hindi/Telugu/Tamil audio for voice calls |
| **Twilio SDK** | 9.2.x | Outbound voice calls — TwiML, STT gather |
| **APScheduler** | 3.10.x | In-process scheduled agents — chain monitor (5 min), inventory (15 min) |
| **pandas** | 2.2.x | Data processing for synthetic data + churn batch |
| **numpy** | 1.26.x | Feature engineering for ML models |
| **faker** | 26.x | Synthetic data generation (500 donors, 50 patients) |
| **httpx** | 0.27.x | Async HTTP client for e-RaktKosh scraping |
| **beautifulsoup4** | 4.12.x | HTML parsing for e-RaktKosh blood stock scraper |
| **python-dotenv** | 1.0.x | Local .env loading |
| **Render.com** | — | Backend hosting: FastAPI web service + cron job, Singapore region |

#### Databases
| Database | Service | Role |
|---|---|---|
| **PostgreSQL** | Supabase (free, 500MB) | All structured data: donors, patients, chains, gamification, memory, blood stock cache |
| **Graph DB** | Neo4j Aura Free (200K nodes) | Blood Bridge chains, compatibility edges, hospital-bank proximity |
| **In-Memory Store** | Python dict + APScheduler state | Active emergency session state, chain status cache (no Redis needed on free tier) |

#### External Services & APIs
| Service | Role | Free Tier |
|---|---|---|
| **Telegram Bot API** | Primary user channel — donors + hospital staff | Unlimited messages, free forever |
| **Groq** | Llama-3.3-70B real-time LLM | 14,400 req/day |
| **Gemini 1.5 Flash** | Reasoning + outreach + conflict resolver | 1M tokens/day |
| **Twilio Voice** | Outbound AI voice calls | $15 trial (~600 min) |
| **ntfy.sh** | Staff push alerts (chain break, CRITICAL patient) | Unlimited topics, free |
| **UptimeRobot** | Render.com keep-alive ping every 5 min | 50 monitors free |
| **e-RaktKosh** | Government blood bank inventory portal | Public portal, scraper or mock |
| **GitHub** | Source control + Render.com CI/CD trigger | Free |

---

## PART 3 — LANGGRAPH AGENTIC AI ARCHITECTURE

### 3.1 Why LangGraph

LangGraph is a stateful, graph-based agent orchestration framework from LangChain. It replaces the custom ReAct loop from v4 with production-grade agent coordination:

| Feature | Custom ReAct (v4) | LangGraph (v5) |
|---|---|---|
| State management | Manual Python dict | Typed `AgentState` dataclass — persisted across nodes |
| Agent routing | if/else chain | Conditional edges — graph decides next node |
| Retry/fallback | Manual try/catch | Built-in retry policy per node |
| Parallelism | Sequential | Parallel branches (alert multiple donors simultaneously) |
| Observability | print() | LangGraph trace — every node input/output logged |
| Memory | In-process only | Checkpointer → Supabase persistence |
| Human-in-loop | Not possible | Built-in interrupt_before for CRITICAL decisions |

### 3.2 LangGraph StateGraph — Master Architecture

```
BloodBridgeGraph (StateGraph)
│
├── [ENTRY] intake_node
│     ↓ (parse request + fetch patient from Supabase)
│
├── eligibility_filter_node
│     ↓ (56-day gap, medical hold, concurrent alert check)
│
├── antigen_scoring_node          ──parallel──→  urgency_scoring_node
│     ↓ (8-antigen scorer)                        ↓ (XGBoost urgency)
│     └──────────────────────────────────────────┘
│                        ↓ (join)
│
├── neo4j_matching_node
│     ↓ (COMPATIBLE_WITH Cypher query, rank by antigen_score + proximity)
│
├── conflict_resolver_node        ← only if 2+ CRITICAL patients share 1 rare donor
│     ↓ (Gemini JSON priority decision)
│
├── planner_node                  ← Gemini decides: Telegram first or Voice first?
│     ↓ (builds action plan: which 8 donors, which channel, which language)
│
├── outreach_node                 ← parallel fan-out to 8 donors
│     ├── donor_1_branch → langdetect → Groq → Telegram send
│     ├── donor_2_branch → langdetect → Groq → Telegram send
│     └── ... (up to 8 parallel branches)
│
├── [LOOP] chain_monitor_node     ← APScheduler calls this every 5 min
│     ↓ Cypher: find ALERTED nodes > 7 min old
│     ├── [CONFIRMED] → gamification_node → outcome_node → END SUCCESS
│     ├── [NO RESPONSE] → voice_agent_node → [loop back to monitor]
│     └── [DECLINED] → chain_repair_node → [next donor in chain]
│
├── chain_repair_node
│     ↓ (Neo4j: mark broken, find next chain position, alert next donor)
│     └── [3 consecutive fails] → inventory_agent_node → escalate_node
│
├── voice_agent_node
│     ↓ Gemini script → gTTS → Twilio → Keyword NLU → Neo4j update
│
├── inventory_agent_node
│     ↓ e-RaktKosh Supabase cache → top 3 blood banks → Planner
│
├── gamification_node
│     ↓ badge check → leaderboard update → /mystats response
│
├── outcome_node
│     ↓ /confirm → Supabase patient + donor → Neo4j COMPLETED → model data
│
└── escalate_node                 ← ntfy.sh push → staff dashboard alert
      ↓ (human coordinator takes over)
      └── END ESCALATED
```

### 3.3 AgentState (Typed — Shared Across All Nodes)

```python
from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages
from datetime import datetime

class AgentState(TypedDict):
    # Request context
    request_id: str
    patient_id: str
    blood_type: str
    city: str
    ward: str
    
    # Patient clinical data (fetched from Supabase in intake_node)
    hemoglobin: float
    days_since_last_transfusion: int
    needs_kell_negative: bool
    needs_duffy_negative: bool
    antibody_flags: List[str]
    urgency_score: float          # 0–10, set by urgency_scoring_node
    priority: str                 # CRITICAL / HIGH / ROUTINE
    hospital_name: str
    hospital_lat: float
    hospital_lng: float
    
    # Matching outputs
    eligible_donors: List[dict]   # After eligibility_filter_node
    scored_donors: List[dict]     # After antigen_scoring_node + neo4j_matching_node
    ranked_donors: List[dict]     # Final ranked list from planner_node
    
    # Coordination state
    chain_status: dict            # {donor_id: status} — updated by chain_monitor_node
    alerted_donors: List[str]     # donor_ids already alerted
    confirmed_donors: List[str]   # donor_ids who confirmed
    declined_donors: List[str]    # donor_ids who declined
    
    # Conflict resolution
    conflict_detected: bool
    conflict_resolution: Optional[dict]  # Gemini JSON output
    
    # Communication
    messages: Annotated[list, add_messages]  # LangGraph message history
    outreach_results: List[dict]  # {donor_id, channel, status, sent_at}
    
    # Voice
    voice_calls_active: List[str] # donor_ids currently on call
    
    # Inventory fallback
    blood_bank_options: List[dict]
    
    # Agent decisions
    next_action: str              # planner decision for routing
    retry_count: int              # chain monitor retry counter
    
    # Outcome
    outcome: str                  # SUCCESS / ESCALATED / IN_PROGRESS
    completed_at: Optional[datetime]
    agent_log: List[dict]         # Full audit trail of every node execution
```

---

## PART 4 — COMPLETE FEATURE LIST WITH DETAILED DATA FLOWS

### FEATURE 1 — Emergency Blood Request (Core Feature)

**What it does:** When a patient urgently needs blood, a hospital staff member sends a Telegram command. The LangGraph pipeline autonomously finds the top 8 compatible donors, sends personalized multilingual outreach, and monitors responses — all without human intervention.

**Trigger:** Staff types `/emergency B+ Hyderabad Secunderabad P-10234` in Telegram

**Step-by-Step Data Flow:**

```
Step 1: INTAKE
  Input:  Telegram message text
  Process:
    - python-telegram-bot routes to /emergency handler
    - langdetect detects language of message text
    - Parse: blood_type="B+", city="Hyderabad", ward="Secunderabad", patient_id="P-10234"
    - Supabase SELECT * FROM patients WHERE patient_id='P-10234'
    - Supabase SELECT * FROM donors WHERE city='Hyderabad' AND blood_type IN (compatible_types)
    - Create AgentState, assign request_id = uuid4()
    - Write AgentState to Supabase emergencies table (initial log entry)
    - Initialize LangGraph StateGraph with AgentState
  Output: Populated AgentState, LangGraph graph starts execution

Step 2: ELIGIBILITY FILTER (eligibility_filter_node)
  Input:  All donors matching city + blood type from Supabase (~150 donors)
  Process:
    - Rule 1: days_since_donation >= 56 (hard block — iron recovery period)
    - Rule 2: medical_hold == False
    - Rule 3: NOT in currently_alerted set (no duplicate alerts)
    - Rule 4: is_active == True (not formally deregistered)
    - Rule engine is pure Python — deterministic, no LLM, no API call
  Output: eligible_donors list (~60–80 donors typically)

Step 3: ANTIGEN SCORING (antigen_scoring_node) ← runs in parallel with Step 4
  Input:  eligible_donors, patient antibody_flags
  Process:
    - For each eligible donor:
      score = 1.0
      if ABO incompatible: score = 0.0 (skip)
      if patient.needs_kell_neg AND NOT donor.kell_negative: score -= 0.35
      if patient.needs_duffy_neg AND NOT donor.duffy_negative: score -= 0.25
      if patient.needs_kidd_safe AND NOT donor.kidd_positive: score -= 0.20
      + Rh-E, Rh-C, MNS penalty checks
      if days_since_donation < 56: score = 0.0 (redundant safety check)
    - Filter: score > 0.60 (minimum acceptable compatibility)
  Output: scored_donors list with antigen_score per donor

Step 4: URGENCY SCORING (urgency_scoring_node) ← runs in parallel with Step 3
  Input:  patient hemoglobin, days_since_last_transfusion, cardiac_flag, splenomegaly_flag, queue_length
  Process:
    - Load XGBoost urgency model from models/urgency_model.joblib (cached in /tmp)
    - feature_vector = [hgb, days_since_tx, cardiac_flag, splenomegaly_flag, queue_len]
    - urgency_score = xgb_urgency.predict(feature_vector)[0]  # 0.0–10.0
    - priority = "CRITICAL" if score >= 8 else "HIGH" if score >= 5 else "ROUTINE"
    - Write urgency_score + priority to Supabase patients table
  Output: urgency_score, priority added to AgentState

Step 5: NEO4J MATCHING (neo4j_matching_node)
  Input:  scored_donors (antigen_score per donor)
  Process:
    - Cypher query:
        MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p:Patient {patient_id: $pid})
        WHERE d.donor_id IN $eligible_ids
          AND c.antigen_score >= 0.80
          AND c.kell_safe = $needs_kell_safe
        WITH d, c,
          point.distance(
            point({latitude: d.lat, longitude: d.lng}),
            point({latitude: $hosp_lat, longitude: $hosp_lng})
          ) AS dist_m
        ORDER BY c.antigen_score DESC, dist_m ASC
        LIMIT 8
        RETURN d.donor_id, d.name, d.phone, d.telegram_chat_id,
               c.antigen_score, dist_m/1000 AS dist_km
    - Re-rank scored_donors using graph antigen_score + proximity
    - Create IN_CHAIN relationships in Neo4j:
        CREATE (d:Donor)-[:IN_CHAIN {chain_position: $pos, status: 'PENDING',
                                      alerted_at: null}]->(p:Patient)
    - Write chain to Supabase chains table (mirror for SQL queries)
    - Push chain state to WebSocket → React dashboard updates instantly
  Output: ranked_donors top 8, Neo4j chain initialized

Step 6: CONFLICT RESOLUTION (conflict_resolver_node) ← only if triggered
  Input:  ranked_donors, AgentState for other CRITICAL patients sharing rare donors
  Process:
    - Check: is this rare donor (kell_negative or AB-) also in top-3 of another CRITICAL patient?
    - If yes: build Gemini prompt:
        "Patient A: urgency 9.2, Hgb 4.1, 12 days since tx, needs Kell-neg B+
         Patient B: urgency 8.7, Hgb 4.8, 8 days since tx, needs Kell-neg B+
         Donor X is the only Kell-negative B+ donor available within 25km.
         Return JSON: {priority_patient, reasoning, fallback_for_other}"
    - Gemini returns structured JSON with priority decision
    - Timeout: 1.5 seconds hard limit → fallback: higher urgency_score wins
    - Log conflict resolution to Supabase emergencies.agent_log
    - Require human coordinator confirmation before executing (LangGraph interrupt_before)
  Output: conflict_resolution dict, priority patient confirmed

Step 7: PLANNER (planner_node)
  Input:  ranked_donors (top 8), urgency, donor memory from Supabase
  Process:
    - Gemini prompt:
        "Given 8 donors ranked by compatibility and proximity,
         urgency CRITICAL, patient at KIMS Secunderabad.
         Decide: send Telegram now (fast) or start with voice calls (higher response)?
         Return JSON: {strategy, channel_per_donor, message_tone}"
    - Fetch donor_memory for each donor: preferred_language, tone_profile, past_anchors
    - Build per-donor outreach plan
  Output: outreach plan with channel + language + tone per donor

Step 8: OUTREACH (outreach_node) ← parallel fan-out
  Input:  outreach plan (8 donors with channel + language + tone)
  Process:
    - LangGraph parallel branches — one per donor, all fire simultaneously
    - For each donor branch:
        a. langdetect confirms language (fallback: donor_memory.preferred_language)
        b. Groq Llama-3.3-70B generates personalized message in donor's language:
             Prompt: "Generate urgent blood donation request in {language}.
                      Donor name: {name}. Lives saved: {lives_saved}.
                      Blood type needed: {blood_type}. Hospital: {hospital}.
                      Tone: {tone_profile}. Max 150 chars for Telegram."
        c. Telegram Bot API: send message to donor.telegram_chat_id
        d. Neo4j: update IN_CHAIN status = 'ALERTED', alerted_at = now()
        e. Supabase chains: update status = 'ALERTED'
        f. WebSocket push → dashboard: donor node turns orange
    - Update AgentState.alerted_donors, outreach_results
  Output: 8 Telegram messages sent, Neo4j + Supabase updated, dashboard live

Step 9: CHAIN MONITOR (chain_monitor_node) ← APScheduler calls every 5 min
  Input:  AgentState for all active emergencies
  Process:
    - Cypher: find ALERTED nodes where alerted_at < now() - 7 minutes
    - For each stale ALERTED node:
        → async invoke voice_agent_node
    - Cypher: find DECLINED or UNREACHABLE nodes
    - For each broken node:
        → chain_repair_node
    - If all 8 donors confirmed → outcome_node → END SUCCESS
    - If 3 consecutive broken → inventory_agent_node → escalate_node
    - WebSocket push → dashboard updates chain visualization
  Output: Auto-repairs, voice calls triggered, escalation if needed

Result: Staff receives Telegram confirmation "8 donors alerted for P-10234 B+ CRITICAL.
         Chain: D1 ✅ D2 ⏳ D3 ⏳ D4 ⏳ D5 ⏳ D6 ⏳ D7 ⏳ D8 ⏳"
```

---

### FEATURE 2 — AI Voice Calling (Chain Recovery)

**What it does:** When a donor doesn't respond to Telegram within 7 minutes, the system automatically calls them with a personalized Hindi/regional-language AI voice message. The donor's spoken response is classified by Keyword NLU and the chain is updated live.

**Trigger:** ChainMonitorAgent finds ALERTED node > 7 minutes old (or ChurnAgent for CRITICAL churn)

**Step-by-Step Data Flow:**

```
Step 1: SCRIPT GENERATION (voice_agent_node)
  Input:  donor dict (name, language, lives_saved, tone), patient dict (blood_type, hospital)
  Process:
    - Gemini prompt:
        "Write a 30-second spoken voice call script in {language}.
         Caller is BloodBridge AI system. Keep it warm, personal, urgent.
         Mention donor's first name, blood type needed, hospital name,
         and how many lives they've saved. End with a clear yes/no question.
         Output: plain text only, no formatting."
    - Gemini returns ~60-word script in donor's language
    - Example (Hindi):
        "Namaste Rahul bhai, BloodBridge se call kar raha hoon.
         Ek bachche ko aaj B+ blood chahiye KIMS mein.
         Aapne 12 logon ki zindagi bachaayi hai.
         Kya aaj bhi kar sakte hain? Haan ya nahi bolein."
  Output: voice_script (plain text, ~60 words)

Step 2: TEXT-TO-SPEECH (gTTS)
  Input:  voice_script, donor.preferred_language
  Process:
    - Language → gTTS lang code map:
        Hindi → 'hi', Telugu → 'te', Tamil → 'ta',
        Kannada → 'kn', Bengali → 'bn', English → 'en'
    - gTTS(text=voice_script, lang=lang_code, slow=False).write_to_fp(buffer)
    - Upload mp3 buffer to Supabase Storage bucket 'voice-clips'
    - Get public URL from Supabase Storage
  Output: public_audio_url (mp3, ~15 seconds audio)

Step 3: TWILIO OUTBOUND CALL
  Input:  donor.phone, public_audio_url, donor_id
  Process:
    - Build TwiML:
        <Response>
          <Play>{public_audio_url}</Play>
          <Gather input="speech" timeout="4" language="{twilio_lang_code}"
                 action="/webhook/voice-response?donor_id={donor_id}">
            <Play>{audio_repeat_url}</Play>
          </Gather>
          <Play>{farewell_audio_url}</Play>
        </Response>
    - Twilio: client.calls.create(to=donor.phone, from_=TWILIO_NUMBER, twiml=twiml_str)
    - Neo4j: update IN_CHAIN voice_call_initiated = True
    - WebSocket push: dashboard shows pulsing edge on donor's graph node
  Output: Twilio call SID, donor phone ringing

Step 4: KEYWORD NLU (voice response webhook)
  Input:  Twilio POST to /webhook/voice-response (SpeechResult text)
  Process:
    - speech_text received (e.g., "haan kar sakta hoon")
    - Keyword NLU classify:
        INTENT_KEYWORDS = {
          'ConfirmDonation':   ['haan', 'yes', 'ha', 'kar sakta', 'theek', 'bilkul', 'zaroor'],
          'DeclineDonation':   ['nahi', 'no', 'busy', 'abhi nahi', 'na', 'nahin', 'mana'],
          'RequestReschedule': ['kal', 'tomorrow', 'baad', 'later', 'shaam', 'evening'],
          'AskMoreInfo':       ['kahan', 'where', 'kab', 'when', 'hospital', 'kitna'],
        }
        scores = {intent: count of keywords found in speech_text}
        intent = argmax(scores) if max > 0 else 'AskMoreInfo'
  Output: intent classification

Step 5: CHAIN UPDATE
  Input:  intent, donor_id
  Process:
    CONFIRM:
      - Neo4j: IN_CHAIN status = 'CONFIRMED', confirmed_at = now()
      - Supabase chains: status = 'CONFIRMED'
      - Supabase donors: lives_saved += 1
      - Telegram to donor: "Shukriya Rahul bhai! Aap ek Blood Hero hain! 🏆"
      - Invoke gamification_node: badge check + leaderboard update
      - WebSocket push: donor node turns GREEN in dashboard
    DECLINE:
      - Neo4j: IN_CHAIN status = 'DECLINED'
      - Invoke chain_repair_node: alert next chain_position donor
      - WebSocket push: donor node turns RED, next node turns ORANGE
    RESCHEDULE:
      - Store reschedule_time in Supabase
      - APScheduler: one-time job at reschedule_time to re-trigger outreach
    ASK_MORE_INFO:
      - Continue TwiML: play hospital address + blood type audio
      - Loop back to gather intent
  Output: Chain updated, downstream agents triggered, dashboard live
```

---

### FEATURE 3 — 8-Antigen Compatibility Matching

**What it does:** Scores each donor against the patient's precise antigen requirements across 8 blood antigen systems — far beyond simple ABO/Rh matching. Prevents Delayed Hemolytic Transfusion Reactions in Thalassemia patients.

**Trigger:** Called within MatchingAgent (antigen_scoring_node) for every emergency

**Data Flow:**
```
Input:  eligible_donors[], patient.antibody_flags, patient.blood_type
        patient.needs_kell_negative, patient.needs_duffy_negative, patient.needs_kidd_safe

Process:
  ABO_COMPATIBILITY = {
    'O-': all types, 'O+': O+/A+/B+/AB+, 'A-': A-/A+/AB-/AB+,
    'A+': A+/AB+, 'B-': B-/B+/AB-/AB+, 'B+': B+/AB+,
    'AB-': AB-/AB+, 'AB+': AB+ only
  }
  ANTIGEN_PENALTIES = {
    'kell_mismatch':  -0.35,  # Most immunogenic after ABO/Rh
    'duffy_mismatch': -0.25,  # High-risk in South Asian patients
    'kidd_mismatch':  -0.20,
    'rh_e_mismatch':  -0.15,
    'rh_c_mismatch':  -0.10,
    'mns_mismatch':   -0.05,
  }
  
  For each donor:
    1. ABO check: if patient.blood_type NOT in ABO_COMPAT[donor.blood_type] → score=0.0, skip
    2. Kell check: patient.needs_kell_neg AND NOT donor.kell_negative → score -= 0.35
    3. Duffy check: patient.needs_duffy_neg AND NOT donor.duffy_negative → score -= 0.25
    4. Kidd check: patient.needs_kidd_safe AND NOT donor.kidd_positive → score -= 0.20
    5. Rh-E check: patient.antibody_flags has 'anti-E' AND donor.rh_e_positive → score -= 0.15
    6. Rh-C check: patient.antibody_flags has 'anti-C' AND donor.rh_c_positive → score -= 0.10
    7. MNS check: patient.antibody_flags has 'anti-M' AND donor.mns_positive → score -= 0.05
    8. Final: score = max(0.0, round(score, 3))
    9. Filter: score >= 0.60 passes to Neo4j matching node

  Neo4j enrichment:
    - COMPATIBLE_WITH edge stores: antigen_score, kell_safe, duffy_safe, kidd_safe, rh_e_safe
    - Edge thickness in dashboard = antigen_score (visual indication of match quality)
    - Cypher re-ranks by antigen_score DESC, proximity ASC

Output: Each donor has antigen_score 0.0–1.0 + boolean safety flags
        Judges see: "Donor D-1023 — B+, Kell-neg, Duffy-neg, score 0.87, 4.2km away"
```

---

### FEATURE 4 — XGBoost Churn Prediction Engine

**What it does:** Runs every night at 8 PM IST. Scores every donor in the system on their likelihood to stop donating in the next 3 weeks. Automatically triggers different interventions based on risk tier — before the donor goes silent.

**Trigger:** Render.com cron job `30 14 * * *` (8 PM IST = 14:30 UTC)

**Data Flow:**
```
Step 1: BATCH SCAN (churn_agent_node)
  Input:  Supabase donors table (all 500+ donors)
  Process:
    - Supabase: SELECT donor_id, days_since_donation, avg_response_time_hours,
                       missed_alerts_last_90d, donation_count, gamification_events_30d,
                       response_rate, days_since_last_badge, preferred_contact_responded
               FROM donors
    - Load churn_model.joblib from /tmp (cached) or Supabase Storage (cold start)
  Output: DataFrame with 8 features per donor

Step 2: XGBOOST INFERENCE
  Input:  Feature DataFrame (N donors × 8 features)
  Process:
    - xgb_churn.predict_proba(X)[:, 1]  # Probability of churn
    - Feature importance (weights):
        days_since_last_donation      0.35
        avg_response_time_decay       0.20
        missed_alerts_ratio_90d       0.15
        gamification_events_30d       0.12
        donation_frequency_trend      0.10
        days_since_last_badge         0.05
        preferred_contact_responded   0.02
        donation_count_normalized     0.01
    - Segmentation:
        CRITICAL: score > 0.75 → voice call within 24h
        HIGH:     0.50–0.74   → Gemini outreach message
        MEDIUM:   0.25–0.49   → unlock new gamification challenge
        LOW:      < 0.25      → standard engagement cadence
  Output: churn_score + churn_risk per donor

Step 3: SUPABASE WRITE
  - UPDATE donors SET churn_score=$score, churn_risk=$risk
    WHERE donor_id=$id
  - Dashboard churn panel refreshes: top 30 at-risk donors visible

Step 4: INTERVENTION DISPATCH
  CRITICAL donors:
    - LangGraph: invoke voice_agent_node
    - Script: "Namaste {name}, aapko yaad kar rahe hain. {hospital} mein..."
  HIGH donors:
    - LangGraph: invoke outreach_agent_node
    - Gemini generates unique personalized Telegram message
    - Uses donor_memory.emotional_anchors, badges, lives_saved
    - Example: "Ramesh bhai, 3 mahine ho gaye. Priya (6 saal) ne apne
                 15th transfusion ki request ki hai. Woh aapko yaad karti hai."
  MEDIUM donors:
    - LangGraph: invoke gamification_node
    - Unlock new challenge: "Weekend Warrior — donate this weekend, earn Silver Badge"
    - Telegram: send challenge unlock notification
  LOW donors:
    - No action this cycle — preserve engagement quality

Output: All CRITICAL + HIGH donors receive personalized outreach before they go silent
```

---

### FEATURE 5 — Gamification Engine (Donor Loyalty)

**What it does:** Makes blood donation feel rewarding and visible. Donors earn badges, compete on leaderboards, get personalized challenges, and receive emotional impact stories. Designed to improve active donor rate from 40% to 85%.

**Trigger:** Telegram commands /mystats, /leaderboard, /challenge, /impact; also auto-triggered on every /confirm

**Data Flow:**
```
/MYSTATS COMMAND:
  Input:  telegram_chat_id
  Process:
    - Supabase: SELECT * FROM donors WHERE telegram_chat_id=$id
    - Supabase: SELECT * FROM gamification WHERE donor_id=$id
    - Build response:
        "🩸 Blood Hero Dashboard — Rahul Kumar
         ❤️ Lives Saved: 13
         💉 Total Donations: 13
         🏅 Badges: Blood Starter, Life Saver, Crisis Hero
         🏆 City Rank: #3 in Hyderabad this month
         ⭐ Next Badge: Blood Hero at 15 donations (2 away!)
         📊 Response Rate: 87%"
  Output: Telegram reply with stats

/LEADERBOARD COMMAND:
  Input:  telegram_chat_id, city
  Process:
    - Supabase: SELECT name, lives_saved, badges FROM donors
               WHERE city=$city ORDER BY lives_saved DESC LIMIT 10
    - Format: numbered list, highlight requesting donor's rank
    - First name only + city (privacy: no phone/last name)
  Output: Top 10 city donors, donor's own rank highlighted

/CHALLENGE COMMAND (scikit-learn SVD):
  Input:  donor profile features, all_donors list from Supabase
  Process:
    - Extract feature vector for this donor: [donation_count, response_rate, gamification_events_30d]
    - For all donors: build feature matrix X
    - StandardScaler normalize X and donor_vec
    - Cosine similarity: donor_vec · X.T → find top 10 similar donors
    - Check what challenges those similar donors completed most
    - Return the challenge with highest completion rate among similar donors
    - Cold start fallback (< 3 donations): use city + frequency rule
    - Format response:
        "🎯 Your Challenge: Weekend Warrior
         Donate between Friday and Sunday.
         73% of donors like you completed it!
         Reward: 🥈 Silver Badge + 10 Leaderboard XP
         Type /confirm after your donation!"
  Output: Personalized challenge recommendation

/IMPACT COMMAND (Gemini story):
  Input:  donor.lives_saved, donor.donation_count, anonymized patient data
  Process:
    - Fetch most recent patient this donor helped from Supabase chains table
    - Gemini prompt:
        "Write a 3-sentence emotional impact story for blood donor {name}.
         They donated blood type {type} for a 7-year-old Thalassemia patient
         at {hospital}. The patient received their {N}th transfusion successfully.
         Make it warm, human, anonymized (no patient name). In {language}."
    - Gemini returns story text
    - Example: "Aapke ek baar dene se ek 7 saal ki bachi apni 23vi transfusion
                 ke baad ghar ja payi. Uski maa ne kaha — 'koi anjaana farishta
                 tha.' Woh farishta aap hain, Rahul bhai."
  Output: Telegram impact story + "Next badge at {N} donations"

BADGE AWARD (auto on /confirm):
  Rules:
    donation_count == 1   → "Blood Starter" 🌱
    donation_count == 5   → "Life Saver" ❤️
    donation_count == 12  → "Blood Hero" 🦸
    same_day_response     → "Crisis Hero" ⚡ (responded within 2h of alert)
    kell_neg + count >= 3 → "Rare Guardian" 💎 (rare phenotype donor)
    top_3_city_month      → "City Champion" 🏆
  Process:
    - Check all rules against updated donation_count
    - New badge found: append to Supabase donors.badges[]
    - UPDATE gamification SET badges=$badges, donation_count=$count, lives_saved=$lives
    - Telegram: send badge award notification with emoji
    - WebSocket push: dashboard gamification panel updates
```

---

### FEATURE 6 — Blood Bridge Chain Monitoring & Auto-Repair

**What it does:** Continuously watches every active Blood Bridge chain. When a donor node fails (declined, unreachable, or timed out), the system automatically repairs the chain by alerting the next donor — maintaining supply without staff intervention.

**Trigger:** APScheduler runs chain_monitor_node every 5 minutes; also event-driven on DECLINED

**Data Flow:**
```
Step 1: STALE NODE DETECTION (Neo4j Cypher every 5 min)
  Cypher:
    MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
    WHERE r.status = 'ALERTED'
      AND r.alerted_at < datetime() - duration('PT7M')
    RETURN p.patient_id, d.donor_id, r.chain_position, r.alerted_at
    ORDER BY r.chain_position

  Output: list of stale ALERTED nodes

Step 2: VOICE ESCALATION
  For each stale node:
    - Invoke voice_agent_node (async, non-blocking)
    - Mark: IN_CHAIN voice_call_initiated = True
    - Wait up to 5 minutes for voice response (Twilio webhook)
    - If still no response after voice: mark UNREACHABLE

Step 3: BROKEN NODE DETECTION
  Cypher:
    MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
    WHERE r.status IN ['DECLINED', 'UNREACHABLE']
    RETURN p.patient_id, d.donor_id, r.chain_position
  
  For each broken node:
    - Find next chain_position donor (chain_position + 1)
    - If next donor exists in chain:
        - Alert them via Telegram (Groq message)
        - Neo4j: next donor status = 'ALERTED', alerted_at = now()
        - WebSocket push: broken node RED, next node ORANGE
    - Else (chain exhausted):
        - Invoke inventory_agent_node (blood bank fallback)
        - Invoke escalate_node (ntfy.sh → staff alert)

Step 4: CHAIN BREAK RECOVERY — INVENTORY FALLBACK
  Input:  patient.blood_type, hospital lat/lng
  Process:
    - inventory_agent_node:
        check Supabase blood_stock cache (15-min TTL)
        if cache miss: scrape e-RaktKosh portal
        Cypher: find blood banks near hospital with required blood type
          MATCH (b:BloodBank)
          WHERE b.units_{blood_type} > 0
          WITH b, point.distance(
            point({lat: b.lat, lng: b.lng}),
            point({lat: $hosp_lat, lng: $hosp_lng})
          ) AS dist_m
          ORDER BY dist_m LIMIT 3
          RETURN b.name, b.contact, b.units_{blood_type}, dist_m/1000 AS dist_km
    - Return top 3 blood banks with contact + units + drive time

Step 5: STAFF ESCALATION
  - ntfy.sh push: "CHAIN BREAK — Patient P-10234 B+ — 3 donors failed —
                   Blood bank fallback ready. Tap to view dashboard."
  - Supabase: emergency status = 'ESCALATED'
  - LangGraph: interrupt_before escalate_node (human coordinator reviews)
  - Dashboard: red pulsing banner "CHAIN BREAK — Human intervention needed"

Output: Chain auto-repaired in seconds OR escalated to staff with blood bank options
```

---

### FEATURE 7 — Multilingual Conversational Chatbot (Telegram)

**What it does:** Every Telegram interaction is in the donor's own language — detected automatically on first message and stored in memory. Hindi, Telugu, Tamil, Kannada, Bengali, Marathi, Gujarati, English + 47 others. All Groq responses are generated in the detected language.

**Trigger:** Any Telegram message (command or free text)

**Data Flow:**
```
Step 1: LANGUAGE DETECTION (every message)
  Input:  Telegram message text
  Process:
    - langdetect.detect(text) → ISO language code
    - Short message fallback (< 3 chars): use donor_memory.preferred_language
    - Unknown lang fallback: 'en' (English)
    - LANG_MAP: {hi: 'Hindi', te: 'Telugu', ta: 'Tamil', kn: 'Kannada',
                  bn: 'Bengali', mr: 'Marathi', gu: 'Gujarati', en: 'English'}
  Output: detected_language string

Step 2: MEMORY UPDATE (Supabase donor_memory)
  - Upsert: INSERT INTO donor_memory (phone, preferred_language, last_context, updated_at)
             VALUES ($phone, $lang, $text, NOW())
             ON CONFLICT (phone) DO UPDATE
               SET preferred_language = EXCLUDED.preferred_language,
                   last_context = EXCLUDED.last_context
  Output: donor_memory up to date

Step 3: GROQ LLM RESPONSE
  Input:  detected_language, command or free_text, donor context
  Process:
    - System prompt:
        "You are BloodBridge AI assistant for blood donation coordination in India.
         Respond ONLY in {detected_language}.
         Keep responses under 150 characters for Telegram.
         Tone: warm, urgent when needed, never robotic.
         Context: donor {name}, {donation_count} donations, {badges}."
    - User message: Telegram text
    - Groq Llama-3.3-70B: max 200 tokens, temperature 0.7
    - Timeout: 1.8 seconds → fallback to pre-written template in detected_language
  Output: Telegram reply in donor's language

Step 4: TESSERACT OCR (photo messages)
  Input:  donor sends photo of blood group card via Telegram
  Process:
    - python-telegram-bot: download photo bytes
    - Pillow: Image.open(BytesIO(photo_bytes))
    - pytesseract.image_to_string(image) → raw text
    - Regex: r'\b(A|B|AB|O)\s*[+\-](ve|positive|negative)?\b'
    - Match → normalize: "B +VE" → "B+"
    - Supabase UPDATE donors SET blood_type=$type WHERE telegram_chat_id=$id
    - Reply: "Blood type B+ detected and saved! You're ready to save lives. 🩸"
  Output: Blood type auto-extracted, profile updated, donor onboarded
```

---

### FEATURE 8 — e-RaktKosh Blood Bank Inventory Integration

**What it does:** Fetches live blood bank inventory from India's national e-RaktKosh portal (or a high-fidelity mock for demo). Shows on the dashboard blood availability map and feeds the inventory fallback during chain breaks.

**Trigger:** APScheduler every 15 minutes + event-driven on CHAIN_BREAK + dashboard map load

**Data Flow:**
```
Step 1: CACHE CHECK (Supabase blood_stock table)
  - SELECT * FROM blood_stock WHERE pk=$blood_type+'#'+$city
  - If expires_at > NOW(): return cached data (avoid hitting portal)
  - If cache miss or expired: proceed to scrape

Step 2: e-RAKTKOSH FETCH (try options in order)
  Option A (XHR reverse-engineer — fastest):
    - Chrome DevTools captured endpoint: POST to e-RaktKosh internal API
    - Headers: User-Agent, Referer, Content-Type mimicked
    - httpx.AsyncClient().post(url, data={bloodGroup, state, district})
    - Parse JSON response: blood_banks[]

  Option B (BeautifulSoup scraper — fallback):
    - requests.Session().post(portal_url, data=payload)
    - bs4 parse table rows → extract name, units, contact, address

  Option C (Supabase mock — demo safe):
    - Pre-populated with 15 real Hyderabad blood banks (manually collected)
    - Labeled in demo: "e-RaktKosh integration-ready, cached every 15 min"

  Post-hackathon (production path):
    - APISetu (api.setu.app) → Ministry of Health official blood bank API
    - Blood Warriors as registered NGO can apply

Step 3: SUPABASE CACHE WRITE
  - UPSERT blood_stock SET blood_banks=$data, expires_at=NOW()+INTERVAL '15 minutes'
    WHERE pk=$blood_type+'#'+$city

Step 4: NEO4J SYNC (blood bank nodes)
  - For each blood bank in data:
      MERGE (b:BloodBank {bb_id: $id})
      SET b.units_b_pos = $units, b.contact = $contact, b.updated_at = datetime()
  - Allows geo-proximity Cypher queries (nearest blood bank with required type)

Step 5: DASHBOARD MAP UPDATE (WebSocket push)
  - Emit: {event: 'blood_stock_update', banks: [...], updated_at: ...}
  - React Leaflet: update pin colors (green>5, yellow 1–5, red 0)

Output: Live blood availability on dashboard + Neo4j for chain fallback queries
```

---

### FEATURE 9 — Donor Onboarding & Memory System

**What it does:** First-time donors register via Telegram in under 2 minutes. Their profile (language, blood type, tone preference, emotional anchors) is stored in Supabase and used to personalize every future interaction — from emergency alerts to churn outreach.

**Trigger:** New donor sends /start to Telegram bot

**Data Flow:**
```
Step 1: /start COMMAND
  - Welcome message in English (default):
      "Welcome to BloodBridge AI! 🩸
       I connect blood donors with Thalassemia patients.
       Let's get you registered in 3 quick steps!"

Step 2: NAME & PHONE COLLECTION
  - Bot: "What's your name?"
  - Donor types name → stored in session state
  - Bot: "Your phone number? (We'll use it for emergency calls)"
  - Donor types → validated: must be 10-digit Indian number

Step 3: BLOOD TYPE COLLECTION
  - Option A: "Send a photo of your blood group card"
    → Tesseract OCR extracts blood type automatically
  - Option B: "Or type your blood type (A+, B-, O+, AB-, etc.)"
    → Regex validate → store

Step 4: LANGUAGE PREFERENCE
  - langdetect on all messages so far → detected_language
  - Bot switches to detected language from this point
  - Ask: "Any medical conditions we should know? (optional)"

Step 5: SUPABASE PROFILE CREATION
  INSERT INTO donors (donor_id, name, phone, telegram_chat_id, blood_type,
                       preferred_language, city, tone_profile, is_active, donation_count)
  VALUES (uuid4(), $name, $phone, $chat_id, $blood_type,
          $detected_lang, 'Unknown', 'motivational', True, 0)

Step 6: DONOR_MEMORY CREATION
  INSERT INTO donor_memory (phone, preferred_language, tone_profile,
                             emotional_anchors, last_context)
  VALUES ($phone, $detected_lang, 'motivational', '[]', 'onboarding')

Step 7: NEO4J NODE CREATION
  MERGE (d:Donor {donor_id: $donor_id})
  SET d.blood_type=$blood_type, d.lat=$lat, d.lng=$lng, d.is_eligible=False
  (eligible after 1st donation is recorded)

Step 8: CONFIRMATION
  "Shukriya {name}! 🎉 You're registered as a BloodBridge donor.
   We'll reach out only when a patient near you needs {blood_type} blood.
   Type /mystats anytime to see your impact.
   Type /help for all commands."

MEMORY UPDATE (every subsequent interaction):
  - Update donor_memory.last_context with last message summary
  - Update preferred_language if new detection differs (langdetect)
  - Track emotional_anchors: ["saved a child", "3-year streak", "Crisis Hero badge"]
  - These anchors are injected into every future Groq/Gemini prompt for personalization
```

---

### FEATURE 10 — Outcome Tracker & Feedback Loop (/confirm)

**What it does:** Closes the entire loop — when a hospital coordinator confirms a transfusion happened, the system updates all records, awards badges, updates the leaderboard, and collects data for model retraining. No /confirm = no closed loop.

**Trigger:** Hospital coordinator types `/confirm P-10234 done` in Telegram

**Data Flow:**
```
Step 1: AUTHORIZATION CHECK
  - Verify telegram_chat_id is in staff_whitelist table (Supabase)
  - If unauthorized: "Only hospital coordinators can confirm outcomes."
  - If authorized: proceed

Step 2: PATIENT UPDATE (Supabase)
  - UPDATE patients SET last_transfusion_date=NOW(),
                        days_since_last_transfusion=0,
                        total_transfusions=total_transfusions+1
    WHERE patient_id='P-10234'

Step 3: NEO4J CHAIN COMPLETION
  - MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient {patient_id: 'P-10234'})
    WHERE r.status = 'CONFIRMED'
    SET r.status = 'COMPLETED', r.completed_at = datetime()
  - MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient {patient_id: 'P-10234'})
    WHERE r.status IN ['PENDING','ALERTED']
    SET r.status = 'RELEASED'  (free up these donors for other patients)

Step 4: DONOR UPDATES (for all confirmed donors in chain)
  - UPDATE donors SET lives_saved=lives_saved+1,
                      donation_count=donation_count+1,
                      last_donation_date=NOW(),
                      days_since_donation=0
    WHERE donor_id IN $confirmed_donor_ids
  - Reset churn_score = 0.1 (they just donated — far from churn)

Step 5: GAMIFICATION TRIGGERS (for each confirmed donor)
  - Badge check: run all badge rules against updated donation_count
  - If new badge: append to donors.badges[], send Telegram notification
  - UPDATE gamification SET donation_count=$n, lives_saved=$n, rank=RANK()...
  - Leaderboard recalculates (Supabase query, not real-time)

Step 6: MODEL DATA COLLECTION
  - INSERT INTO training_data (donor_id, patient_id, antigen_score,
                                response_time_hours, chain_position, outcome)
    VALUES (...)
  - This data feeds XGBoost retraining in next monthly batch

Step 7: FEEDBACK MESSAGES
  - To hospital coordinator: "✅ Outcome recorded for P-10234. Chain closed. Thank you!"
  - To each confirmed donor (Telegram):
      "Shukriya {name}! Patient {P-10234} received their transfusion successfully.
       You saved another life. 🩸 Type /impact to hear their story."
  - If badge awarded: badge notification appended to message

Step 8: DASHBOARD UPDATE (WebSocket push)
  - Emergency card: status → COMPLETED (green)
  - Neo4j graph: all nodes turn teal (COMPLETED)
  - Gamification panel: leaderboard ranks update

Output: Complete audit trail, model training data collected, donor motivated to donate again
```

---

## PART 5 — FULL-STACK WEB APP: FRONTEND DASHBOARDS

### 5.1 Dashboard Architecture Decision: Next.js

**Why Next.js over plain React:**

| Feature | React (CRA/Vite) | Next.js 14 (App Router) |
|---|---|---|
| Routing | Manual (React Router) | Built-in file-based routing |
| API routes | Need separate Express | Built-in /app/api/* routes |
| SSR for dashboard initial load | No | Yes — faster perceived load |
| WebSocket integration | Manual | Works with any WS library |
| Vercel deployment | Works | Native, zero config |
| TypeScript support | Manual setup | Built-in |
| Image optimization | Manual | next/image built-in |

Next.js API routes are used ONLY for lightweight proxying (frontend → FastAPI). All business logic stays in FastAPI. No Node.js server needed.

### 5.2 Five Dashboard UIs

---

#### Dashboard 1 — Emergency Operations Center (EOC)

**URL:** `/dashboard/emergency`
**User:** Hospital staff, Blood Warriors coordinators
**Purpose:** Real-time monitoring and control of all active blood emergencies

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚨 EMERGENCY OPERATIONS CENTER          [+New Emergency]    │
│                                                             │
│ ACTIVE EMERGENCIES (3)                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔴 CRITICAL  P-10234  B+   Urgency: 8.7/10             │ │
│ │ KIMS Secunderabad • 2 hrs ago                           │ │
│ │ Chain: D1✅ D2⏳ D3⏳ D4❌ D5⏳ D6⏳ D7⏳ D8⏳          │ │
│ │ [View Chain] [Override Alert] [Escalate]                │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🟠 HIGH      P-10891  A-   Urgency: 6.2/10             │ │
│ │ Apollo Banjara Hills • 45 min ago                       │ │
│ │ Chain: D1✅ D2✅ D3⏳ D4⏳ D5⏳                         │ │
│ │ [View Chain] [Override Alert] [Escalate]                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ RECENT COMPLETIONS (Today: 4)                               │
│ ✅ P-10120  O+  Completed 2:14 PM • Donated: Rajesh K      │
└─────────────────────────────────────────────────────────────┘
```

**Real-time Features (WebSocket):**
- 5-second polling via Socket.io → FastAPI WebSocket `/ws/emergency`
- Chain node status changes update instantly (no page refresh)
- New emergency card appears without reload
- Chain break banner: red pulsing "CHAIN BREAK — Human needed" with sound

**Data Sources:**
- Supabase: `emergencies` table (urgency, status, patient data)
- Supabase: `chains` table (chain positions and statuses)
- FastAPI: `GET /api/emergencies/active` → sorted by urgency DESC
- WebSocket: `ws://api/ws/emergency` → real-time updates

**Actions:**
- **[+New Emergency]** → Modal: Enter patient_id, blood_type, city, ward → POST /api/v1/emergency → LangGraph starts
- **[Override Alert]** → Skip 7-min wait → manually trigger next donor alert
- **[Escalate]** → Mark ESCALATED → ntfy.sh push to senior staff

---

#### Dashboard 2 — Blood Bridge Graph Visualization

**URL:** `/dashboard/graph`
**User:** Hospital staff, Blood Warriors coordinators
**Purpose:** Live visual of every Blood Bridge chain — see exactly which donor is confirming, declining, or pending

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🕸️ BLOOD BRIDGE CHAIN — P-10234               [Filter]     │
│                                                             │
│  Patient    Donor 1   Donor 2   Donor 3  ...               │
│  [♦ P234]──[● D-1023]──[● D-1024]──[● D-1025]──           │
│  CRITICAL    ✅GREEN    ⏳ORANGE    ❌RED                    │
│                                                             │
│  [■ KIMS Hospital]                                          │
│                                                             │
│  LEGEND:                                                    │
│  ● Donor (green=confirmed, orange=alerted, red=declined)   │
│  ♦ Patient   ■ Hospital   ━ edge thickness = antigen_score │
│                                                             │
│  [Selected: D-1023 — Rahul Kumar]                          │
│  Blood Type: B+  |  Antigen Score: 0.87  |  Dist: 4.2km   │
│  Churn Score: 0.12 (LOW)  |  Donations: 13                 │
│  Last Donation: 68 days ago  |  Badges: Life Saver         │
└─────────────────────────────────────────────────────────────┘
```

**Technical Implementation:**
```jsx
import ForceGraph2D from 'react-force-graph-2d';

// Graph data from FastAPI: GET /api/chain/{patient_id}
// Returns: {nodes: [...], links: [...]}

// Node colors
const nodeColor = (node) => {
  if (node.type === 'patient') return '#EF4444';  // red
  if (node.type === 'hospital') return '#6B7280'; // gray
  const statusColors = {
    CONFIRMED: '#22C55E',    // green
    ALERTED: '#F97316',      // orange
    DECLINED: '#EF4444',     // red
    COMPLETED: '#14B8A6',    // teal
    PENDING: '#9CA3AF',      // light gray
  };
  return statusColors[node.status] || '#9CA3AF';
};

// Edge width = antigen_score
const linkWidth = (link) => link.antigen_score * 6;

// Pulsing edge when voice call active
const linkColor = (link) => link.voice_active ? '#FBBF24' : '#E5E7EB';
```

**Real-time Updates:**
- Socket.io event `chain_update` → graph re-renders (nodes change color)
- Event `voice_call_active` → edge pulses yellow
- Click node → side panel slides in with full donor profile
- Filter by patient → show only that patient's chain

---

#### Dashboard 3 — Blood Availability Map

**URL:** `/dashboard/map`
**User:** Hospital staff, Blood Warriors coordinators
**Purpose:** Real-time blood bank inventory across Hyderabad — overlaid on map with drive time estimates

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🗺️ BLOOD AVAILABILITY — Hyderabad        [Filter: B+] [▼]  │
│                                                             │
│  [MAP: Hyderabad centered on KIMS hospital]                 │
│  📍 Green pins: >5 units available                          │
│  📍 Yellow pins: 1–5 units available                        │
│  📍 Red pins: 0 units                                       │
│                                                             │
│  [Selected: Nizam's Institute Blood Bank]                   │
│  B+: 8 units  O+: 3 units  AB-: 0 units                    │
│  📞 040-23489000  |  2.3km  |  ~8 min drive                │
│                                                             │
│  BLOOD STOCK TABLE:                                         │
│  Blood Bank              B+  O+  A+  AB- Distance           │
│  Nizam's Institute       8   3   12  0   2.3km             │
│  KIMS Blood Bank         2   8   5   1   0.8km             │
└─────────────────────────────────────────────────────────────┘
```

**Technical:**
- Leaflet.js + react-leaflet for map
- Pins pulled from `GET /api/blood-stock?city=Hyderabad&type=B+`
- Pin click → popup with units by blood type + contact + drive time (Google Maps API optional, fallback: distance only)
- Auto-refreshes every 15 minutes (matches APScheduler inventory fetch)
- Filter dropdown: blood type + radius slider

---

#### Dashboard 4 — Donor Engagement & Churn Panel

**URL:** `/dashboard/donors`
**User:** Blood Warriors outreach team
**Purpose:** Monitor donor health, identify at-risk donors, trigger AI outreach manually

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ 👥 DONOR ENGAGEMENT CENTER                 [Run AI Outreach]│
│                                                             │
│ AT-RISK DONORS (churn_score > 0.50) — Sorted by Risk       │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Name        Last Don  Score   Risk      Actions          ││
│ │ Ramesh P.   92 days   0.81    CRITICAL  [AI Call][TG]   ││
│ │ Sita K.     78 days   0.67    HIGH      [AI Call][TG]   ││
│ │ Arjun M.    65 days   0.53    HIGH      [AI Call][TG]   ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ LEADERBOARD — This Month (Hyderabad)                        │
│  🥇 Rahul K.     13 donations  ❤️❤️❤️                      │
│  🥈 Priya M.     11 donations  ❤️❤️                        │
│  🥉 Suresh T.    9 donations   ❤️                          │
│                                                             │
│ ENGAGEMENT METRICS                                          │
│ Active Donors: 312/500 (62%) ↑ from 40% last month        │
│ Avg Response Rate: 71%  |  Churn Rate (30d): 8%            │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Churn score color bar (red > 0.75, orange 0.50–0.75, yellow 0.25–0.50, green < 0.25)
- **[AI Call]** → POST /api/v1/voice-call/{donor_id} → triggers voice_agent_node immediately
- **[TG]** → POST /api/v1/outreach/{donor_id} → triggers outreach_agent_node (Gemini message)
- **[Run AI Outreach]** → triggers manual churn batch for selected donors
- Recharts line chart: donor active rate over time (last 6 months)
- Recharts bar chart: donations by city this month

**Data Source:**
- `GET /api/donors?sort=churn_score&order=desc&limit=30`
- `GET /api/leaderboard?city=Hyderabad&period=month`
- `GET /api/analytics/engagement` → time-series metrics

---

#### Dashboard 5 — Admin & System Config

**URL:** `/dashboard/admin`
**User:** Blood Warriors admin team
**Purpose:** System health monitoring, staff whitelist management, agent config, model metrics

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ ADMIN — BloodBridge AI System                            │
│                                                             │
│ SYSTEM HEALTH                                               │
│  FastAPI (Render.com)    ● ONLINE   Resp: 142ms            │
│  Neo4j Aura Free         ● ONLINE   Nodes: 5,234           │
│  Supabase PostgreSQL     ● ONLINE   Size: 48MB / 500MB     │
│  Telegram Bot            ● ACTIVE   Messages today: 247    │
│  Groq API                ● ONLINE   Requests today: 1,204  │
│  Gemini API              ● ONLINE   Tokens today: 42,300   │
│                                                             │
│ STAFF WHITELIST (can send /confirm)                         │
│  [+Add Staff]  Telegram ID: @drpriya  Hospital: KIMS       │
│                                                             │
│ MODEL METRICS                                               │
│  Churn Model: Last trained 2 days ago  Accuracy: 0.87      │
│  Urgency Model: Last trained 2 days ago  Accuracy: 0.91    │
│  [Retrain Models]  [Download Training Data]                 │
│                                                             │
│ AGENT CONFIGURATION                                         │
│  Chain monitor interval: [5] min                           │
│  Voice call timeout: [7] min                               │
│  Max chain length: [8] donors                              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Health check: `GET /api/health` → pings all services, returns latency
- Model retraining: POST /api/admin/retrain → triggers generate_and_train.py
- Staff whitelist CRUD: Supabase `staff_whitelist` table
- Config update: POST /api/admin/config → updates APScheduler intervals live
- LangGraph agent trace viewer: last 10 emergency traces with node-by-node log

---

## PART 6 — BACKEND ARCHITECTURE

### 6.1 FastAPI Project Structure

```
bloodbridge-api/
├── main.py                    # FastAPI app, lifespan (APScheduler + Telegram init)
├── render.yaml                # Render.com deployment config
├── requirements.txt
├── .env                       # Local only (never commit)
│
├── agents/                    # LangGraph agent nodes
│   ├── graph.py               # StateGraph definition — all nodes + edges
│   ├── state.py               # AgentState TypedDict
│   ├── intake_node.py
│   ├── eligibility_node.py
│   ├── antigen_scoring_node.py
│   ├── urgency_scoring_node.py
│   ├── neo4j_matching_node.py
│   ├── conflict_resolver_node.py
│   ├── planner_node.py
│   ├── outreach_node.py
│   ├── chain_monitor_node.py
│   ├── chain_repair_node.py
│   ├── voice_agent_node.py
│   ├── churn_agent_node.py
│   ├── outreach_llm_node.py
│   ├── gamification_node.py
│   ├── inventory_agent_node.py
│   ├── outcome_node.py
│   └── escalate_node.py
│
├── handlers/                  # FastAPI route handlers
│   ├── telegram_handler.py    # All Telegram commands
│   ├── emergency_handler.py   # POST /api/v1/emergency
│   ├── voice_handler.py       # POST /webhook/voice-response
│   ├── dashboard_handler.py   # All dashboard REST endpoints
│   ├── admin_handler.py       # Admin config + health
│   └── websocket_handler.py   # WebSocket /ws/emergency
│
├── db/
│   ├── supabase_client.py     # Supabase connection + queries
│   └── neo4j_client.py        # Neo4j driver + Cypher queries
│
├── models/
│   ├── churn_model.joblib     # Shipped in repo
│   ├── urgency_model.joblib
│   └── train.py               # generate_and_train.py
│
├── services/
│   ├── compatibility.py       # 8-antigen scorer
│   ├── langdetect_service.py  # Language detection
│   ├── keyword_nlu.py         # Voice intent classification
│   ├── tts_service.py         # gTTS → Supabase Storage
│   ├── eraktkosh_service.py   # Blood bank scraper + cache
│   └── gamification_service.py # Badge logic + leaderboard
│
├── scripts/
│   ├── generate_data.py       # Synthetic 500 donors + 50 patients
│   ├── seed_supabase.py       # JSON → Supabase
│   └── seed_neo4j.py          # JSON → Neo4j nodes + edges
│
└── tests/
    ├── test_compatibility.py
    ├── test_keyword_nlu.py
    └── test_churn_model.py
```

### 6.2 FastAPI Endpoints (Complete List)

```
WEBHOOK ENDPOINTS:
  POST /webhook/telegram           → Telegram bot updates
  POST /webhook/voice-response     → Twilio STT response
  GET  /webhook/health             → Uptime robot ping

EMERGENCY ENDPOINTS:
  POST /api/v1/emergency           → Start emergency LangGraph flow
  GET  /api/emergencies/active     → All active emergencies (dashboard)
  GET  /api/chain/{patient_id}     → Chain status (graph data)
  POST /api/chain/override/{id}    → Manual override: trigger next donor

DONOR ENDPOINTS:
  GET  /api/donors                 → Paginated donor list (admin)
  GET  /api/donors/{id}            → Single donor profile
  POST /api/donors/{id}/call       → Manual trigger voice call
  POST /api/donors/{id}/outreach   → Manual trigger AI outreach

ANALYTICS ENDPOINTS:
  GET  /api/leaderboard            → Top donors by city + period
  GET  /api/analytics/engagement   → Active rate, response rate, churn rate
  GET  /api/blood-stock            → Blood bank inventory

ADMIN ENDPOINTS:
  GET  /api/health                 → All service health checks
  POST /api/admin/retrain          → Trigger model retraining
  GET  /api/admin/config           → Current agent config
  POST /api/admin/config           → Update agent config
  GET  /api/admin/staff            → Staff whitelist
  POST /api/admin/staff            → Add staff coordinator

DEBUG ENDPOINTS (demo only, remove in production):
  POST /debug/trigger-voice-call   → Skip 7-min wait for demo
  POST /debug/trigger-emergency    → Inject test emergency
  POST /debug/seed-neo4j           → Reseed graph data

WEBSOCKET:
  WS   /ws/emergency               → Real-time dashboard updates
```

### 6.3 WebSocket Real-Time Events

```python
# FastAPI WebSocket in websocket_handler.py
from fastapi import WebSocket
import asyncio, json

active_connections: list[WebSocket] = []

async def broadcast(event: str, data: dict):
    message = json.dumps({"event": event, "data": data})
    for ws in active_connections:
        await ws.send_text(message)

# Events emitted:
EVENTS = {
    "chain_update":         "Node status changed (ALERTED/CONFIRMED/DECLINED)",
    "new_emergency":        "New emergency request received",
    "voice_call_active":    "Voice call initiated to a donor",
    "blood_stock_update":   "e-RaktKosh inventory refreshed",
    "churn_batch_complete": "Nightly churn batch finished",
    "chain_break":          "Chain break detected — human alert",
    "emergency_completed":  "All donors confirmed — success",
    "badge_awarded":        "Donor earned a new badge",
}
```

---

## PART 7 — DATABASE ARCHITECTURE

### 7.1 Supabase (PostgreSQL) — Complete Schema

```sql
-- ============================================================
-- DONORS TABLE
-- ============================================================
CREATE TABLE donors (
    donor_id            TEXT PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    phone               TEXT UNIQUE NOT NULL,
    telegram_chat_id    TEXT UNIQUE,

    -- Blood phenotype
    blood_type          TEXT NOT NULL,  -- 'B+', 'O-', etc.
    kell_negative       BOOLEAN DEFAULT FALSE,
    duffy_negative      BOOLEAN DEFAULT FALSE,
    kidd_positive       BOOLEAN DEFAULT FALSE,
    rh_e_positive       BOOLEAN DEFAULT TRUE,
    rh_c_positive       BOOLEAN DEFAULT TRUE,
    mns_positive        BOOLEAN DEFAULT FALSE,

    -- Location
    city                TEXT,
    ward                TEXT,
    lat                 FLOAT,
    lng                 FLOAT,

    -- Eligibility
    is_eligible         BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN DEFAULT TRUE,
    medical_hold        BOOLEAN DEFAULT FALSE,
    last_donation_date  DATE,
    days_since_donation INTEGER DEFAULT 999,

    -- Engagement metrics
    donation_count      INTEGER DEFAULT 0,
    lives_saved         INTEGER DEFAULT 0,
    response_rate       FLOAT DEFAULT 0.5,
    avg_response_time_hours FLOAT DEFAULT 24.0,
    missed_alerts_last_90d INTEGER DEFAULT 0,
    gamification_events_30d INTEGER DEFAULT 0,

    -- Personalization
    preferred_language  TEXT DEFAULT 'English',
    tone_profile        TEXT DEFAULT 'motivational',
    preferred_contact_time TEXT DEFAULT '18-20',

    -- Gamification
    badges              JSONB DEFAULT '[]',
    completed_challenges JSONB DEFAULT '[]',

    -- Churn model outputs
    churn_score         FLOAT DEFAULT 0.0,
    churn_risk          TEXT DEFAULT 'LOW',

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_donors_blood_city    ON donors(blood_type, city);
CREATE INDEX idx_donors_city_eligible ON donors(city, is_eligible);
CREATE INDEX idx_donors_churn         ON donors(churn_score DESC);
CREATE INDEX idx_donors_telegram      ON donors(telegram_chat_id);

-- ============================================================
-- PATIENTS TABLE
-- ============================================================
CREATE TABLE patients (
    patient_id              TEXT PRIMARY KEY DEFAULT gen_random_uuid(),
    blood_type              TEXT NOT NULL,
    hemoglobin              FLOAT,
    days_since_last_transfusion INTEGER DEFAULT 0,
    max_safe_interval_days  INTEGER DEFAULT 21,
    total_transfusions      INTEGER DEFAULT 0,

    -- Antigen requirements
    needs_kell_negative     BOOLEAN DEFAULT FALSE,
    needs_duffy_negative    BOOLEAN DEFAULT FALSE,
    antibody_flags          JSONB DEFAULT '[]',  -- ['anti-Kell', 'anti-E', ...]

    -- Clinical flags
    cardiac_flag            BOOLEAN DEFAULT FALSE,
    splenomegaly_flag       BOOLEAN DEFAULT FALSE,

    -- Urgency (updated by XGBoost urgency model)
    urgency_score           FLOAT DEFAULT 0.0,
    priority                TEXT DEFAULT 'ROUTINE',

    -- Location
    hospital                TEXT,
    city                    TEXT,
    hospital_lat            FLOAT,
    hospital_lng            FLOAT,

    last_transfusion_date   DATE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_patients_city_urgency ON patients(city, urgency_score DESC);

-- ============================================================
-- CHAINS TABLE (mirrors Neo4j for SQL queries)
-- ============================================================
CREATE TABLE chains (
    chain_id        TEXT PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      TEXT REFERENCES patients(patient_id),
    donor_id        TEXT REFERENCES donors(donor_id),
    chain_position  INTEGER NOT NULL,
    status          TEXT DEFAULT 'PENDING',
    -- PENDING → ALERTED → CONFIRMED / DECLINED / UNREACHABLE / COMPLETED / RELEASED
    antigen_score   FLOAT,
    alerted_at      TIMESTAMPTZ,
    confirmed_at    TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    voice_call_sid  TEXT,
    UNIQUE(patient_id, donor_id)
);

CREATE INDEX idx_chains_patient    ON chains(patient_id);
CREATE INDEX idx_chains_status     ON chains(status);
CREATE INDEX idx_chains_alerted_at ON chains(alerted_at);

-- ============================================================
-- EMERGENCIES TABLE (full audit trail)
-- ============================================================
CREATE TABLE emergencies (
    request_id      TEXT PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      TEXT REFERENCES patients(patient_id),
    blood_type      TEXT,
    city            TEXT,
    priority        TEXT,
    urgency_score   FLOAT,
    status          TEXT DEFAULT 'IN_PROGRESS',
    -- IN_PROGRESS → SUCCESS / ESCALATED / CANCELLED
    agent_log       JSONB DEFAULT '[]',  -- Every LangGraph node execution logged here
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ============================================================
-- DONOR_MEMORY TABLE (conversational memory per phone)
-- ============================================================
CREATE TABLE donor_memory (
    phone               TEXT PRIMARY KEY,
    preferred_language  TEXT DEFAULT 'English',
    tone_profile        TEXT DEFAULT 'motivational',
    last_context        TEXT,
    emotional_anchors   JSONB DEFAULT '[]',
    last_interaction    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- GAMIFICATION TABLE
-- ============================================================
CREATE TABLE gamification (
    donor_id         TEXT PRIMARY KEY REFERENCES donors(donor_id),
    badges           JSONB DEFAULT '[]',
    donation_count   INTEGER DEFAULT 0,
    lives_saved      INTEGER DEFAULT 0,
    city_rank        INTEGER,
    current_challenge TEXT,
    challenge_started TIMESTAMPTZ
);

-- ============================================================
-- BLOOD_STOCK TABLE (e-RaktKosh cache)
-- ============================================================
CREATE TABLE blood_stock (
    pk          TEXT PRIMARY KEY,  -- Format: 'B+#Hyderabad'
    blood_banks JSONB DEFAULT '[]',
    expires_at  TIMESTAMPTZ
);

-- ============================================================
-- STAFF_WHITELIST TABLE
-- ============================================================
CREATE TABLE staff_whitelist (
    telegram_chat_id TEXT PRIMARY KEY,
    name             TEXT,
    hospital         TEXT,
    role             TEXT DEFAULT 'coordinator',
    added_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRAINING_DATA TABLE (for model retraining)
-- ============================================================
CREATE TABLE training_data (
    id              BIGSERIAL PRIMARY KEY,
    donor_id        TEXT,
    patient_id      TEXT,
    antigen_score   FLOAT,
    response_time_hours FLOAT,
    chain_position  INTEGER,
    outcome         TEXT,  -- 'CONFIRMED' / 'DECLINED' / 'UNREACHABLE'
    recorded_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security (DPDP Act compliance)
ALTER TABLE donors ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE donor_memory ENABLE ROW LEVEL SECURITY;

-- Donors can only read their own records (via Supabase auth)
CREATE POLICY "donor_self_read" ON donors
    FOR SELECT USING (auth.uid()::text = telegram_chat_id);
```

---

### 7.2 Neo4j Aura Free — Graph Schema

**Why Neo4j alongside Supabase:**

Supabase (PostgreSQL) handles structured data, SQL queries, and auth. Neo4j handles graph-specific operations that are impossible or extremely slow in SQL:
- Find broken chain links by graph distance
- Compute shortest compatible donor path
- Traverse Blood Bridge chains by position
- Store antigen compatibility as weighted edges (avoids N×M join table)
- Geo-distance ranking within Cypher (native spatial index)

**Node Types (4):**

```cypher
-- DONOR node
(:Donor {
    donor_id:           STRING,   -- matches Supabase donors.donor_id
    name:               STRING,
    phone:              STRING,
    blood_type:         STRING,
    kell_negative:      BOOLEAN,
    duffy_negative:     BOOLEAN,
    kidd_positive:      BOOLEAN,
    city:               STRING,
    ward:               STRING,
    lat:                FLOAT,
    lng:                FLOAT,
    is_eligible:        BOOLEAN,
    days_since_donation: INTEGER,
    churn_score:        FLOAT
})

-- PATIENT node
(:Patient {
    patient_id:         STRING,
    blood_type:         STRING,
    needs_kell_negative: BOOLEAN,
    needs_duffy_negative: BOOLEAN,
    antibody_flags:     LIST<STRING>,
    urgency_score:      FLOAT,
    priority:           STRING,
    hospital:           STRING,
    city:               STRING,
    hospital_lat:       FLOAT,
    hospital_lng:       FLOAT
})

-- HOSPITAL node
(:Hospital {
    hospital_id:        STRING,
    name:               STRING,
    city:               STRING,
    lat:                FLOAT,
    lng:                FLOAT,
    contact:            STRING
})

-- BLOOD BANK node
(:BloodBank {
    bb_id:              STRING,
    name:               STRING,
    city:               STRING,
    lat:                FLOAT,
    lng:                FLOAT,
    contact:            STRING,
    units_o_neg:        INTEGER,
    units_o_pos:        INTEGER,
    units_a_neg:        INTEGER,
    units_a_pos:        INTEGER,
    units_b_neg:        INTEGER,
    units_b_pos:        INTEGER,
    units_ab_neg:       INTEGER,
    units_ab_pos:       INTEGER,
    updated_at:         DATETIME
})
```

**Relationship Types (4):**

```cypher
-- Blood Bridge chain position
(d:Donor)-[:IN_CHAIN {
    chain_position:     INTEGER,  -- 1–8 ordering
    status:             STRING,   -- PENDING/ALERTED/CONFIRMED/DECLINED/COMPLETED
    antigen_score:      FLOAT,
    alerted_at:         DATETIME,
    confirmed_at:       DATETIME,
    voice_call_initiated: BOOLEAN
}]->(p:Patient)

-- Pre-computed compatibility (stored at onboarding/batch)
(d:Donor)-[:COMPATIBLE_WITH {
    antigen_score:      FLOAT,    -- 0.60–1.0 (only above threshold stored)
    kell_safe:          BOOLEAN,
    duffy_safe:         BOOLEAN,
    kidd_safe:          BOOLEAN,
    rh_e_safe:          BOOLEAN
}]->(p:Patient)

-- Patient-hospital association
(p:Patient)-[:ADMITTED_AT]->(h:Hospital)

-- Hospital-blood bank proximity
(h:Hospital)-[:NEAR_BANK {
    distance_km:        FLOAT
}]->(bb:BloodBank)
```

**Production Cypher Queries (all used in agents):**

```cypher
-- 1. MATCHING: Top 8 compatible eligible donors for patient
MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p:Patient {patient_id: $pid})
WHERE d.is_eligible = true
  AND c.antigen_score >= 0.80
  AND c.kell_safe = $needs_kell_safe
  AND c.duffy_safe = $needs_duffy_safe
WITH d, c,
  point.distance(
    point({latitude: d.lat, longitude: d.lng}),
    point({latitude: $hosp_lat, longitude: $hosp_lng})
  ) AS dist_m
ORDER BY c.antigen_score DESC, dist_m ASC
LIMIT 8
RETURN d.donor_id, d.name, d.phone, d.telegram_chat_id,
       c.antigen_score, dist_m/1000 AS dist_km

-- 2. CHAIN STATUS: /bridge command + dashboard graph
MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient {patient_id: $pid})
RETURN d.name, d.donor_id, r.chain_position, r.status,
       r.alerted_at, r.confirmed_at, r.antigen_score
ORDER BY r.chain_position

-- 3. STALE NODES: ChainMonitor (runs every 5 min)
MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
WHERE r.status = 'ALERTED'
  AND r.alerted_at < datetime() - duration('PT7M')
RETURN p.patient_id, d.donor_id, d.phone, r.chain_position, r.alerted_at
ORDER BY r.chain_position

-- 4. BROKEN NODES: Chain repair
MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
WHERE r.status IN ['DECLINED', 'UNREACHABLE']
RETURN p.patient_id, d.donor_id, r.chain_position
ORDER BY p.patient_id, r.chain_position

-- 5. NEAREST BLOOD BANK: Inventory fallback
MATCH (b:BloodBank)
WHERE b[$blood_type_field] > 0
WITH b, point.distance(
    point({latitude: b.lat, longitude: b.lng}),
    point({latitude: $hosp_lat, longitude: $hosp_lng})
) AS dist_m
ORDER BY dist_m
LIMIT 3
RETURN b.name, b.contact, b[$blood_type_field] AS units, dist_m/1000 AS dist_km

-- 6. UPDATE CHAIN NODE STATUS
MATCH (d:Donor {donor_id: $donor_id})-[r:IN_CHAIN]->(p:Patient {patient_id: $patient_id})
SET r.status = $new_status,
    r.confirmed_at = CASE WHEN $new_status = 'CONFIRMED' THEN datetime() ELSE r.confirmed_at END
RETURN r.status
```

**Neo4j Free Tier Capacity:**
- Free limit: 200,000 nodes, 400,000 relationships
- Estimated usage: 500 donors + 50 patients + 15 hospitals + 15 blood banks + ~4,000 chain/compatibility edges
- Usage: ~580 nodes, ~4,000 relationships = **2% of free limit**

---

### 7.3 In-Memory State (No Redis Needed)

Redis is NOT needed on the free tier. All in-memory needs are handled:

| Need | Solution | Why No Redis |
|---|---|---|
| Active emergency session state | AgentState in LangGraph checkpointer | LangGraph persists state to Supabase via SQLite checkpointer |
| Chain status cache (5-min window) | Python dict in APScheduler job | Single Render.com instance, reset on deploy is OK |
| WebSocket connection registry | Python list in main.py | Single instance, reconnect on restart |
| Groq/Gemini response cache | None (responses are personalized, caching would reduce quality) | Not needed |
| Blood stock cache | Supabase blood_stock table with expires_at | 15-min TTL, Supabase handles it |

If the system scales to multi-instance (Phase 2): add Upstash Redis free tier (10MB, enough for session state).

---

## PART 8 — LANGGRAPH IMPLEMENTATION

### 8.1 StateGraph Definition

```python
# agents/graph.py
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents import (
    intake_node, eligibility_filter_node,
    antigen_scoring_node, urgency_scoring_node,
    neo4j_matching_node, conflict_resolver_node,
    planner_node, outreach_node, chain_monitor_node,
    chain_repair_node, voice_agent_node,
    inventory_agent_node, gamification_node,
    outcome_node, escalate_node
)

def build_emergency_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("intake",           intake_node.run)
    graph.add_node("eligibility",      eligibility_filter_node.run)
    graph.add_node("antigen_scoring",  antigen_scoring_node.run)
    graph.add_node("urgency_scoring",  urgency_scoring_node.run)
    graph.add_node("neo4j_matching",   neo4j_matching_node.run)
    graph.add_node("conflict_resolver",conflict_resolver_node.run)
    graph.add_node("planner",          planner_node.run)
    graph.add_node("outreach",         outreach_node.run)
    graph.add_node("chain_monitor",    chain_monitor_node.run)
    graph.add_node("chain_repair",     chain_repair_node.run)
    graph.add_node("voice_agent",      voice_agent_node.run)
    graph.add_node("inventory_agent",  inventory_agent_node.run)
    graph.add_node("gamification",     gamification_node.run)
    graph.add_node("outcome",          outcome_node.run)
    graph.add_node("escalate",         escalate_node.run)

    # Entry point
    graph.set_entry_point("intake")

    # Linear flow: intake → eligibility → parallel scoring → matching
    graph.add_edge("intake", "eligibility")
    graph.add_edge("eligibility", "antigen_scoring")
    graph.add_edge("antigen_scoring", "urgency_scoring")
    graph.add_edge("urgency_scoring", "neo4j_matching")

    # Conditional: conflict resolver only if needed
    graph.add_conditional_edges("neo4j_matching", route_after_matching, {
        "conflict":      "conflict_resolver",
        "no_conflict":   "planner",
    })
    graph.add_edge("conflict_resolver", "planner")
    graph.add_edge("planner", "outreach")
    graph.add_edge("outreach", "chain_monitor")

    # Chain monitor loop
    graph.add_conditional_edges("chain_monitor", route_after_monitor, {
        "all_confirmed": "outcome",
        "needs_voice":   "voice_agent",
        "needs_repair":  "chain_repair",
        "in_progress":   "chain_monitor",  # continue monitoring
        "escalate":      "inventory_agent",
    })
    graph.add_edge("voice_agent", "chain_monitor")
    graph.add_edge("chain_repair", "chain_monitor")
    graph.add_edge("inventory_agent", "escalate")
    graph.add_edge("outcome", "gamification")
    graph.add_edge("gamification", END)
    graph.add_edge("escalate", END)

    return graph.compile()

def route_after_matching(state: AgentState) -> str:
    if state.get("conflict_detected"):
        return "conflict"
    return "no_conflict"

def route_after_monitor(state: AgentState) -> str:
    confirmed = len(state.get("confirmed_donors", []))
    if confirmed >= 1:  # At least 1 donor confirmed → success
        return "all_confirmed"
    if state.get("retry_count", 0) >= 3:
        return "escalate"
    if state.get("stale_nodes"):
        return "needs_voice"
    if state.get("broken_nodes"):
        return "needs_repair"
    return "in_progress"

# Build once at startup, reuse for all requests
EMERGENCY_GRAPH = build_emergency_graph()
```

---

## PART 9 — TELEGRAM COMMANDS (Complete)

| Command | Who Uses It | What It Does |
|---|---|---|
| `/start` | New donors | Onboarding flow — register name, phone, blood type |
| `/emergency [type] [city] [ward] [patient_id]` | Hospital staff | Start emergency LangGraph flow |
| `/bridge [patient_id]` | Staff | View live chain status in text format |
| `/mystats` | Donors | Personal dashboard: lives saved, badges, rank |
| `/leaderboard` | Donors | Top 10 city donors this month |
| `/challenge` | Donors | Get personalized donation challenge |
| `/impact` | Donors | Receive anonymized patient impact story |
| `/confirm [patient_id] done` | Hospital staff | Close the loop — transfusion completed |
| `/help` | Anyone | List all commands with descriptions |
| Free text | Donors | Groq LLM conversational response in detected language |
| Photo message | Donors | Tesseract OCR → blood group extraction |

---

## PART 10 — 3-DAY SPRINT PLAN

### Day 1 — Foundation + Matching (10 hours)

**Morning (5h) — Data + Backend skeleton:**
- [ ] Run `generate_data.py` → 500 donors, 50 patients JSON
- [ ] Set up FastAPI project structure (all directories)
- [ ] Install all dependencies (`pip install -r requirements.txt`)
- [ ] Create Supabase project → run SQL schema → seed with `seed_supabase.py`
- [ ] Create Neo4j Aura Free instance → run `seed_neo4j.py`
- [ ] Train XGBoost churn + urgency models → save to `models/`
- [ ] Build `compatibility.py` — 8-antigen scorer (+ unit tests)
- [ ] Create Telegram bot via @BotFather → save token

**Afternoon (5h) — LangGraph graph + Telegram:**
- [ ] `agents/state.py` — AgentState TypedDict
- [ ] `agents/graph.py` — StateGraph with all nodes registered
- [ ] Implement: intake_node, eligibility_filter_node, antigen_scoring_node
- [ ] Implement: neo4j_matching_node (Cypher matching query)
- [ ] Telegram handler: `/emergency`, `/help`, free-text routing
- [ ] Deploy to Render.com → set all env vars → set Telegram webhook
- [ ] **End-of-Day test:** `/emergency B+ Hyderabad` → 3 Telegram messages sent ✓

### Day 2 — AI Layer + Voice + All Agents (10 hours)

**Morning (5h) — Voice + Chain:**
- [ ] `urgency_scoring_node.py` — XGBoost urgency model
- [ ] `planner_node.py` — Gemini ReAct decision
- [ ] `outreach_node.py` — parallel Groq messages per donor
- [ ] `chain_monitor_node.py` — APScheduler job (5-min)
- [ ] `chain_repair_node.py` — DECLINED → next donor
- [ ] `voice_agent_node.py` — Gemini script → gTTS → Twilio → NLU
- [ ] `keyword_nlu.py` — 4 intents, Hindi/Telugu/English
- [ ] WebSocket handler — `/ws/emergency` + broadcast helper

**Afternoon (5h) — Gamification + Churn + Memory:**
- [ ] `churn_agent_node.py` — nightly batch, Render.com cron
- [ ] `outreach_llm_node.py` — Gemini personalized outreach
- [ ] `gamification_node.py` — badge logic + `/mystats`, `/leaderboard`, `/challenge`, `/impact`
- [ ] `outcome_node.py` — `/confirm` full flow
- [ ] `langdetect_service.py` — language detection with short-text fallback to donor_memory
- [ ] Tesseract OCR photo handler
- [ ] `inventory_agent_node.py` — e-RaktKosh + Supabase cache
- [ ] **End-of-Day test:** Full emergency → voice call fires → say "haan" → node turns green ✓

### Day 3 — Dashboard + Demo (10 hours)

**Morning (4h) — Next.js Dashboard:**
- [ ] `npx create-next-app bloodbridge-dashboard --typescript --tailwind`
- [ ] Install: shadcn/ui, react-force-graph, react-leaflet, recharts, socket.io-client
- [ ] Dashboard 1: Emergency OC — cards + chain status (Socket.io live updates)
- [ ] Dashboard 2: Neo4j Graph — react-force-graph with color nodes + edge width
- [ ] Deploy to Vercel → connect GitHub → auto-deploy

**Afternoon (4h) — Polish + Demo Prep:**
- [ ] Dashboard 3: Blood Map (Leaflet + mock e-RaktKosh pins)
- [ ] Dashboard 4: Donor Engagement + churn table
- [ ] `/debug/trigger-voice-call` endpoint (skip 7-min wait)
- [ ] UptimeRobot → ping Render.com every 5 min
- [ ] Fix all issues found in end-to-end rehearsal
- [ ] 5× full 90-second demo rehearsal

**Evening (2h) — Demo Prep:**
- [ ] Backup: pre-recorded Hindi voice call audio file (play from laptop if Twilio fails)
- [ ] Screenshot all working features → update slide deck
- [ ] Practice demo script (assign: who types, who holds phone for voice demo)

---

## PART 11 — 90-SECOND DEMO SCRIPT

```
T+0:00  Open Next.js dashboard → Dashboard 1 Emergency OC
         Show: 1 CRITICAL card — P-10234, B+, Urgency 8.7/10

T+0:05  Open Telegram on demo phone
         Type: /emergency B+ Hyderabad Secunderabad P-10234

T+0:10  Dashboard: 3 donor cards update to ALERTED (orange) in real time
         Telegram: 3 personalized messages sent (show Hindi message on screen)

T+0:15  Say: "Our LangGraph chain monitor fires every 5 minutes.
         For the demo, we'll trigger the 7-minute timeout now."

T+0:25  Run: POST /debug/trigger-voice-call?donor_id=D-1000
         OR: curl -X POST https://bloodbridge-api.onrender.com/debug/trigger-voice-call

T+0:35  Demo phone RINGS. Answer on speaker.
         Room hears gTTS Hindi voice:
         "Namaste Rahul bhai, BloodBridge se call kar raha hoon.
          Ek bachche ko aaj B+ blood chahiye KIMS mein.
          Aapne 12 logon ki zindagi bachaayi hai. Haan ya nahi bolein."

T+1:00  Say "haan" clearly into phone.

T+1:05  Dashboard: D-1 node flips orange → GREEN in react-force-graph. Live.
         Telegram: "Shukriya Rahul bhai! Aap ek Blood Hero hain! 🏆"

T+1:10  Type: /mystats
         Reply: "13 lives saved. Badge: Life Saver. Rank #3 Hyderabad this month."

T+1:20  Switch to Dashboard 3 — Blood Map
         "3 units B-negative available at KIMS, 2.3km away. Live from e-RaktKosh."

T+1:35  Switch to Dashboard 2 — Graph
         "This is the Blood Bridge chain — 8 donors, 1 patient, real-time.
          Thicker edges = better antigen compatibility. Green = confirmed."

T+1:45  Final line:
         "LangGraph autonomous agents. 8-antigen matching. AI voice in Hindi.
          Neo4j Blood Bridge chains. Telegram + web dashboard. ₹0 deployment.
          80% staff time saved. This is BloodBridge AI."
```

---

## PART 12 — COMPLIANCE, PRIVACY & SECURITY

| Requirement | Implementation |
|---|---|
| No medical data via Telegram | Only logistics transmitted (time, hospital name, codes). Clinical data stays in Supabase. |
| Supabase encryption | AES-256 at rest, TLS in transit, Row Level Security enabled |
| Neo4j Aura encryption | Encrypted at rest + in transit by default |
| DPDP Act 2023 compliance | Consent at onboarding, data minimization, right to deletion (CASCADE) |
| /confirm authorization | Staff whitelist check (Supabase) before any outcome update |
| LLM audit trail | All Gemini decisions logged to Supabase emergencies.agent_log |
| Donor phone privacy | Phone numbers never sent to other donors in any Telegram message |
| LangGraph human-in-loop | interrupt_before escalate_node — CRITICAL conflict requires coordinator approval |
| API key security | Render.com environment variables (never in code or GitHub) |

---

## PART 13 — JUDGE Q&A PREPARATION

**Q: "Why LangGraph instead of a simple if/else chain?"**
A: "LangGraph gives us typed shared state that persists across all 8 agent nodes — every node reads and writes the same AgentState. It gives us conditional routing (the graph decides next node based on state), built-in retry policy per node, parallel branches (we alert 8 donors simultaneously, not sequentially), and a full trace log of every node execution for debugging and audit. A custom ReAct loop would give us none of these for free."

**Q: "How does your matching work? Is it just blood type?"**
A: "No — we score across 8 antigen systems using clinically validated penalty weights from ISBT. Kell mismatch carries the heaviest penalty (-0.35) because it's the most immunogenic after ABO/Rh. For Thalassemia patients who've had 50+ transfusions, ABO-only matching can trigger Delayed Hemolytic Transfusion Reactions. Our scorer prevents this. These compatibility scores are stored as COMPATIBLE_WITH edges in Neo4j, so the graph query re-ranks by both antigen quality and geographic proximity in a single Cypher query."

**Q: "Why Neo4j? Couldn't Supabase handle everything?"**
A: "Supabase handles structured data perfectly. But Blood Bridge chains are literally a graph — 8 donors connected to a patient by chain relationships with position and status. Detecting broken chain links by graph traversal, finding the nearest phenotype-compatible donor path, and computing geo-distance rankings across the full network — these are graph operations. The Cypher query that finds the top 8 compatible donors sorted by antigen score and proximity runs in under 100ms. The equivalent SQL would require 3+ joins and application-layer sorting across hundreds of records."

**Q: "Where does 67% response rate come from?"**
A: "That's our projected target based on the personalization design — not measured data yet. 15% is the documented response rate for generic broadcast reminders in donor engagement literature. Our system calls donors by name in their own language, mentions their specific impact, and calls at their preferred time. We want to be transparent: we'll validate the actual rate in a pilot with Blood Warriors' 40,000 real donor records."

**Q: "What happens if Groq is down during an emergency?"**
A: "We have a 1.8-second timeout on every Groq call. If it exceeds that, the system falls back to pre-written emergency templates in the donor's last-known language — stored in Supabase. The matching and chain logic are entirely separate from the LLM layer, so an LLM outage doesn't block donor alerts — it just sends a slightly less personalized message."

**Q: "Why Telegram instead of WhatsApp?"**
A: "Telegram's Bot API requires zero approval, zero business verification, and costs nothing — we had it running in 2 minutes via @BotFather. WhatsApp Business API requires Meta approval that can take weeks. The same commands work identically. Our channel layer in FastAPI is abstracted — adding WhatsApp or SMS in production requires only adding a new handler, not touching any agent logic."

---

## PART 14 — COMPLETE FREE TIER STACK

| Function | Service | Free Limit | Why Chosen |
|---|---|---|---|
| Messaging channel | Telegram Bot API | Unlimited, forever | Zero approval, 2-min setup |
| AI Voice Calling | Twilio Voice ($15 trial) | ~600 min | Best free voice API |
| Hindi/regional TTS | gTTS Python library | Unlimited | pip install, no API |
| Voice NLU | Keyword NLU (Python) | Unlimited | Zero dependency, no quota |
| Language detection | langdetect Python | 55 languages offline | pip install, runs in-process |
| Challenge recommendations | scikit-learn SVD | Unlimited | pip install, no API |
| Image OCR | Tesseract + pytesseract | Unlimited | apt-get install, open source |
| Agent orchestration | LangGraph | Unlimited (OSS library) | Production-grade, Python |
| LLM (fast) | Groq Llama-3.3-70B | 14,400 req/day | 200 tok/s, fastest free LLM |
| LLM (reasoning) | Gemini 1.5 Flash | 1M tokens/day | Best free reasoning model |
| Graph DB | Neo4j Aura Free | 200K nodes, permanent | Native graph, no credit card |
| Database | Supabase PostgreSQL | 500MB permanent | Full SQL + realtime + auth |
| Backend compute | Render.com (FastAPI) | 750 hrs/month | Python native, auto-deploy |
| Frontend hosting | Vercel | 100GB bandwidth | Next.js native, CI/CD |
| Staff alerts | ntfy.sh | Unlimited | Zero setup push notifications |
| Keep-alive | UptimeRobot | 50 monitors free | Prevents Render.com sleep |
| **Total cost** | | **₹0** | |

---

*BloodBridge AI — PRD v5.0*
*Definitive · Agentic AI · LangGraph · Full-Stack · Free-Tier-First · Zero-AWS*
*Team Inqilab | DNR College of Engineering and Technology | Blend360 Hackathon*
*Stack: Next.js + FastAPI + LangGraph + Neo4j + Supabase + Telegram + Groq + Gemini + Twilio*
*8 LangGraph agent nodes · 5 dashboard UIs · 10 features with full data flows · ₹0 demo cost*
*All 15 problem requirements addressed · All 8 evaluator gaps closed · Node.js: NOT needed*
---

## PART 15 — DESIGN SYSTEM & COLOR PALETTE

> Judges judge with their eyes first. Every color decision is intentional — Medical Trust (teal) + Urgency (red) + Safety (green). This is a healthcare product, not a startup landing page.

### 15.1 Core Color Palette

| Role | Name | Tailwind Class | Hex | Usage |
|---|---|---|---|---|
| **Primary — Trust** | Medical Teal | `teal-600` | `#0D9488` | Primary buttons, active states, confirmed donor nodes, sidebar active link, headers |
| **Secondary — Structure** | Deep Navy | `slate-800` | `#1E293B` | Sidebar background, primary text, card headers |
| **Alert — Urgency** | Crisis Red | `red-500` | `#EF4444` | CRITICAL badges, declined donor nodes, chain break banners, emergency buttons |
| **Success — Safe** | Vital Green | `emerald-500` | `#10B981` | Confirmed donors, completed transfusions, blood stock >5 units, badge awards |
| **Warning — Pending** | Amber Orange | `amber-500` | `#F59E0B` | Alerted/pending donors, low blood stock 1–5 units, medium churn risk bar |
| **Gamification** | Hero Gold | `yellow-400` | `#FBBF24` | Badge icons, leaderboard crowns, challenge stars, impact story highlights |
| **Background** | Clinical White | `slate-50` | `#F8FAFC` | Dashboard background — reduces eye strain for staff on monitoring screens |
| **Surface** | Card White | `white` | `#FFFFFF` | All card surfaces, modals, panels |
| **Border** | Subtle Gray | `slate-200` | `#E2E8F0` | Card borders, table row dividers, input borders |
| **Muted Text** | Slate Muted | `slate-500` | `#64748B` | Secondary labels, timestamps, subtitles |

### 15.2 Semantic Color Map — Every Component

```
DONOR NODE COLORS (Neo4j Graph + Chain Circles):
  CONFIRMED   → emerald-500  #10B981  solid fill, white ✓
  ALERTED     → amber-500    #F59E0B  solid fill, white !, animate-pulse
  PENDING     → slate-300    #CBD5E1  outline only, no fill
  DECLINED    → red-500      #EF4444  solid fill, white ✗
  COMPLETED   → teal-600     #0D9488  solid fill, white ●
  VOICE_CALL  → yellow-400   #FBBF24  pulsing ring animation

URGENCY BADGE:
  CRITICAL    → red-100 bg, red-700 text, uppercase, font-bold
  HIGH        → amber-100 bg, amber-800 text
  ROUTINE     → slate-100 bg, slate-700 text

BLOOD STOCK MAP PINS:
  >5 units    → emerald-500  (safe)
  1–5 units   → amber-500    (low)
  0 units     → red-500      (critical, greyed overlay)

CHURN SCORE PROGRESS BAR:
  > 0.75      → red-500      CRITICAL — trigger voice call
  0.50–0.74   → amber-500    HIGH     — AI outreach
  0.25–0.49   → yellow-400   MEDIUM   — gamification nudge
  < 0.25      → emerald-500  LOW      — standard cadence

BUTTONS:
  Primary action  → bg-teal-600 hover:bg-teal-700 text-white
  Destructive     → bg-red-500  hover:bg-red-600  text-white
  Outline         → border-slate-300 hover:bg-slate-50 text-slate-700
  Ghost           → hover:bg-slate-100 text-slate-600
```

### 15.3 Typography System

```
Font Stack (import in globals.css):
  @import url('https://fonts.googleapis.com/css2?
    family=Inter:wght@400;500;600;700;800&
    family=JetBrains+Mono:wght@400;500&display=swap');

  Display/Dashboard heading → Inter 700–800, slate-800
  Body text                 → Inter 400, slate-600
  Monospace (IDs, scores)   → JetBrains Mono 400–500, slate-700
  Telegram bot text         → Plain UTF-8 only. Bold via *asterisks*.

Tailwind Scale:
  text-2xl font-bold    → Dashboard page heading (24px)
  text-lg  font-semibold → Card title (18px)
  text-sm  font-normal  → Body text (14px)
  text-xs  font-normal  → Caption / timestamp (12px)
  text-xs  font-bold uppercase tracking-wider → Urgency badge
  font-mono text-sm     → Patient ID / donor ID / scores
```

### 15.4 Telegram Bot UX Rules

```
TONE & HONORIFICS:
  Hindi:   "Rahul bhai", "Shukriya", "*B+* blood chahiye"
  Telugu:  "Rahul garu", "Dhanyavaadalu"
  Tamil:   "Rahul anna", "Nandri"
  English: "Dear Rahul", "Thank you"

EMOJI STANDARDS:
  🩸  Blood / donation event
  🚨  Emergency alert
  🏆  Badge awarded / leaderboard
  📞  Voice call incoming
  ✅  Confirmed / success
  ❌  Declined
  ⏱️  Time elapsed
  🎯  Challenge unlocked
  💉  Transfusion confirmed
  🌟  Leaderboard rank

INLINE KEYBOARD BUTTONS (always use — never make donor type yes/no):
  Emergency alert:
    [✅ Haan, karunga]   [❌ Aaj nahi]   [📞 Mujhe call karo]
  Post-voice follow-up:
    [✅ Confirm donation]   [📅 Reschedule]
  Onboarding:
    [📸 Send blood card photo]   [⌨️ Type my blood type]

MESSAGE LENGTH LIMITS:
  Emergency alert     → max 150 chars (no scroll on small phones)
  Badge notification  → max 200 chars
  Impact story        → max 300 chars (3 sentences)
  Conversational      → max 150 chars (enforced in Groq system prompt)
```

---

## PART 16 — DETAILED FRONTEND UI/UX SPECIFICATIONS

### 16.1 Global App Shell

**Files:** `app/layout.tsx` · `app/dashboard/layout.tsx`

```
SIDEBAR (Fixed left, w-60, bg-slate-800, h-screen):
┌──────────────────────────┐
│  🩸 BloodBridge AI       │  ← teal-400 drop icon + Inter 700 white text
│  ────────────────────    │  ← border-slate-700 divider
│  🚨 Emergencies          │  ← Active: bg-teal-600 rounded-lg text-white
│  🕸️  Blood Bridge         │  ← Inactive: text-slate-400 hover:bg-slate-700
│  🗺️  Blood Map            │    hover:text-white transition-all 200ms
│  👥 Donors               │
│  ⚙️  Admin                │
│                          │
│  ────────────────────    │
│  ● All systems online    │  ← emerald-400 dot + text-xs text-slate-400
│  Dr. Priya · KIMS        │  ← Avatar initials circle + name + logout
└──────────────────────────┘

TOP BAR (h-14, bg-white, border-b border-slate-200, px-6):
  Left:  Breadcrumb → "Dashboard / Emergencies" (text-sm text-slate-500)
  Center: Search bar (Cmd+K shortcut) → searches donors + patients
  Right: 🔔 notification bell (badge count) · Staff avatar

MAIN CONTENT (bg-slate-50, p-6, flex-1, overflow-y-auto):
  Max width: max-w-7xl mx-auto
  Card style: bg-white rounded-xl shadow-sm border border-slate-200 p-6
  Grid gaps: gap-6 (24px)
  Responsive breakpoints: grid-cols-1 sm:grid-cols-2 xl:grid-cols-4

GLOBAL SHADCN/UI COMPONENTS USED:
  Card, CardHeader, CardContent, CardFooter  → all info panels
  Badge                                       → urgency, status pills
  Button (variant: default/destructive/outline/ghost)
  Sheet                                       → slide-out donor profile
  Dialog                                      → confirm modals, new emergency
  Table + DataTable                           → donor lists, blood stock
  Progress                                    → churn score bar
  Skeleton                                    → loading state during WS connect
  Sonner (toast)                              → real-time event notifications
  Tooltip                                     → hover info on graph nodes
  Accordion                                   → collapsible LangGraph traces
  Select                                      → filter dropdowns
```

---

### 16.2 Dashboard 1 — Emergency Operations Center

**File:** `app/dashboard/emergency/page.tsx`

```
PAGE HEADER ROW (flex justify-between items-center mb-6):
  Left:  "Emergency Operations Center"  text-2xl font-bold text-slate-800
  Right: [+ New Emergency]  bg-teal-600 text-white px-4 py-2 rounded-lg

SUMMARY METRIC STRIP (grid grid-cols-4 gap-4 mb-6):
  Card 1 — Active Emergencies
    Number: text-3xl font-bold text-red-500
    Label:  "Active Emergencies" text-sm text-slate-500
    Icon:   🚨 top-right, opacity-20, text-4xl

  Card 2 — Donors Alerted Today
    Number: text-3xl font-bold text-amber-500
    Label:  "Donors Alerted Today"

  Card 3 — Confirmed Today
    Number: text-3xl font-bold text-emerald-500
    Label:  "Confirmed Today"

  Card 4 — Avg Response Time
    Number: text-3xl font-bold text-teal-600
    Label:  "Avg Response Time"

EMERGENCY CARDS (grid grid-cols-1 xl:grid-cols-2 gap-4):
┌─────────────────────────────────────────────────────────┐
│ CardHeader (flex justify-between):                       │
│   Left:  <Badge variant="destructive">CRITICAL</Badge>  │
│           + "P-10234" font-mono font-semibold           │
│   Right: ⏱️ "14 min ago" text-xs text-slate-500         │
├─────────────────────────────────────────────────────────┤
│ CardContent:                                             │
│   Blood type: "B+" text-4xl font-black text-teal-600   │
│   Hospital:   "KIMS Secunderabad" text-sm text-slate-600│
│   Urgency bar: Progress value={87} className="h-1.5"   │
│   Label: "Urgency: 8.7 / 10" text-xs text-slate-400    │
│                                                          │
│   CHAIN ROW (flex gap-2 items-center mt-4):             │
│   ●  ●  ●  ✗  ●  ○  ○  ○                               │
│   D1 D2 D3 D4 D5 D6 D7 D8                              │
│                                                          │
│   Status summary text-xs text-slate-500:                │
│   "1 confirmed · 3 alerted · 1 declined · 3 pending"    │
├─────────────────────────────────────────────────────────┤
│ CardFooter (flex gap-2 border-t border-slate-100 pt-3): │
│   [📞 Voice Call]  bg-red-50 text-red-600 border-red-200│
│   [⚡ Override]    outline variant                       │
│   [🚨 Escalate]   ghost variant text-slate-500          │
└─────────────────────────────────────────────────────────┘

ChainDot COMPONENT:
```tsx
function ChainDot({ status, position, donorId }: ChainDotProps) {
  const config = {
    CONFIRMED: { bg: 'bg-emerald-500', text: 'text-white', icon: '✓', pulse: false },
    ALERTED:   { bg: 'bg-amber-500',   text: 'text-white', icon: '!', pulse: true  },
    DECLINED:  { bg: 'bg-red-500',     text: 'text-white', icon: '✗', pulse: false },
    PENDING:   { bg: 'bg-slate-200',   text: 'text-slate-400', icon: '·', pulse: false },
    VOICE:     { bg: 'bg-yellow-400',  text: 'text-white', icon: '📞', pulse: true  },
    COMPLETED: { bg: 'bg-teal-600',    text: 'text-white', icon: '●', pulse: false },
  };
  const c = config[status];
  return (
    <Tooltip content={`D-${donorId} · ${status}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center
                       text-xs font-bold transition-all duration-300 cursor-pointer
                       ${c.bg} ${c.text} ${c.pulse ? 'animate-pulse' : ''}`}>
        {c.icon}
      </div>
    </Tooltip>
  );
}
```

WEBSOCKET REAL-TIME BEHAVIOR:
  Event "chain_update" received:
    → Find emergency card matching patient_id
    → Find ChainDot at donor's chain_position
    → Animate: prev color → scale-110 (150ms) → new color (300ms)
    → Sonner toast: "✅ Rahul Kumar confirmed for P-10234!"
    → If status=CONFIRMED: confetti micro-animation on dot

  Event "chain_break" received:
    → Insert red banner above cards:
      "⚠️ Chain Break — P-10234 · Position 4 · Auto-repair in progress"
      bg-red-500 text-white text-sm py-2 px-4 rounded-lg animate-bounce once

  Event "new_emergency" received:
    → Prepend new card to grid (slide-in from top, 400ms)
    → Sonner toast destructive: "🚨 New Emergency: B+ · KIMS"

NEW EMERGENCY DIALOG:
  shadcn Dialog triggered by [+ New Emergency] button
  Fields:
    Patient ID*  → Input, font-mono, auto-uppercase on change
    Blood Type*  → Select: O-, O+, A-, A+, B-, B+, AB-, AB+
    City*        → Select: Hyderabad, Bangalore, Chennai, Mumbai...
    Ward/Area*   → Input text
    Hospital*    → Input text
    Urgency      → Switch "Override AI urgency scoring" (default off)
  Submit button: [⚡ Activate AI Agents]
    Loading state: spinner + "LangGraph agents activating..."
    Success: Dialog closes, new card slides into grid
```

---

### 16.3 Dashboard 2 — Blood Bridge Graph Visualization

**File:** `app/dashboard/graph/page.tsx`
**Library:** `react-force-graph-2d`

```
LAYOUT:
  Left panel:   w-full canvas (flex-1, relative)
  Right panel:  w-80 Sheet drawer (slides out on node click)

FILTER BAR (h-12 bg-white border-b border-slate-200 px-4 flex gap-3):
  [Patient: All ▼]   [Status: All ▼]   [City: Hyderabad ▼]
  Right side: [⏸ Pause] [📷 Screenshot] [? Legend]

GRAPH CANVAS (bg-slate-900, calc(100vh - 10rem)):
  Dark background makes colored nodes pop dramatically

NODE SPECIFICATIONS:
  Patient Node:
    Shape:   Diamond (drawn via canvas ctx.save/rotate/fillRect)
    Radius:  22
    Fill:    #EF4444 (red-500)
    Stroke:  white 2px
    Label:   patient_id below, white 10px Inter

  Donor Node:
    Shape:   Circle
    Radius:  8 + (antigen_score × 14)  ← size = match quality
    Fill:    status color (see 15.2)
    Stroke:  if churn_score > 0.75: red dashed ring 2px (warning halo)
    Label:   first name below, white 9px Inter

  Hospital Node:
    Shape:   Rounded square
    Radius:  14
    Fill:    #475569 (slate-600)
    Label:   short name, white 9px

EDGE SPECIFICATIONS:
  COMPATIBLE_WITH (pre-computed, always visible):
    Width:  antigen_score × 4  (min 2.4px, max 4px)
    Color:  #0D9488 teal-600
    Style:  solid

  IN_CHAIN CONFIRMED:
    Width:  3px   Color: #10B981 emerald   Style: solid

  IN_CHAIN ALERTED:
    Width:  2px   Color: #F59E0B amber     Style: dashed (animated)
    Animation: linkLineDash offset increments each frame

  IN_CHAIN DECLINED:
    Width:  2px   Color: #EF4444 red       Style: solid

  NEAR_BANK:
    Width:  1px   Color: #94A3B8 slate-400 Style: dotted

REACT IMPLEMENTATION:
```tsx
import ForceGraph2D from 'react-force-graph-2d';

const NODE_COLORS = {
  CONFIRMED: '#10B981', ALERTED: '#F59E0B', DECLINED: '#EF4444',
  PENDING: '#CBD5E1', COMPLETED: '#0D9488', VOICE: '#FBBF24',
};

<ForceGraph2D
  graphData={graphData}
  backgroundColor="#0F172A"
  nodeColor={node =>
    node.type === 'patient'  ? '#EF4444' :
    node.type === 'hospital' ? '#475569' :
    NODE_COLORS[node.status] || '#CBD5E1'
  }
  nodeVal={node =>
    node.type === 'patient'  ? 484 :
    node.type === 'donor'    ? Math.pow(8 + node.antigen_score * 14, 2) :
    196
  }
  linkWidth={link => (link.antigen_score || 0.5) * 4}
  linkColor={link => {
    const c = { CONFIRMED:'#10B981', ALERTED:'#F59E0B',
                DECLINED:'#EF4444', default:'#0D9488' };
    return c[link.status] || c.default;
  }}
  linkLineDash={link => link.status === 'ALERTED' ? [5,5] : null}
  onNodeClick={node => node.type === 'donor' && setSelectedDonor(node)}
  nodeCanvasObjectMode={() => 'after'}
  nodeCanvasObject={(node, ctx) => {
    // Draw churn warning ring
    if (node.churn_score > 0.75) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + 4, 0, 2 * Math.PI);
      ctx.strokeStyle = '#EF4444';
      ctx.lineWidth = 2;
      ctx.setLineDash([3,3]);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }}
  cooldownTicks={100}
  enableNodeDrag={true}
/>
```

RIGHT DRAWER (shadcn Sheet, side="right", className="w-80"):
┌───────────────────────────────┐
│ Rahul Kumar              [×]  │  ← SheetHeader
│ Donor D-1023                  │  ← font-mono text-slate-500 text-xs
├───────────────────────────────┤
│ 🩸 B+          📍 4.2 km      │  ← grid grid-cols-2 gap-3
│ 🧬 Score: 0.87 ⏰ 68d ago     │
│ 💉 13 donations               │
│ 🏆 Life Saver badge           │
│                               │
│ Churn Risk                    │
│ [██░░░░░░░░] 0.12 LOW         │  ← Progress + badge
│                               │
│ Chain Status                  │
│ <Badge>ALERTED</Badge>        │  ← amber Badge
│ Alerted at 2:14 PM            │
├───────────────────────────────┤
│ [📞 Force Call Now]           │  ← bg-red-500 full width
│ [💬 Send AI Message]          │  ← outline full width mt-2
└───────────────────────────────┘
```

---

### 16.4 Dashboard 3 — Blood Availability Map

**File:** `app/dashboard/map/page.tsx`
**Libraries:** `react-leaflet` · `leaflet`

```
LAYOUT: flex h-full
  Left:  flex-1 (70%) — react-leaflet map
  Right: w-80 (30%) — scrollable bank list

MAP CONFIGURATION:
  Center:    [17.3850, 78.4867] — Hyderabad
  Zoom:      11
  Tile URL:  https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png
  Attribution: CartoDB (clean, light, medical aesthetic — no Google Maps required)

HOSPITAL MARKER (current patient's hospital):
  Icon: Red cross SVG, size 40px
  Pulsing ring: position absolute, w-24 h-24 rounded-full
                bg-red-500 opacity-30, animate-ping
  Popup: "Patient P-10234 · KIMS Secunderabad · B+ needed"

BLOOD BANK CUSTOM SVG PIN:
  function createBankIcon(totalUnits: number): L.DivIcon {
    const color = totalUnits > 5 ? '#10B981'
                : totalUnits > 0 ? '#F59E0B' : '#EF4444';
    return L.divIcon({
      html: `<svg viewBox="0 0 24 32" width="28" height="36">
        <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20S24 21 24 12 18.6 0 12 0z"
              fill="${color}" stroke="white" stroke-width="1.5"/>
        <circle cx="12" cy="12" r="5" fill="white"/>
      </svg>`,
      iconSize: [28, 36], iconAnchor: [14, 36], className: '',
    });
  }

POPUP (on marker click):
  "Nizam's Institute Blood Bank\n
   B+: 8u  O+: 3u  AB-: 0u\n
   📞 040-23489000\n
   [📍 Directions]"

FLOATING FILTER (top-right on map, bg-white/90 rounded-xl shadow p-3):
  Blood Type: [B+ ▼]  Radius: [10 km ●───]

RIGHT LIST PANEL (bg-white border-l border-slate-200 overflow-y-auto):
  Header: "Blood Banks · Hyderabad"  Updated: "8 min ago"  [🔄]

  Each bank item (p-4 border-b border-slate-100 hover:bg-slate-50 cursor-pointer):
  ┌───────────────────────────────┐
  │ Nizam's Institute             │  ← font-semibold text-slate-800
  │ 2.3 km · ~8 min drive        │  ← text-sm text-slate-500
  │                               │
  │ B+ ████████░░ 8u              │  ← mini progress bar
  │ O+ ████░░░░░░ 3u              │    emerald if >5, amber >0, red 0
  │ AB-░░░░░░░░░░ 0u              │    text-xs font-mono
  │                               │
  │ 📞 040-23489000               │  ← text-xs text-slate-500
  │ [📍 Get Directions →]         │  ← outline Button xs
  └───────────────────────────────┘

  Click item → map.flyTo(bank.lat, bank.lng, zoom=14) + opens popup
```

---

### 16.5 Dashboard 4 — Donor Engagement & Churn Panel

**File:** `app/dashboard/donors/page.tsx`

```
PAGE HEADER (flex justify-between mb-6):
  Left:  "Donor Engagement Center" text-2xl font-bold
  Right: [⚡ Run AI Outreach Batch] bg-teal-600
         [📥 Export CSV] outline

METRIC ROW (grid grid-cols-4 gap-4 mb-6):
  Active Donors:   "312 / 500"  text-emerald-500  "Active rate: 62%"
  Avg Response:    "71%"        text-teal-600      "Response rate"
  At-Risk Donors:  "47"         text-red-500       "churn_score > 0.50"
  Donated This Mo: "89"         text-emerald-500   "This month"

ANALYTICS CHARTS (grid grid-cols-2 gap-6 mb-6):
  LEFT — Active Donor Rate (last 30 days):
    <AreaChart data={trendData} width="100%" height={200}>
      <defs>
        <linearGradient id="teal" x1="0" y1="0" x2="0" y2="1">
          <stop offset="5%"  stopColor="#0D9488" stopOpacity={0.3}/>
          <stop offset="95%" stopColor="#0D9488" stopOpacity={0}/>
        </linearGradient>
      </defs>
      <Area type="monotone" dataKey="active_pct"
            stroke="#0D9488" strokeWidth={2} fill="url(#teal)"/>
      <XAxis dataKey="date" tick={{fontSize:11, fill:'#94A3B8'}}/>
      <YAxis tick={{fontSize:11, fill:'#94A3B8'}} domain={[0,100]}/>
      <Tooltip contentStyle={{background:'#1E293B',border:'none',color:'white'}}/>
    </AreaChart>

  RIGHT — Donations by City:
    <BarChart data={cityData} width="100%" height={200}>
      <Bar dataKey="donations" fill="#0D9488" radius={[4,4,0,0]}/>
      <XAxis dataKey="city" tick={{fontSize:11}}/>
      <YAxis tick={{fontSize:11}}/>
      <Tooltip/>
    </BarChart>

AT-RISK DONOR TABLE (DataTable, full width card):
  Title: "At-Risk Donors — Sorted by Churn Score"

  COLUMNS:
    Name:
      Avatar: w-8 h-8 rounded-full bg-teal-100 text-teal-700 font-semibold text-sm
              initials (first + last name first chars)
      Text:   full name font-medium text-slate-800

    Blood Type:
      <Badge className="bg-teal-50 text-teal-700 border-teal-200">B+</Badge>

    Last Donation:
      "92 days ago"
      Color: text-red-500 if >70d, text-amber-500 if 45–70d, text-slate-500 else

    Churn Score:
      <div className="flex items-center gap-2">
        <Progress value={score*100}
          className={`h-2 w-24 ${score>0.75?'[&>div]:bg-red-500':
                                  score>0.50?'[&>div]:bg-amber-500':
                                  score>0.25?'[&>div]:bg-yellow-400':
                                             '[&>div]:bg-emerald-500'}`}/>
        <span className="font-mono text-xs">{score.toFixed(2)}</span>
      </div>

    Risk Tier:
      CRITICAL → <Badge className="bg-red-100 text-red-700 border-red-200">CRITICAL</Badge>
      HIGH     → <Badge className="bg-amber-100 text-amber-700">HIGH</Badge>
      MEDIUM   → <Badge className="bg-yellow-50 text-yellow-700">MEDIUM</Badge>
      LOW      → <Badge className="bg-emerald-50 text-emerald-700">LOW</Badge>

    Actions:
      <Button size="icon" variant="ghost" onClick={() => triggerCall(donor.id)}
              title="AI Voice Call">📞</Button>
      <Button size="icon" variant="ghost" onClick={() => triggerOutreach(donor.id)}
              title="AI Telegram Message">💬</Button>
      Both: show Loader2 spinner while POST is in flight

  TABLE FILTERS:
    [Risk Tier: All ▼] [City: All ▼] [Blood Type: All ▼] [🔍 Search name]

LEADERBOARD PANEL (card below table):
  Title: "Blood Heroes · Hyderabad · This Month"
  City filter: [Hyderabad] [Mumbai] [Chennai] tab row

  Top 3 (special layout):
  ┌──────────────────────────────────┐
  │ 🥇 Rahul K.   13 lives  ████████│  ← gold bar, bg-yellow-50
  │ 🥈 Priya M.   11 lives  ██████  │  ← silver
  │ 🥉 Suresh T.   9 lives  █████   │  ← bronze
  └──────────────────────────────────┘
  Rank 4–10: compact rows, text-sm, no special bg
```

---

### 16.6 Dashboard 5 — Admin & System Config

**File:** `app/dashboard/admin/page.tsx`

```
PAGE HEADER:
  Left:  "Admin — BloodBridge AI"
  Right: "Checked 14s ago" text-slate-500 text-sm + [🔄 Refresh]

SYSTEM HEALTH GRID (grid grid-cols-3 gap-4 mb-6):
  Each service card (bg-white rounded-xl border p-4):
  ┌──────────────────────────┐
  │ ● FastAPI                │  ← status dot + name font-semibold
  │ Render.com               │  ← text-xs text-slate-500
  │ 142ms · 200 OK           │  ← text-xs font-mono
  │                          │
  │ [████████████] healthy   │  ← tiny latency bar
  └──────────────────────────┘

  Status dot logic:
    <span className={`w-2.5 h-2.5 rounded-full inline-block mr-2
      ${latency < 500  ? 'bg-emerald-500' :
        latency < 2000 ? 'bg-amber-500'   : 'bg-red-500'}`}/>

  Services shown: FastAPI, Neo4j Aura, Supabase, Telegram Bot,
                  Groq API, Gemini API, Twilio, UptimeRobot

MODEL METRICS CARD (full width):
  grid grid-cols-2 gap-6:
    LEFT — Churn Model (XGBoost):
      Trained: "2 days ago"
      Samples: "500 synthetic"
      <Progress value={87} className="h-3 [&>div]:bg-teal-600 mt-2"/>
      "87% accuracy" text-sm text-slate-600
      [🔄 Retrain Now] → POST /api/admin/retrain → shows spinner
      [📥 Download Data] → GET /api/admin/training-data

    RIGHT — Urgency Model (XGBoost):
      Trained: "2 days ago"
      Samples: "50 patients"
      <Progress value={91} className="h-3 [&>div]:bg-teal-600 mt-2"/>
      "91% accuracy"

    Note (italic text-slate-400 text-xs mt-4 col-span-2):
      "Trained on synthetic data for hackathon. Fine-tuning on Blood Warriors'
       40,000 real donor records is first post-pilot task."

STAFF WHITELIST (DataTable card):
  Columns: Telegram Username (font-mono teal-600), Hospital, Role (Badge), Added, [Remove]
  [+ Add Staff] → Dialog: username input + hospital select + role select

AGENT CONFIG (card, editable inline):
  Title: "Agent Configuration"
  Note:  "Changes apply to next agent cycle — no redeploy needed"

  Editable field row pattern:
  ┌─────────────────────────────────────────────────────┐
  │ Chain monitor interval   [5] min      [Edit] [Save] │
  │ Voice call timeout       [7] min                    │
  │ Max chain length         [8] donors                 │
  │ Churn CRITICAL threshold [0.75]                     │
  │ Churn HIGH threshold     [0.50]                     │
  │ Max Groq timeout         [1.8] sec                  │
  │ Max Gemini timeout       [1.5] sec                  │
  └─────────────────────────────────────────────────────┘
  [Save All Config] bg-teal-600 → POST /api/admin/config

LANGGRAPH TRACE VIEWER (Accordion, collapsible):
  Title: "Last 5 Emergency Agent Traces"
  Each trace (AccordionItem):
    Trigger: "P-10234 · 2h ago · SUCCESS · 8 nodes · 14.3s total"
    Content (when expanded):
      Node timeline grid:
      [intake ✓ 0.1s] → [eligibility ✓ 0.2s] → [neo4j ✓ 0.08s] → ...
      Green bg = success, Red bg = error, Yellow bg = fallback used
```

---

## PART 17 — DETAILED DEVELOPMENT EXECUTION (Engineering Playbook)

### Feature 1: 8-Antigen Compatibility Scorer

**File:** `services/compatibility.py`
**Hackathon critical trick:** Run `seed_neo4j.py` on Day 1 morning. Pre-calculate all 500 donors × 50 patients = 25,000 edges. Store in Neo4j. During demo the matching agent only runs a 50ms Cypher query — not live Python math.

```python
ANTIGEN_PENALTIES = {
    'kell':  0.35,  # Most immunogenic after ABO/Rh
    'duffy': 0.25,  # High-risk in South Asian patients
    'kidd':  0.20,
    'rh_e':  0.15,
    'rh_c':  0.10,
    'mns':   0.05,
}

ABO_COMPATIBLE = {
    'O-':  ['O-','O+','A-','A+','B-','B+','AB-','AB+'],
    'O+':  ['O+','A+','B+','AB+'],
    'A-':  ['A-','A+','AB-','AB+'],
    'A+':  ['A+','AB+'],
    'B-':  ['B-','B+','AB-','AB+'],
    'B+':  ['B+','AB+'],
    'AB-': ['AB-','AB+'],
    'AB+': ['AB+'],
}

def calculate_antigen_score(donor: dict, patient: dict) -> float:
    if patient['blood_type'] not in ABO_COMPATIBLE.get(donor['blood_type'], []):
        return 0.0
    score = 1.0
    if patient.get('needs_kell_negative') and not donor.get('kell_negative'):
        score -= ANTIGEN_PENALTIES['kell']
    if patient.get('needs_duffy_negative') and not donor.get('duffy_negative'):
        score -= ANTIGEN_PENALTIES['duffy']
    if patient.get('needs_kidd_safe') and not donor.get('kidd_positive'):
        score -= ANTIGEN_PENALTIES['kidd']
    if 'anti-E' in patient.get('antibody_flags', []) and donor.get('rh_e_positive'):
        score -= ANTIGEN_PENALTIES['rh_e']
    if 'anti-C' in patient.get('antibody_flags', []) and donor.get('rh_c_positive'):
        score -= ANTIGEN_PENALTIES['rh_c']
    if 'anti-M' in patient.get('antibody_flags', []) and donor.get('mns_positive'):
        score -= ANTIGEN_PENALTIES['mns']
    return max(0.0, round(score, 3))

# seed_neo4j.py — run ONCE before demo, creates all COMPATIBLE_WITH edges
def seed_compatible_edges(donors, patients, driver):
    with driver.session() as session:
        for patient in patients:
            for donor in donors:
                score = calculate_antigen_score(donor, patient)
                if score >= 0.60:
                    session.run("""
                        MATCH (d:Donor {donor_id: $did}), (p:Patient {patient_id: $pid})
                        MERGE (d)-[r:COMPATIBLE_WITH]->(p)
                        SET r.antigen_score=$score, r.kell_safe=$ks,
                            r.duffy_safe=$ds, r.kidd_safe=$kis
                    """, did=donor['donor_id'], pid=patient['patient_id'],
                         score=score,
                         ks=not(patient.get('needs_kell_negative') and not donor.get('kell_negative')),
                         ds=not(patient.get('needs_duffy_negative') and not donor.get('duffy_negative')),
                         kis=not(patient.get('needs_kidd_safe') and not donor.get('kidd_positive')))

# Live Cypher query used in neo4j_matching_node
MATCHING_CYPHER = """
MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p:Patient {patient_id: $pid})
WHERE c.antigen_score >= 0.70 AND c.kell_safe=$needs_kell_safe
  AND c.duffy_safe=$needs_duffy_safe AND d.days_since_donation >= 56
  AND d.is_eligible=true AND d.medical_hold=false
WITH d, c,
  point.distance(
    point({latitude: d.lat, longitude: d.lng}),
    point({latitude: $hosp_lat, longitude: $hosp_lng})
  ) AS dist_m
ORDER BY c.antigen_score DESC, dist_m ASC LIMIT 8
RETURN d.donor_id, d.name, d.phone, d.telegram_chat_id,
       c.antigen_score, dist_m/1000 AS dist_km
"""
```

---

### Feature 2: LangGraph StateGraph

**Files:** `agents/state.py` · `agents/graph.py`

```python
# agents/state.py
from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    request_id: str
    patient_id: str
    blood_type: str
    city: str
    hemoglobin: float
    days_since_last_transfusion: int
    needs_kell_negative: bool
    needs_duffy_negative: bool
    antibody_flags: List[str]
    urgency_score: float
    priority: str                   # CRITICAL / HIGH / ROUTINE
    hospital_name: str
    hospital_lat: float
    hospital_lng: float
    eligible_donors: List[dict]
    scored_donors: List[dict]
    ranked_donors: List[dict]
    chain_status: dict
    alerted_donors: List[str]
    confirmed_donors: List[str]
    declined_donors: List[str]
    conflict_detected: bool
    conflict_resolution: Optional[dict]
    messages: Annotated[list, add_messages]
    outreach_results: List[dict]
    voice_calls_active: List[str]
    blood_bank_options: List[dict]
    next_action: str
    retry_count: int
    outcome: str                    # SUCCESS / ESCALATED / IN_PROGRESS
    agent_log: List[dict]

# agents/graph.py
from langgraph.graph import StateGraph, END
from agents.state import AgentState

def build_emergency_graph():
    graph = StateGraph(AgentState)
    graph.add_node("intake",            intake_node)
    graph.add_node("eligibility",       eligibility_filter_node)
    graph.add_node("antigen_scoring",   antigen_scoring_node)
    graph.add_node("urgency_scoring",   urgency_scoring_node)
    graph.add_node("neo4j_matching",    neo4j_matching_node)
    graph.add_node("conflict_resolver", conflict_resolver_node)
    graph.add_node("planner",           planner_node)
    graph.add_node("outreach",          outreach_node)
    graph.add_node("chain_monitor",     chain_monitor_node)
    graph.add_node("chain_repair",      chain_repair_node)
    graph.add_node("voice_agent",       voice_agent_node)
    graph.add_node("inventory_agent",   inventory_agent_node)
    graph.add_node("gamification",      gamification_node)
    graph.add_node("outcome",           outcome_node)
    graph.add_node("escalate",          escalate_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake",          "eligibility")
    graph.add_edge("eligibility",     "antigen_scoring")
    graph.add_edge("antigen_scoring", "urgency_scoring")
    graph.add_edge("urgency_scoring", "neo4j_matching")
    graph.add_conditional_edges("neo4j_matching", route_after_matching,
        {"conflict": "conflict_resolver", "no_conflict": "planner"})
    graph.add_edge("conflict_resolver", "planner")
    graph.add_edge("planner",           "outreach")
    graph.add_edge("outreach",          "chain_monitor")
    graph.add_conditional_edges("chain_monitor", route_after_monitor, {
        "all_confirmed": "outcome",
        "needs_voice":   "voice_agent",
        "needs_repair":  "chain_repair",
        "in_progress":   "chain_monitor",
        "escalate":      "inventory_agent",
    })
    graph.add_edge("voice_agent",     "chain_monitor")
    graph.add_edge("chain_repair",    "chain_monitor")
    graph.add_edge("inventory_agent", "escalate")
    graph.add_edge("outcome",         "gamification")
    graph.add_edge("gamification",    END)
    graph.add_edge("escalate",        END)
    return graph.compile()

def route_after_matching(state):
    return "conflict" if state.get("conflict_detected") else "no_conflict"

def route_after_monitor(state):
    if len(state.get("confirmed_donors", [])) >= 1: return "all_confirmed"
    if state.get("retry_count", 0) >= 3:             return "escalate"
    if state.get("stale_nodes"):                      return "needs_voice"
    if state.get("broken_nodes"):                     return "needs_repair"
    return "in_progress"

EMERGENCY_GRAPH = build_emergency_graph()
```

---

### Feature 3: Chain Auto-Repair (APScheduler)

**File:** `main.py` — runs inside FastAPI lifespan

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=5)
async def chain_monitor_job():
    async with neo4j_driver.async_session() as session:
        # Find stale ALERTED nodes (>7 minutes)
        stale = await session.run("""
            MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
            WHERE r.status='ALERTED'
              AND r.alerted_at < datetime() - duration('PT7M')
            RETURN p.patient_id AS pid, d.donor_id AS did, d.phone AS phone
        """)
        for node in [r async for r in stale]:
            asyncio.create_task(voice_agent_node.trigger(node['did'], node['pid']))

        # Find DECLINED/UNREACHABLE → repair chain
        broken = await session.run("""
            MATCH (d:Donor)-[r:IN_CHAIN]->(p:Patient)
            WHERE r.status IN ['DECLINED','UNREACHABLE']
            RETURN p.patient_id AS pid, d.donor_id AS did, r.chain_position AS pos
        """)
        for node in [r async for r in broken]:
            asyncio.create_task(chain_repair_node.repair(node['pid'], node['pos']))

    await ws_manager.broadcast("chain_monitor_tick", {
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

### Feature 4: AI Voice Call Pipeline

**File:** `agents/voice_agent_node.py`

```python
LANG_TO_GTTS   = {'hi':'hi','te':'te','ta':'ta','kn':'kn','bn':'bn','en':'en'}
LANG_TO_TWILIO = {'hi':'hi-IN','te':'te-IN','ta':'ta-IN','kn':'kn-IN','en':'en-IN'}

async def voice_agent_node(state: AgentState, donor: dict):
    lang = donor.get('preferred_language', 'en')

    # Gemini: generate 30-sec script in donor's language
    prompt = (f"Write a 30-second spoken voice script in {lang}. "
              f"Donor: {donor['name']}. Blood type needed: {state['blood_type']}. "
              f"Hospital: {state['hospital_name']}. Lives saved: {donor['lives_saved']}. "
              f"Warm, urgent, personal. End with clear yes/no question. Max 70 words. Plain text only.")
    script = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt).text

    # gTTS → MP3
    buf = io.BytesIO()
    gTTS(text=script, lang=LANG_TO_GTTS.get(lang,'en'), slow=False).write_to_fp(buf)
    audio_key = f"voice/{state['request_id']}/{donor['donor_id']}.mp3"
    supabase.storage.from_('voice-clips').upload(audio_key, buf.getvalue())
    audio_url = supabase.storage.from_('voice-clips').get_public_url(audio_key)

    # Twilio TwiML
    twiml = f"""<?xml version="1.0"?><Response>
        <Play>{audio_url}</Play>
        <Gather input="speech" timeout="4" language="{LANG_TO_TWILIO.get(lang,'en-IN')}"
                action="/webhook/voice-response?donor_id={donor['donor_id']}&patient_id={state['patient_id']}">
            <Play>{audio_url}</Play>
        </Gather></Response>"""

    call = Client(TWILIO_SID, TWILIO_TOKEN).calls.create(
        to=donor['phone'], from_=TWILIO_NUMBER, twiml=twiml
    )
    await ws_manager.broadcast("voice_call_active", {"donor_id": donor['donor_id']})

# Keyword NLU — /webhook/voice-response
INTENT_KEYWORDS = {
    'ConfirmDonation':   ['haan','ha','yes','kar sakta','theek','bilkul','zaroor',
                          'avunu','sari','aamam','aaunga','ready'],
    'DeclineDonation':   ['nahi','na','no','busy','abhi nahi','nahin',
                          'ledu','illa','illai','mudiyathu'],
    'RequestReschedule': ['kal','tomorrow','baad','later','shaam','evening',
                          'repu','ratri','subah'],
    'AskMoreInfo':       ['kahan','where','kab','when','hospital','kitna','ekkada'],
}
def keyword_nlu(speech: str) -> str:
    t = speech.lower()
    scores = {i: sum(1 for kw in kws if kw in t) for i, kws in INTENT_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'AskMoreInfo'
```

---

### Feature 5: Multilingual Telegram Bot + OCR

**File:** `handlers/telegram_handler.py`

```python
async def detect_language(text: str, phone: str) -> str:
    if len(text.strip()) < 3:
        mem = await supabase.table('donor_memory').select('preferred_language')\
              .eq('phone', phone).single().execute()
        return (mem.data or {}).get('preferred_language', 'en')
    try:
        return detect(text)
    except:
        return 'en'

async def handle_message(update, context):
    text = update.message.text
    chat_id = str(update.effective_chat.id)
    donor = await get_donor_by_telegram_id(chat_id)
    phone = (donor or {}).get('phone', '')
    lang_code = await detect_language(text, phone)
    lang_name = LANG_NAMES.get(lang_code, 'English')
    await update_donor_memory(phone, lang_code, text)

    system = (f"You are BloodBridge AI. Respond ONLY in {lang_name}. "
              f"Under 150 chars. Warm, urgent when needed. Never robotic. "
              f"Donor: {(donor or {}).get('name','friend')}, "
              f"donations={(donor or {}).get('donation_count',0)}")
    try:
        reply = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":text}],
            max_tokens=120, timeout=1.8
        ).choices[0].message.content
    except:
        FALLBACK = {'hi':"Namaste! Kaise madad kar sakta hoon? /help",
                    'te':"Namaskaram! Ela sahayam? /help",
                    'en':"Hello! Type /help for commands."}
        reply = FALLBACK.get(lang_code, FALLBACK['en'])
    await context.bot.send_message(chat_id=chat_id, text=reply)

# OCR blood card photo
async def handle_photo(update, context):
    photo = await (await update.message.photo[-1].get_file()).download_as_bytearray()
    raw = pytesseract.image_to_string(Image.open(io.BytesIO(photo)))
    match = re.search(r'\b(A|B|AB|O)\s*[+\-](ve|positive|negative)?\b', raw, re.IGNORECASE)
    if match:
        blood_type = normalize_blood_type(match.group(0))
        await supabase.table('donors').upsert(
            {'telegram_chat_id': str(update.effective_chat.id), 'blood_type': blood_type},
            on_conflict='telegram_chat_id').execute()
        reply = f"🩸 Blood type *{blood_type}* saved! Ready to save lives."
    else:
        reply = "Couldn't read clearly. Type your blood type: A+, B-, O+, AB-, etc."
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text=reply, parse_mode='Markdown')
```

---

### Feature 6: XGBoost Churn Model

**Files:** `models/train.py` · `agents/churn_agent_node.py`

```python
# models/train.py — Run Day 1, save model
FEATURES = ['days_since_donation','avg_response_time_hours',
            'missed_alerts_last_90d','gamification_events_30d',
            'donation_frequency_trend','days_since_last_badge',
            'preferred_contact_responded','donation_count_normalized']

def train_churn_model(donors_df):
    X, y = donors_df[FEATURES], donors_df['churned']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = xgb.XGBClassifier(n_estimators=100, max_depth=5,
                               learning_rate=0.1, eval_metric='logloss')
    model.fit(X_train, y_train)
    print(f"Accuracy: {model.score(X_test, y_test):.3f}")
    joblib.dump(model, 'models/churn_model.joblib')

# Nightly cron (Render.com: 0 20 * * *)
async def run_churn_batch():
    model = joblib.load('/tmp/churn_model.joblib')
    donors = pd.DataFrame((await supabase.table('donors')
                           .select(','.join(FEATURES+['donor_id'])).execute()).data)
    probs = model.predict_proba(donors[FEATURES])[:, 1]
    for i, row in donors.iterrows():
        score = float(probs[i])
        risk = ('CRITICAL' if score>0.75 else 'HIGH' if score>0.50
                else 'MEDIUM' if score>0.25 else 'LOW')
        await supabase.table('donors').update(
            {'churn_score':score,'churn_risk':risk}
        ).eq('donor_id', row['donor_id']).execute()
        if   risk == 'CRITICAL': asyncio.create_task(voice_agent_node.trigger_churn(row['donor_id']))
        elif risk == 'HIGH':     asyncio.create_task(outreach_llm_node.send(row['donor_id']))
        elif risk == 'MEDIUM':   asyncio.create_task(gamification_node.unlock_challenge(row['donor_id']))
    await ws_manager.broadcast("churn_batch_complete", {"scored": len(donors)})
```

---

### Feature 7: Gamification — Badges + SVD Challenges

**File:** `services/gamification_service.py`

```python
BADGE_RULES = [
    {'id':'blood_starter', 'name':'Blood Starter 🌱',
     'cond': lambda d: d['donation_count'] == 1},
    {'id':'life_saver',    'name':'Life Saver ❤️',
     'cond': lambda d: d['donation_count'] == 5},
    {'id':'blood_hero',    'name':'Blood Hero 🦸',
     'cond': lambda d: d['donation_count'] == 12},
    {'id':'crisis_hero',   'name':'Crisis Hero ⚡',
     'cond': lambda d: d.get('response_hours', 99) < 2},
    {'id':'rare_guardian', 'name':'Rare Guardian 💎',
     'cond': lambda d: d.get('kell_negative') and d['donation_count'] >= 3},
    {'id':'city_champion', 'name':'City Champion 🏆',
     'cond': lambda d: d.get('city_rank', 99) <= 3},
]

async def check_and_award_badges(donor_id: str):
    donor = await get_donor(donor_id)
    existing = donor.get('badges', [])
    new_badges = [r for r in BADGE_RULES
                  if r['id'] not in existing and r['cond'](donor)]
    if new_badges:
        await supabase.table('donors').update(
            {'badges': existing + [r['id'] for r in new_badges]}
        ).eq('donor_id', donor_id).execute()
        for badge in new_badges:
            await telegram_bot.send_message(
                chat_id=donor['telegram_chat_id'],
                text=f"🏅 *New Badge!*\n{badge['name']}\nType /mystats to see all!",
                parse_mode='Markdown')

# SVD Challenge Recommender
async def recommend_challenge(donor_id: str) -> str:
    df = pd.DataFrame((await supabase.table('donors')
                       .select('donor_id,donation_count,response_rate,gamification_events_30d,completed_challenges')
                       .execute()).data)
    X = StandardScaler().fit_transform(
        df[['donation_count','response_rate','gamification_events_30d']].values)
    donor_idx = df[df['donor_id']==donor_id].index[0]
    sims = np.dot(X, X[donor_idx]) / (np.linalg.norm(X,axis=1)*np.linalg.norm(X[donor_idx])+1e-8)
    top10 = np.argsort(sims)[::-1][1:11]
    CHALLENGES = ['Weekend Warrior','Early Bird','Crisis Responder','Streak Master']
    counts = {c: sum(1 for i in top10 if c in (df.iloc[i].get('completed_challenges') or []))
              for c in CHALLENGES}
    best = max(counts, key=counts.get)
    pct = round(counts[best]/len(top10)*100)
    return (f"🎯 *Challenge: {best}*\n{pct}% of donors like you finished it!\n"
            f"Reward: 🥈 Silver Badge\nType /confirm after donating!")
```

---

### Feature 8: /confirm Outcome Tracker

**File:** `handlers/telegram_handler.py`

```python
async def handle_confirm(update, context):
    chat_id = str(update.effective_chat.id)
    # Auth check
    wl = await supabase.table('staff_whitelist').select('*')\
         .eq('telegram_chat_id', chat_id).execute()
    if not wl.data:
        await update.message.reply_text("❌ Only authorized staff can confirm outcomes.")
        return
    patient_id = (context.args or [None])[0]
    if not patient_id:
        await update.message.reply_text("Usage: /confirm P-10234 done")
        return

    # Supabase patient update
    await supabase.table('patients').update(
        {'last_transfusion_date':'now()', 'days_since_last_transfusion':0}
    ).eq('patient_id', patient_id).execute()

    # Neo4j: complete chain
    async with neo4j_driver.async_session() as s:
        await s.run("""MATCH (d)-[r:IN_CHAIN]->(p {patient_id:$pid})
                       WHERE r.status='CONFIRMED'
                       SET r.status='COMPLETED', r.completed_at=datetime()""",
                    pid=patient_id)
        await s.run("""MATCH (d)-[r:IN_CHAIN]->(p {patient_id:$pid})
                       WHERE r.status IN ['PENDING','ALERTED']
                       SET r.status='RELEASED'""", pid=patient_id)

    # Update confirmed donors
    confirmed = (await supabase.table('chains').select('donor_id')
                 .eq('patient_id', patient_id).eq('status','CONFIRMED').execute()).data
    for rec in confirmed:
        did = rec['donor_id']
        await supabase.table('donors').update(
            {'lives_saved': supabase.func('lives_saved+1'),
             'donation_count': supabase.func('donation_count+1'),
             'days_since_donation': 0, 'churn_score': 0.1}
        ).eq('donor_id', did).execute()
        await check_and_award_badges(did)
        donor = await get_donor(did)
        patient = await get_patient(patient_id)
        story = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":
                f"2-sentence emotional thank you in {donor['preferred_language']} "
                f"for donor {donor['name']} who helped a Thalassemia patient at "
                f"{patient['hospital']}. Warm, personal, anonymized."}],
            max_tokens=100).choices[0].message.content
        await telegram_bot.send_message(
            chat_id=donor['telegram_chat_id'],
            text=f"💉 *Transfusion Confirmed!*\n\n{story}\n\nType /mystats! 🏆",
            parse_mode='Markdown')

    await ws_manager.broadcast("emergency_completed", {"patient_id": patient_id})
    await update.message.reply_text(f"✅ Outcome recorded for {patient_id}. Chain closed!")
```

---

### Feature 9: e-RaktKosh Inventory

**File:** `services/eraktkosh_service.py`

```python
async def fetch_blood_stock(blood_type: str, city: str) -> list:
    pk = f"{blood_type}#{city}"
    cached = (await supabase.table('blood_stock').select('blood_banks,expires_at')
              .eq('pk', pk).execute()).data
    if cached and cached[0]['expires_at'] > datetime.utcnow().isoformat():
        return cached[0]['blood_banks']

    banks = await scrape_eraktkosh(blood_type, city) or load_mock_data(city)

    expires = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
    await supabase.table('blood_stock').upsert(
        {'pk': pk, 'blood_banks': banks, 'expires_at': expires}).execute()
    await sync_blood_banks_to_neo4j(banks)
    return banks

async def scrape_eraktkosh(blood_type, city) -> list:
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.post("https://eraktkosh.mohfw.gov.in/BLDAHIMS/bloodbank/transactions/hsbbtransaction.cnt",
                data={'bloodGroup':blood_type,'stateName':'TELANGANA','districtName':city},
                headers={'User-Agent':'Mozilla/5.0','Referer':'https://eraktkosh.mohfw.gov.in/'})
            soup = BeautifulSoup(r.text,'html.parser')
            return [parse_bank_row(row) for row in soup.select('table tbody tr')
                    if parse_bank_row(row)]
    except:
        return []

def load_mock_data(city):
    with open('data/mock_blood_banks.json') as f:
        return [b for b in json.load(f) if b.get('city')==city]
```

---

### Feature 10: FastAPI WebSocket + Next.js Client

**Backend:** `handlers/websocket_handler.py`

```python
class ConnectionManager:
    def __init__(self): self.active: list[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept(); self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
    async def broadcast(self, event: str, data: dict):
        msg = json.dumps({"event":event,"data":data,
                          "ts":datetime.utcnow().isoformat()})
        dead = []
        for ws in self.active:
            try: await ws.send_text(msg)
            except: dead.append(ws)
        for d in dead: self.active.remove(d)

ws_manager = ConnectionManager()

@app.websocket("/ws/emergency")
async def ws_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True: await websocket.receive_text()  # keep-alive
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

**Frontend hook:** `hooks/useEmergencySocket.ts`

```typescript
export function useEmergencySocket() {
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/emergency`);

    ws.onmessage = (e) => {
      const { event, data } = JSON.parse(e.data);

      if (event === 'chain_update') {
        setEmergencies(prev => prev.map(em =>
          em.patient_id !== data.patient_id ? em : {
            ...em,
            chain: em.chain.map((d: ChainDonor) =>
              d.donor_id === data.donor_id ? { ...d, status: data.status } : d
            )
          }
        ));
        toast.success(`${data.donor_name} ${data.status === 'CONFIRMED' ? 'confirmed ✅' : 'updated'}`);
      }
      if (event === 'new_emergency')    { setEmergencies(p => [data, ...p]); toast.error('🚨 New Emergency: '+data.blood_type); }
      if (event === 'chain_break')      { toast.error('⚠️ Chain Break: '+data.patient_id, { duration: 10000 }); }
      if (event === 'emergency_completed') { toast.success('✅ Transfusion confirmed: '+data.patient_id); }
    };

    return () => ws.close();
  }, []);

  return { emergencies };
}
```

---

## PART 18 — AI CHEAT SHEET (Hackathon Unblock Prompts)

> When stuck at 2 AM, copy-paste these exact prompts to get instant code.

### LangGraph & Backend
1. *"Give me the exact Python code for AgentState TypedDict and build_emergency_graph() with all conditional edges for BloodBridge AI."*
2. *"Write the FastAPI WebSocket manager code to broadcast donor status updates to the Next.js dashboard."*
3. *"Give me the exact Python 8-antigen compatibility scorer with ISBT penalty weights."*
4. *"Write the APScheduler job that checks Neo4j for stale ALERTED nodes every 5 minutes and triggers voice agent."*

### Database & Neo4j
5. *"Give me the complete Supabase SQL schema for all 8 BloodBridge tables with Row Level Security policies."*
6. *"Write the seed_neo4j.py script that reads JSON donor/patient data and creates COMPATIBLE_WITH edges with pre-calculated antigen scores."*
7. *"Give me the exact Cypher query to find top 8 compatible donors ranked by antigen score and geographic distance using point.distance."*

### AI Voice & Telegram
8. *"Write the FastAPI webhook that receives Twilio Gather SpeechResult and uses Keyword NLU to classify Haan vs Nahi and update Neo4j chain."*
9. *"Give me Python code that uses langdetect and injects detected language into Groq Llama-3 system prompt with 1.8s timeout and template fallback."*
10. *"Write the pytesseract OCR handler that extracts blood type from Telegram photo using regex and upserts to Supabase."*

### Frontend (Next.js)
11. *"Give me Next.js React code using react-force-graph-2d for Blood Bridge chain — nodes colored by status, edges sized by antigen_score."*
12. *"Write the WebSocket client hook for Next.js listening for chain_update events and animating ChainDot from amber to emerald without page refresh."*
13. *"Give me the Tailwind + shadcn/ui Emergency Card component code with 8 ChainDot status circles and real-time update animation."*

### Emergency Fallbacks During Demo
14. *"Groq is timing out. Give me a Python dict of pre-written emergency templates in Hindi, Telugu, Tamil, and English as fallback."*
15. *"Twilio is failing. Give me a mock FastAPI endpoint that simulates a successful voice call response so dashboard still updates green."*
16. *"Write the exact 90-second demo script with timestamps — what words to say, what commands to type, what to show on screen."*

---

*BloodBridge AI — PRD v6.0 FINAL*
*Architecture · Design System · 5 Dashboard UI Specs · Engineering Playbook · AI Cheat Sheet*
*Team Inqilab | Blend360 Hackathon*
*Stack: Next.js 14 + FastAPI + LangGraph + Neo4j + Supabase + Telegram + Groq + Gemini + Twilio*
*₹0 deployment · 10+ Indian languages · 8 LangGraph agents · 5 Dashboard UIs · 15/15 criteria*
