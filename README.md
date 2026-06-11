<div align="center">

# 🩸 inqilab AI

### Autonomous AI for Blood Donor Coordination

An AI-powered multi-agent system that autonomously matches donors, coordinates outreach, repairs failed donor chains, predicts shortages, and improves donor engagement for Thalassemia patients.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.23-4581C3?logo=neo4j&logoColor=white)](https://neo4j.com)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-Claude%204-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Team Inqilab · AI forGood Hackathon 2.0 · Blend360  2026**

🏆 **AI4 Hackathon 1 Submission (WhatsApp Chatbot):** [bloodbridge-inquilab-niat](https://github.com/mysource0/bloodbridge-inquilab-niat.git)

</div>

---

## 🚨 The Problem

Thalassemia patients require blood transfusions **every 15–28 days for life**.

Blood Warriors NGO currently faces:

- Manual donor matching
- Donor chain breakdowns
- High donor attrition
- Multi-language coordination challenges
- Limited scalability across India

> When a donor declines, staff often spend hours making follow-up calls and rebuilding donor chains manually.

---

## 💡 Our Solution

BloodBridge AI is a **14-Agent Autonomous Coordination Platform** that manages the entire donor lifecycle:

```
Request → Matching → Outreach → Monitoring → Chain Repair → Confirmation → Learning
```

The system can coordinate donor networks with **minimal human intervention** while continuously improving its future decisions.

---

## 🏗 Core Architecture

```
┌─────────── USERS ───────────┐
│  Telegram Bot                │
│  Staff Dashboard             │
└──────────┬──────────────────┘
           │
┌──────────▼──────────────────┐
│     FastAPI Backend          │
│  ├── LangGraph Multi-Agent   │
│  ├── Matching Engine         │
│  ├── Churn Prediction        │
│  ├── Demand Forecasting      │
│  └── Self-Healing Chains     │
└──┬───────┬──────┬────────┬──┘
   │       │      │        │
Supabase  Neo4j  Bedrock  Bolna AI
                           & AWS
```

---

## ✨ Key Features

### 🩸 Smart Matching

- Geo Radius-Tier Matching
- Weighted Donor Scoring
- Multi-Location Search
- Hungarian Assignment Optimization
- ABO + Rh Compatibility

### 🔗 Autonomous Coordination

- 14-Agent LangGraph Workflow
- Automated Outreach
- Real-Time Monitoring
- AI Voice Escalation
- Self-Healing Donor Chains
- Blood Bank Fallback Routing

### 💚 Donor Engagement

- Churn Prediction (XGBoost)
- Gamification & Badges
- Personalized Impact Stories
- Failure Learning System
- Smart Re-engagement Campaigns

### 🌍 Scale & Responsible AI

- Telegram-Based Access
- Multi-Language Support (10 Indian languages)
- DPDP 2023 Compliance
- Consent Management
- AWS Cloud Deployment

---

## 🤖 The 14-Agent System

| Agent | Responsibility |
|-------|---------------|
| **Intake** | Request Processing |
| **Eligibility** | Donor Validation |
| **Antigen Score** | Compatibility Analysis |
| **Urgency Score** | Criticality Prediction |
| **Neo4j Match** | Donor Matching |
| **Conflict Resolver** | Assignment Resolution |
| **Planner** | Outreach Strategy |
| **Outreach** | Message Delivery |
| **Monitor** | Response Tracking |
| **Repair** | Chain Recovery |
| **Voice** | AI Calling |
| **Inventory** | Blood Bank Fallback |
| **Gamification** | Rewards & Engagement |
| **Outcome** | Analytics & Learning |

---

## 🧠 AI & Machine Learning

### LLM Layer

| Model | Use Case |
|-------|----------|
| **Claude Haiku 4.5** | Telegram replies, outreach, planning |
| **Claude Sonnet 4.6** | Impact story generation |
| **Amazon Bedrock** | LLM hosting & inference |

### Machine Learning

| Model | Algorithm |
|-------|-----------|
| Churn Prediction | XGBoost |
| Urgency Prediction | XGBoost |
| Recommendation System | SVD (scikit-learn) |
| Assignment Optimization | Hungarian Algorithm (scipy) |

---

## ⚙️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11 · FastAPI · LangGraph · LangChain · APScheduler |
| **Frontend** | React · TypeScript · Vite · Framer Motion · Tailwind CSS |
| **Databases** | Supabase (PostgreSQL) · Neo4j Aura |
| **Infrastructure** | AWS EC2 · AWS S3 · CloudFront · Docker · Nginx |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mahaboobsub/AI4FullStack.git
cd AI4FullStack
```

### 2. Backend Setup

```bash
cd BloodBridge_AI_Backend

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd BloodBridge_AI_frontend

# Install dependencies
pnpm install

# Start dev server
cd artifacts/bloodbridge
pnpm run dev
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| **Backend API** | <http://localhost:8000> |
| **API Docs (Swagger)** | <http://localhost:8000/docs> |
| **Health Check** | <http://localhost:8000/health> |
| **Staff Dashboard** | <http://localhost:5173> |

### 5. Telegram Webhook (Optional)

```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Auto-register webhook
cd BloodBridge_AI_Backend
python setup_webhook.py
```

---

## 🔒 Security & Privacy

BloodBridge AI is designed with **DPDP 2023** compliance principles:

- ✅ Consent-first onboarding
- ✅ Row-Level Security (RLS)
- ✅ JWT Authentication
- ✅ Data Minimization
- ✅ Audit Logging
- ✅ Right-to-Erasure Support

---

## 🧪 Testing

```bash
cd BloodBridge_AI_Backend

# Run all tests
pytest

# Run end-to-end scenarios
python run_scenarios_ae.py

# Compile check
python -m compileall agents services
```

**Key validation scenarios:**

- Smart Matching
- Self-Healing Chains
- Telegram Agent
- Churn Prediction
- Multi-Patient Conflict Resolution

---

## 🗺 Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| **Current** | ✅ | 14-Agent Workflow · Smart Matching · Churn Prediction · Demand Forecasting · Telegram Bot · Self-Healing Chains · Gamification |
| **Phase 2** | ⏳ | 8-Antigen Matching · Advanced Clinical Safety Layer |
| **Phase 3** | 📋 | e-RaktKosh Integration · WhatsApp Channel · LoRa Offline Support · Multi-Region Deployment |

---

## ❤️ Impact

BloodBridge AI transforms donor coordination from a manual process into an autonomous, intelligent system that can:

- 📉 Reduce staff workload
- 📈 Improve donor response rates
- 🔗 Prevent donor chain failures
- 🔮 Predict shortages before emergencies
- 🩸 Help ensure no Thalassemia patient waits for blood

---

<div align="center">

### *"Every drop, coordinated by AI."*

**Built with ❤️ by Team Inqilab**

</div>
