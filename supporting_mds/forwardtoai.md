# BloodBridge AI: Core AI Workflows & Testing Guide

This document outlines the four critical AI pipelines in the BloodBridge system and provides a step-by-step testing guide. It serves as a reference for understanding the system architecture and for AI agents (or human testers) interacting with the platform.

---

## 1. Donor Prediction & Testing (Churn Risk & ML Models)

**How it works:**
The system evaluates donors based on their behavioral history, engagement metrics, and clinical data to predict their likelihood to donate and their potential risk of dropping out (churn).
- **Behavioral Scoring:** Donors who frequently decline or ignore requests see an increase in their `churn_score`.
- **Antigen Prediction:** For patients needing multi-transfusions (e.g., Thalassemia), the system evaluates minor antigen compatibility (Kell, Duffy, Kidd) to predict the safest blood match.
- **Implementation:** Churn and response rates are updated via `services/donor_memory.py` after every interaction.

**How to test:**
1. Open the **Staff Dashboard** (`/dashboard/donors`).
2. Search for a donor and observe their "Churn Risk" badge (LOW, MEDIUM, HIGH, CRITICAL).
3. Using the **Telegram Bot**, simulate a donor declining a request multiple times.
4. Check the database (`donors` table) or dashboard to see the `churn_score` adaptively increase and the risk label update.

---

## 2. Donor-Patient Mapping (Neo4j Graph Matching Engine)

**How it works:**
BloodBridge uses **Neo4j** to map complex relationships between Patients, Donors, Hospitals, and Blood Banks. 
- During seeding/registration, `COMPATIBLE_WITH` edges are generated between compatible donors and patients.
- The `Neo4jMatcher` (in `agents/neo4j_match.py`) queries the graph to find the optimal donors for a specific patient.
- **Scoring Algorithm:** The matching engine weights donors based on:
  - Exact blood type and antigen match (+ score)
  - Geographic proximity to the hospital (+ score)
  - High churn risk or recent donation history (- penalty)

**How to test:**
1. Create a new emergency request for a Patient.
2. The `Neo4jMatcher` will execute a Cypher query to find the top $N$ available donors.
3. You can manually verify the graph by opening your Neo4j Workspace and running:
   ```cypher
   MATCH (d:Donor)-[r:COMPATIBLE_WITH]->(p:Patient {patient_id: "P-XXXX"})
   RETURN d.name, d.blood_type, r.score
   ORDER BY r.score DESC LIMIT 5
   ```

---

## 3. Donor Bridge Formation (LangGraph Orchestration)

**How it works:**
A "Bridge" is the confirmed communication chain connecting a patient's request to an available donor.
- When an emergency is triggered, `agents/graph.py` kicks off the LangGraph pipeline.
- The **Match Agent** selects the best donors from Neo4j.
- The **Outreach Agent** dispatches messages to the donors in parallel (via Telegram, SMS, or Voice depending on their `consent_records` and `preferred_language`).
- A `blood_chains` record is created in Supabase with `status='ALERTED'`.
- When the donor replies "Yes" (or `HAAN` in Hindi) to the Telegram Bot, the webhook updates the chain status to `CONFIRMED`. **The bridge is formed.**

**How to test:**
1. Log into the **Staff Portal** and click **"Trigger AI Pipeline"** for a patient.
2. Ensure you have a Telegram account registered as a donor with a matching blood type.
3. You will receive an immediate Telegram message from the BloodBridge Bot in your preferred language.
4. Reply affirmatively (e.g., "Yes, I can donate").
5. The Staff Dashboard live-map will instantly update, showing the bridge between the donor and the hospital turning **Green** (Confirmed).

---

## 4. Donor Broken Bridge Rebuild (Self-Healing AI Repair)

**How it works:**
If a donor declines the request, or if they fail to respond within the required timeframe, the bridge breaks. The AI system is designed to self-heal without human staff intervention.
- The Telegram Bot webhook catches the "No" response, or the background `chain_monitor_agent` (run by APScheduler every 5 minutes) detects an expired timeout.
- The **Chain Repair Agent** (`agents/repair.py`) is invoked.
- The agent analyzes the failure reason (e.g., `medical_hold`, `out_of_town`, `ignored`).
- It updates the broken chain node to `FAILED` or `DECLINED`.
- It queries the `Neo4jMatcher` for the **next best available donors** who were not initially contacted.
- It automatically hands off to the **Outreach Agent** to message the backup donors, thus dynamically rebuilding the bridge.

**How to test:**
1. Trigger the AI Pipeline for a patient.
2. When the Telegram Bot messages you, reply "No" or "I am out of town".
3. Check the **Staff Dashboard**: The specific chain link will turn **Red** (Failed/Declined).
4. Watch the dashboard closely: Within seconds, a new chain link will appear targeting a *different* donor.
5. The system logs in the terminal will show:
   `Background Repair: Re-running outreach for request Req-XXXX...`
   `Chain repaired dynamically.`

---

## End-to-End Autonomous Testing Script Reference

For automated testing bots, you can follow this sequence via APIs:
1. `POST /api/auth/signup` (Create a donor)
2. `POST /api/webhooks/telegram` (Simulate the `/start` command to register the chat ID)
3. `POST /api/emergencies` (Create an emergency as a hospital staff)
4. `POST /api/emergencies/{req_id}/trigger` (Start the LangGraph pipeline)
5. Read Neo4j DB to ensure `blood_chains` are in `ALERTED` state.
6. `POST /api/webhooks/telegram` (Simulate the donor replying "No" to test Rebuild, or "Yes" to test Formation).
