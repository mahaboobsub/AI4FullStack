# BloodBridge AI — Testing & Execution Guide

Welcome to BloodBridge AI! This guide will walk you through how to start the platform, the full list of features available, and step-by-step instructions on how to test each feature end-to-end.

---

## 1. How to Run the Platform

Since the platform relies on external services (Supabase, Neo4j, Telegram, and Bolna), make sure your `.env` files are configured properly before starting.

### Step 1: Start the Backend (FastAPI)
Open a terminal in the root directory and run:
```powershell
cd BloodBridge_AI_Backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
*The backend API will be available at `http://localhost:8000`*
*The API Documentation (Swagger) will be at `http://localhost:8000/docs`*

### Step 2: Start the Frontend (React + Vite)
Open a new terminal in the root directory and run:
```powershell
cd BloodBridge_AI_frontend\artifacts\bloodbridge
pnpm run dev
```
*The web dashboard will be available at `http://localhost:5173`*

### Step 3: Start Ngrok (For Telegram Webhooks)
To allow the AI chatbot to receive messages from Telegram, you must expose your local backend to the internet.
Open a new terminal and run:
```powershell
ngrok http 8000
```
Leave this running. Then, in another terminal, run the webhook setup script:
```powershell
cd BloodBridge_AI_Backend
.\venv\Scripts\python.exe setup_webhook.py
```

---

## 2. List of All Features

1. **Intelligent Donor Matching (Neo4j)**: Finds exact blood type matches in the same city using Neo4j Graph DB.
2. **AI Multilingual Outreach (Groq/Llama-3)**: Generates highly personalized, multilingual text messages (English, Hindi, Telugu) to reach out to donors.
3. **Automated Voice Calls (Bolna)**: Uses AI Voice agents to literally call donors on their phones for critical emergencies.
4. **Interactive Telegram Chatbot**: Donors can chat with a Telegram bot to accept/decline requests, check badges, and earn points.
5. **Real-time Web Dashboard (Supabase Realtime)**: A beautiful dashboard that updates instantly when a new emergency is created or a donor accepts a request.
6. **Gamification & Leaderboard**: Donors earn badges ("Life Saver", "Blood Hero") and rank on a city-wide leaderboard.
7. **Emergency Request Creation**: Staff can create new requests (Low, Medium, High, Critical urgency) directly from the UI.

---

## 3. Guide to Test Each Feature

### Test 1: Real-time Dashboard & Donor Data
1. Open the frontend dashboard at `http://localhost:5173`.
2. Navigate to the **Donors** tab. You should see all 100 randomly seeded donors loaded successfully from Supabase.
3. Keep the dashboard open on the "Emergencies" tab to witness real-time WebSocket updates.

### Test 2: Create an Emergency Request (Trigger AI Matching)
1. In the web dashboard, click **"New Emergency"** or go to the specific emergency creation form.
2. Enter a patient name, City (e.g., "Hyderabad" or "Warangal"), Blood Type (e.g., "O-"), and set Urgency to **CRITICAL**.
3. Submit the request.
4. **Behind the scenes**: The FastAPI backend will hit Neo4j, find matching donors, use Groq AI to generate personalized messages in regional languages, and trigger outreaches!

### Test 3: Interact with the Telegram Chatbot
*(Make sure Ngrok and your Backend are running)*
1. Open your Telegram App and search for your Bot (the username attached to your Bot Token).
2. Type `/start` to see the bot's greeting.
3. You can reply "YES" to a simulated emergency, and the AI will recognize your intent, mark you as confirmed, and update the database!
4. Check the frontend dashboard — the emergency progress bar will instantly update in real-time as you confirm via Telegram.

### Test 4: Gamification & Badges
1. In the Telegram Bot, send the command `/badges` or ask "What is my rank?".
2. The bot will query your `donation_count` from Supabase and return your newly earned badges (e.g., "Bronze Blood Hero").
3. You can also view the Leaderboard tab on the frontend web dashboard to see the top-ranked donors for the city.

### Test 5: Automated Voice Call Trigger (Bolna AI)
*(Requires Bolna Agent ID & API Key in `.env`)*
1. If an emergency is marked as **CRITICAL**, the backend will automatically queue a voice call.
2. Alternatively, you can test it manually from the backend Swagger docs:
   - Go to `http://localhost:8000/docs`
   - Find the `POST /api/donors/{id}/trigger-voice` endpoint.
   - Enter a `donor_id` (from one of your seeded donors) and execute.
3. The Bolna AI will dial the donor's registered phone number and speak to them using an AI voice, asking them if they can donate blood immediately!

---
*Happy Testing! If any service fails, check the terminal logs for the FastAPI backend, as all AI Agent traces and database errors are printed there.*
