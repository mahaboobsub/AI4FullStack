---

# Phase 1 — Foundation & Fixes (Hour 1)

---

## Prompt A1 — Gamification Bug Fix + Amazon Bedrock LLM Migration

```
CONTEXT:
You are working on BloodBridge AI — a FastAPI + LangGraph backend for coordinating blood 
donations for Thalassemia patients. The project uses LangChain for LLM abstraction.

TASK 1 — FIX BUG:
In agents/gamification.py around line 70, there is a reference to a variable called 
`donor` that is never fetched from Supabase before being used. This causes the 
gamification agent node to crash silently at the end of every pipeline run.

Fix this by: reading the complete agent state that flows into the gamification node, 
identifying all the donor_ids present in the completed blood chain, then fetching each 
donor's full record from the Supabase `donors` table using the service role client 
before any badge logic runs. The badge threshold checks (Blood Starter at 1, Life Saver 
at 5, Blood Hero at 12, Crisis Hero for same-day, Rare Guardian for kell+3, City Champion 
for top-3) must all operate on the freshly fetched donor object.

TASK 2 — BEDROCK MIGRATION:
Replace all LLM instantiations across the entire codebase. The project currently uses 
two LLM providers: Groq (for fast real-time responses in outreach.py, telegram_bot.py) 
and Google Gemini Flash (for reasoning tasks in conflict.py, planner.py, voice.py, 
impact_story.py).

Migration mapping:
- Every instance of ChatGroq → replace with ChatBedrock using model_id 
  "amazon.nova-pro-v1:0", region "ap-south-1"
- Every instance of ChatGoogleGenerativeAI → replace with ChatBedrock using model_id 
  "anthropic.claude-3-5-haiku-20241022-v1:0", region "ap-south-1"
- For impact_story.py only (highest quality needed) → use model_id 
  "anthropic.claude-3-5-sonnet-20241022-v2:0"

In core/config.py: add AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY as 
Pydantic settings fields with env var binding.

In requirements.txt: add langchain-aws, boto3. Remove the groq and 
google-generativeai packages entirely.

Update .env.example to show the three new AWS credential variables.

The LangChain interface (invoke, ainvoke, bind_tools) must remain identical — only 
the class and model_id change. Do not touch any prompt strings or chain logic.

EXPECTED OUTCOME:
- Gamification agent completes without crashing on every pipeline run
- All LLM calls route through Amazon Bedrock
- Zero changes to prompt templates or agent logic
```

---

## Prompt A2 — BWF Dataset Seeding (Supabase + Neo4j)

```
CONTEXT:
You have two TSV files containing real Blood Warriors Foundation operational donor data 
from Hyderabad. The columns include: user_id, bridge_id, role, blood_group, gender, 
latitude, longitude, bridge_gender, bridge_blood_group, quantity_required, 
last_transfusion_date, expected_next_transfusion_date, registration_date, donor_type, 
last_contacted_date, last_donation_date, next_eligible_date, donations_till_date, 
eligibility_status, cycle_of_donations, total_calls, frequency_in_days, 
status_of_bridge, status, donated_earlier, last_bridge_donation_date, 
calls_to_donations_ratio, user_donation_active_status, inactive_trigger_comment.

TASK 1 — SUPABASE SEED:
In data/seed_supabase.py, write a seeding function that reads this TSV and transforms 
each unique user_id into a row in the `donors` table with these mappings:
- donor_id = hash of user_id (consistent SHA256 truncated to UUID format)
- blood_type = blood_group field (map "A Positive" → "A+", "O Negative" → "O-" etc.)
- lat, lng = latitude, longitude fields
- last_donation_date = last_donation_date field
- donation_count = donations_till_date field
- is_active = TRUE if user_donation_active_status is "Active"
- churn_score = calls_to_donations_ratio divided by 23 (max in dataset), capped at 1.0
- donor_type stored in a notes field for reference
- next_eligible_date from the dataset field directly
- The inactive_trigger_comment maps to a new text field called churn_risk_reason

Deduplicate by user_id — one user may appear multiple times (different bridge_ids). 
Insert only once per unique user_id. Use upsert with conflict resolution on donor_id.

TASK 2 — NEO4J SEED:
In data/seed_neo4j.py, after creating Donor nodes for all unique user_ids, create 
COMPATIBLE_WITH edges between each Bridge Donor and their bridge_id patient node.

For bridge donors (rows where bridge_id is not empty): create an IN_CHAIN relationship 
from Donor node to Patient node using bridge_id as the patient reference, with 
chain_position = 1, antigen_score = 0.85 (default since antigen data isn't in this 
dataset), frequency_days = frequency_in_days from the dataset.

Also create a TRANSFUSION_SCHEDULE property on the Patient node using 
expected_next_transfusion_date and frequency_in_days to express recurring schedule.

TASK 3 — VALIDATION:
After seeding, print a summary: total donors inserted, total bridge edges created, 
count by blood type, count by eligibility_status, count by user_donation_active_status.

EXPECTED OUTCOME:
- Neo4j graph populated with real Hyderabad donor network
- Graph visualization page shows real data instead of empty canvas
- Churn scores derived from actual calls_to_donations_ratio field
```

---

## Prompt B1 — Fully Agentic Telegram Bot (Complete Implementation)

```
CONTEXT:
BloodBridge AI has a Telegram bot in services/telegram_bot.py. It handles slash commands 
(/start, /register, /profile, /eligibility, /impact, /badges, /leaderboard, /pause, 
/resume, /nextdonation, /schedule) and has a framework for 10 Groq tool-calling tools. 
The free-text agentic path (where users type natural language instead of commands) is 
partially wired but not tested end-to-end. This is now migrating from Groq to Amazon 
Bedrock Nova Pro.

GOAL:
Make the Telegram bot fully agentic — every message a donor sends (command OR natural 
language) goes through an Amazon Bedrock Nova Pro tool-calling loop that decides which 
tool to invoke, executes it, and composes a natural, memory-aware, multilingual reply.

TASK 1 — TOOL REGISTRY (verify all 10 tools are complete):
Define or verify these 10 tools exist as proper function-schema objects that Bedrock 
can call:
1. get_donor_profile — fetches donor record by telegram_chat_id from Supabase
2. check_eligibility — runs the WHO/NBTC eligibility filter for the donor
3. get_donation_history — returns last N donations with dates and patient impact
4. toggle_availability — sets donor is_active flag, returns confirmation
5. get_badges — returns unlocked and locked badge list with progress percentages
6. get_leaderboard — returns city top-10 ranked by lives_saved
7. get_impact_story — fetches the latest AI-generated impact story for the donor
8. get_next_donation_date — computes when they're next eligible based on 56-day rule
9. report_medical_hold — sets medical_hold flag with a reason and end date
10. get_active_emergency — checks if donor is currently in an active blood chain

TASK 2 — AGENTIC LOOP:
Build an async tool-calling loop in the handle_message() function:
- Step 1: Fetch donor_memory record to build a 200-token context string 
  (preferred_language, tone_profile, emotional_anchors, badges, streak_days)
- Step 2: Prepend that context as a system message to every Bedrock call
- Step 3: Call Bedrock Nova Pro with the donor's message + system context + tool schemas
- Step 4: If response contains a tool_use block, execute the corresponding local 
  function and feed the tool_result back to Bedrock in a follow-up call
- Step 5: Repeat until response is a plain text block (no tool calls)
- Step 6: Detect language of the final response — if it's not the donor's 
  preferred_language, make one more Bedrock call asking it to translate the response
- Step 7: Send the final text via Telegram, update donor_memory.last_interaction

TASK 3 — OCR FLOW:
When a donor sends a photo (not a text message), the bot should:
- Download the image via Telegram file API
- Pass it to ocr_service.py (now using Amazon Textract)
- Parse extracted text for blood group keywords and antigen flags
- If blood group found, prompt donor to confirm and update their profile
- Store the verification in donor_verifications table with type "ocr_card"

TASK 4 — CONSENT GATEWAY:
On /start, before any other tool is accessible, invoke consent_service.py to check 
if the donor has granted consent_data_storage and consent_outreach_telegram. If not, 
send the DPDP 2023 consent message with inline keyboard buttons (Yes/No) and block 
all other functionality until consent is granted.

EXPECTED OUTCOME:
- Any natural language message like "am I eligible to donate?" correctly triggers 
  check_eligibility tool and replies in the donor's language
- All 10 tools reachable via natural language without using slash commands
- Memory context makes every reply feel personalized
- Photo messages extract blood card data automatically
```

---

## Prompt B2 — Amazon Comprehend + Textract Integration

```
CONTEXT:
BloodBridge AI uses two Python libraries that should be replaced with Amazon AWS services:
- langdetect library in services/telegram_bot.py and agents/outreach.py for detecting 
  Indian language
- pytesseract + Pillow in services/ocr_service.py for extracting text from blood donor 
  card photos

TASK 1 — REPLACE langdetect WITH Amazon Comprehend:
In every place langdetect.detect() is called, replace it with boto3 call to 
comprehend.detect_dominant_language(). The return value from Comprehend is a list of 
language codes with confidence scores — take the highest-confidence result. Map 
Comprehend's ISO codes to the internal language names the system uses (hi, ta, te, 
kn, ml, bn, mr, gu, pa, ur → map to the display names already in the codebase).

Create a utility function in services/language_service.py that wraps this single call, 
so no other file imports boto3 directly for language detection.

TASK 2 — REPLACE pytesseract WITH Amazon Textract:
In services/ocr_service.py, remove all imports of pytesseract and Pillow.

Replace with Amazon Textract analyze_document() API call using FORMS and TABLES feature 
types. The input is a base64-encoded image bytes object (received from Telegram photo 
download). Textract returns blocks of KEY_VALUE_SET and LINE types — parse these to 
extract blood group (look for patterns like "A+", "B Positive", "O-", "AB Positive"), 
donor name, and any antigen flag text (Kell negative, Duffy negative etc.).

The function signature must remain identical to what callers expect: takes image bytes, 
returns a dict with keys blood_group, name, antigens (list of strings), raw_text.

Remove pytesseract and Pillow from requirements.txt. These are now handled by boto3 
which is already in the dependency list from the Bedrock migration.

EXPECTED OUTCOME:
- Language detection works more accurately on short Telegram messages in Indian scripts
- OCR handles handwritten blood cards better than Tesseract did
- No local OCR binaries needed (no tesseract-ocr system dependency)
```

---

# Phase 2 — New Agents (Hour 2)

---

## Prompt A3 — Demand Forecast LangGraph Agent

```
CONTEXT:
BloodBridge AI uses a LangGraph StateGraph for its 14-node emergency pipeline. A new 
standalone agent is needed: a demand forecasting agent that runs on a schedule and 
provides the admin panel with weekly blood demand predictions by blood type. This agent 
reads from both the BWF transfusion schedule data and the emergency_requests historical 
data to forecast how many units of each blood type will be needed in the coming weeks.

CREATE: agents/demand_forecast_agent.py

AGENT STATE (TypedDict):
Fields: patient_schedules (list of upcoming transfusion records), historical_requests 
(list of past emergency requests with blood type and outcome), forecast_horizon_days 
(default 30), forecast_by_blood_type (dict), forecast_by_week (list of weekly buckets), 
confidence_scores (dict), shortage_alerts (list), agent_summary (str), generated_at (timestamp)

5-NODE LANGGRAPH PIPELINE:

NODE 1 — DATA_COLLECTOR:
Pull from Supabase: all rows from transfusion_schedule where scheduled_date is within 
the next forecast_horizon_days and status is PENDING or OUTREACH_STARTED. Also pull 
last 90 days of emergency_requests grouped by blood_type and week. Load this into 
state.patient_schedules and state.historical_requests.

NODE 2 — SCHEDULE_ANALYZER:
For each upcoming transfusion in patient_schedules, extract blood_type and scheduled_date. 
Build a dictionary: for each of the next 4 weeks, count how many units of each blood 
type are needed. This is the baseline deterministic forecast. Also flag any blood types 
where demand in any week exceeds 5 units as high-demand periods.

NODE 3 — HISTORICAL_PATTERN_NODE:
Using historical_requests data, compute a weekly demand multiplier for each blood type. 
For example, if O+ has historically seen 20% more emergency requests than scheduled 
transfusions alone would predict, apply that multiplier to the schedule-based counts. 
Compute a confidence_score for each blood type based on how consistent historical 
patterns have been (low variance = high confidence).

NODE 4 — BEDROCK_INSIGHT_NODE:
Send the structured forecast data (week-by-week counts per blood type, shortages, 
historical multipliers) to Amazon Bedrock Claude Haiku as a structured JSON prompt. 
Ask it to generate: a plain-English summary of the next 30 days demand situation, 
any specific shortage risks to flag to admins, and one recommended action per blood 
type that is under-supplied. The LLM output is stored as agent_summary.

NODE 5 — PERSIST_NODE:
Write the complete forecast result to a new Supabase table called demand_forecasts with 
columns: forecast_id (PK), generated_at, forecast_horizon_days, forecast_json (JSONB 
containing the week-by-week breakdown), shortage_alerts (text array), ai_summary (text), 
blood_type_breakdown (JSONB). Also update a Redis-style key in a simple Supabase table 
called system_cache with key "latest_demand_forecast" and the forecast_id as value, 
so the admin API can fetch it without rerunning the agent.

SCHEDULING:
Register this agent in scheduler/jobs.py to run every day at 6 AM IST via APScheduler. 
Also expose a manual trigger endpoint POST /api/admin/forecast/run that runs it as a 
background task.

ADD API ENDPOINT in api/admin.py:
GET /api/admin/forecast — returns the most recent demand_forecast row as JSON, 
including the AI summary and week-by-week breakdown ready for the frontend chart.

EXPECTED OUTCOME:
- Demand forecast available in admin panel updated daily
- Admin can see "next week: 8 units O+, 3 units A+, 2 units B-" style breakdown
- AI-generated shortage alerts sent to staff via ntfy.sh if any week shows deficit
```

---

## Prompt A4 — Churn Model Retraining Automation

```
CONTEXT:
BloodBridge AI has a churn prediction model at ml/churn_predictor.py that loads a 
static file ml/models/churn_model.joblib. The model was trained on synthetic data. 
Now that real BWF data is seeded into Supabase, the model must be retrained on real 
features and automated to retrain monthly.

TASK 1 — RETRAIN ON BWF FEATURES:
In ml/train_churn.py, rewrite the feature extraction to pull training data from 
Supabase donors table using these features (all now populated from BWF seed):
- calls_to_donations_ratio (primary feature — strongest signal from BWF data)
- donation_count (donations_till_date from BWF)
- response_rate (derive from blood_chains: confirmed / alerted ratio per donor)
- days_since_donation (compute from last_donation_date)
- is_one_time_donor (boolean: donor_type = "One-Time Donor")
- has_active_bridge (boolean: has any IN_CHAIN edge in Neo4j)
- total_calls (from BWF total_calls field stored in donor notes)

Label: is_active field (False = churned, True = active) — this matches BWF's 
user_donation_active_status.

Train XGBoost with these hyperparameters tuned for class imbalance 
(roughly 40% inactive in BWF data): use scale_pos_weight = ratio of inactive to active. 
Save the new model atomically: write to churn_model_new.joblib first, then rename to 
churn_model.joblib only if validation AUC exceeds 0.70. Log the AUC, precision, 
recall to Supabase in a new table called ml_model_logs.

TASK 2 — CHURN RISK TIERS:
Update ml/churn_predictor.py to output four risk tiers based on the BWF inactive_trigger 
patterns observed:
- Score 0.0–0.3 → LOW (active, consistent donor)  
- Score 0.3–0.6 → MEDIUM (watch, recent engagement drop)
- Score 0.6–0.8 → HIGH (matches "Not donated in last 1 year" pattern)
- Score 0.8–1.0 → CRITICAL (matches "Very limited activity despite multiple calls" pattern)

Each tier gets a different outreach intervention strategy stored in the tier definition: 
LOW = no action, MEDIUM = send impact story, HIGH = send badge challenge, 
CRITICAL = trigger AI voice call.

TASK 3 — MONTHLY AUTOMATION:
In scheduler/jobs.py, add an APScheduler cron job that runs on the 1st of each month 
at 2 AM IST. The job calls train_churn.py main function, then immediately runs 
churn_predictor.py in batch mode to update all donor churn_scores in Supabase.

Also wire the existing POST /api/models/retrain endpoint to trigger this job on demand 
for the hackathon demo.

EXPECTED OUTCOME:
- Churn model trained on real BWF data with 7 meaningful features
- Four actionable risk tiers that map to specific outreach responses
- Monthly retraining runs automatically without manual intervention
- Admin panel model metrics card shows real AUC instead of placeholder values
```

---

## Prompt B3 — Voice Agent Hardening

```
CONTEXT:
BloodBridge AI has a voice agent in agents/voice.py that places AI voice calls via 
Bolna.ai. The outbound call works, but two critical gaps exist: there is no fallback 
when the call goes unanswered or the webhook payload is lost, and the Bolna.ai agent 
dashboard configuration for the BloodBridge use case has never been specified.

TASK 1 — SMS FALLBACK AFTER FAILED VOICE:
In agents/voice.py, after placing the Bolna.ai call, store the call_id and donor_id 
in a Supabase table called voice_call_attempts with columns: attempt_id, donor_id, 
request_id, call_id (from Bolna), initiated_at, status (PLACED/ANSWERED/UNANSWERED/FAILED), 
attempts_count.

In scheduler/jobs.py, add a 15-minute interval job that queries voice_call_attempts 
for calls where status is still PLACED (meaning no webhook callback arrived) and 
initiated_at is more than 12 minutes ago. For these stuck calls: increment attempts_count. 
If attempts_count equals 2, trigger services/sms_service.py to send a Twilio SMS 
to the donor's phone number with the blood request details and a YES/NO reply instruction. 
Mark status as FALLBACK_SMS_SENT.

TASK 2 — WEBHOOK RETRY RESILIENCE:
In api/webhooks.py, the Bolna webhook handler must become idempotent. Before processing 
any incoming call result: check if call_id already exists in voice_call_attempts with 
status ANSWERED or UNANSWERED. If yes, return 200 OK immediately without reprocessing. 
If the payload signature verification fails (BOLNA_WEBHOOK_SECRET HMAC check), return 
403 and log the event — do not raise an exception.

TASK 3 — BOLNA AGENT SPECIFICATION DOCUMENT:
Create a file BOLNA_AGENT_CONFIG.md in the project root that specifies exactly how to 
configure the Bolna.ai agent dashboard for this use case:
- Agent name: BloodBridge Emergency Coordinator
- Voice: Sarvam AI Hindi female voice (specify the exact Sarvam model name for Bolna)
- Call intro: a 2-sentence opener in Hindi explaining who is calling and why
- Tool: a YES/NO structured capture that fires the webhook on donor response
- TRAI compliance: allowed calling hours 8 AM to 9 PM IST — specify how to set this 
  in Bolna's schedule field
- Fallback: if no response in 20 seconds, disconnect and trigger SMS

EXPECTED OUTCOME:
- No donor ever gets stuck in limbo after an unanswered call
- SMS reaches donor within 15 minutes of a failed voice attempt
- Bolna dashboard can be configured by any team member reading the spec doc
```

---

## Prompt B4 — AI Feedback Loop (Donor Response → Outreach Tone)

```
CONTEXT:
BloodBridge AI stores donor interactions in the donor_memory table with fields: 
tone_profile, emotional_anchors, last_response_time_secs, preferred_language. 
The planner agent (agents/planner.py) reads donor_memory to personalize outreach. 
However, nothing currently writes back to donor_memory after a donor responds — 
the loop is open. This prompt closes it.

TASK 1 — RESPONSE SIGNAL CAPTURE:
In api/webhooks.py (Telegram webhook handler) and in agents/monitor.py (chain monitor), 
after a donor confirms or declines, extract these signals:
- response_time_seconds: time from alerted_at to confirmed_at/declined_at in blood_chains
- response_outcome: CONFIRMED or DECLINED  
- response_channel: TELEGRAM or VOICE or SMS
- message_text: the donor's actual reply message (if Telegram)
- time_of_day: morning/afternoon/evening bucket based on response timestamp IST

TASK 2 — BEDROCK ANALYSIS:
Create a new service function in services/donor_memory.py called analyze_response_and_update(). 
This function takes the response signals above and makes a single Amazon Bedrock Claude 
Haiku call with a structured prompt: given this donor's current tone_profile and 
emotional_anchors, and given that they just responded with these signals, suggest an 
updated tone_profile (warm/urgent/factual/inspirational), any new emotional_anchor to 
add (e.g., if donor replied quickly on Tuesday mornings, add "responsive_tuesday_morning"), 
and the optimal_contact_window (morning/afternoon/evening) based on their response 
time_of_day history.

The Bedrock response must be parsed as JSON. Update the donor_memory row with the new 
tone_profile and add to emotional_anchors array only if the new anchor is not already 
present.

TASK 3 — WIRE INTO PIPELINE:
Call analyze_response_and_update() at the end of the outcome node (agents/outcome.py) 
for every donor in the completed chain — both confirmed and declined donors. Declined 
donor feedback is equally valuable: if a donor declines on voice but responds on 
Telegram, their preferred_channel should update to TELEGRAM.

Also update the churn model's donor features table in Supabase: after each response, 
recalculate response_rate for that donor (confirmed / total alerted in last 90 days) 
and write it back to the donors table. This keeps the churn model inputs fresh.

EXPECTED OUTCOME:
- After 3 pipeline runs, each donor's tone_profile reflects their actual response behavior
- Planner agent selects better channels and tones on subsequent outreach
- Response rate field in Supabase stays accurate without manual data entry
- Churn scores update within hours of a donor interaction rather than monthly only
```

---

# Phase 3 — Frontend + Integration (Hour 3)

---

## Prompt A5 — Demand Forecast Chart in Admin Panel

```
CONTEXT:
Admin.tsx in the frontend has a health dashboard, traces viewer, staff management, 
and model metrics. A new section must be added showing the weekly blood demand forecast 
generated by the new demand_forecast_agent. The section should be additive — no 
existing Admin.tsx components should be modified.

TASK 1 — API HOOK:
Create a new React Query hook called useDemandForecast in lib/api.ts that calls 
GET /api/admin/forecast. The response contains: generated_at timestamp, ai_summary 
string, forecast_by_week array of objects {week_label, blood_type_counts: {A+: 3, O+: 8 ...}}, 
shortage_alerts string array.

TASK 2 — GROUPED BAR CHART:
In dashboard/Admin.tsx, after the existing model metrics card, add a new section 
called "Blood Demand Forecast — Next 30 Days". Render a Recharts BarChart with 
grouped bars: X-axis is the 4 week labels, each group has one bar per blood type 
(A+, A-, B+, B-, AB+, AB-, O+, O-), each blood type has a distinct color from the 
Tailwind palette. Use a custom legend showing blood type → color mapping.

TASK 3 — AI SUMMARY CARD:
Above the chart, add a card showing the ai_summary text from the forecast response. 
Style it like the existing trace cards: left border accent, expandable. Show the 
generated_at timestamp in relative format ("updated 3 hours ago").

TASK 4 — SHORTAGE ALERT BANNERS:
If shortage_alerts array is non-empty, render one banner per alert above the chart. 
Use the existing shadcn/ui Alert component with destructive variant. Each banner shows 
the shortage text and a "Trigger Outreach" button that calls the existing 
POST /api/emergencies endpoint pre-filled with the flagged blood type.

TASK 5 — LOADING STATE:
While the useDemandForecast hook is loading, show a skeleton matching the chart's 
approximate height and the summary card's height. Use the same skeleton pattern 
already used elsewhere in the Admin panel.

EXPECTED OUTCOME:
- Admin can see "O+ needed: 8 units in week 2" at a glance
- AI summary explains the demand situation in plain English
- Shortage alerts are actionable — one click triggers the matching pipeline
```

---

## Prompt A6 — Production Build Configuration

```
CONTEXT:
BloodBridge AI frontend runs in development mode (node node_modules\vite\bin\vite.js). 
The backend has test tokens hardcoded in several places. Before AWS deployment, 
both must be cleaned up.

TASK 1 — VITE PRODUCTION CONFIG:
In BloodBridge_AI_frontend/artifacts/bloodbridge/vite.config.ts, add a production 
build configuration. The API proxy (from /api → http://localhost:8000) must only 
apply in development mode. In production, VITE_API_URL environment variable should 
be the AWS EC2 backend URL. Add a define block that replaces import.meta.env.VITE_API_URL 
at build time.

Create a .env.production file (gitignored) with placeholder: VITE_API_URL=https://your-ec2-url-here

In lib/api.ts, ensure every fetch call uses import.meta.env.VITE_API_URL as the base 
URL prefix, not hardcoded localhost.

TASK 2 — REMOVE TEST TOKENS:
Search the entire frontend codebase for VITE_STAFF_TOKEN usage. Currently some 
components may use a hardcoded fallback staff token for development. Remove any 
hardcoded token strings. The app must only use the JWT stored in localStorage after 
a real login via POST /api/auth/login. Any component that was bypassing auth with 
a hardcoded token should redirect to the /login page instead.

TASK 3 — BACKEND ENV CLEANUP:
In core/config.py, add a strict validation: if APP_ENV is "production", raise a 
startup error if DEMO_MOCK_MODE is True, if CORS allows_origins contains "*", 
or if any password field is the literal string "password" or "admin". This prevents 
accidentally deploying with development defaults.

In main.py, make CORS allow_origins read from a comma-separated env variable 
ALLOWED_ORIGINS rather than the hardcoded wildcard. In development it defaults to "*", 
in production it must be set explicitly to the CloudFront distribution URL.

TASK 4 — PACKAGE.JSON BUILD SCRIPT:
In package.json, ensure the build script runs: pnpm run build. Verify output goes to 
the dist/ directory. Add a preview script that serves dist/ locally on port 4173 for 
smoke testing before S3 upload.

EXPECTED OUTCOME:
- pnpm build completes without errors and produces dist/ folder
- No hardcoded tokens, localhost URLs, or test credentials in production build
- Backend refuses to start in production mode if insecure defaults are detected
```

---

## Prompt B5 — Framer Motion Animations (Additive Only)

```
CONTEXT:
BloodBridge AI frontend uses Framer Motion (already installed). The donor portal and 
emergency dashboard need animation improvements. The rule is strictly additive: 
wrap existing components in motion wrappers, do not change any existing component's 
internal structure or logic.

TASK 1 — DONOR PORTAL BADGE GRID (DonorPortal.tsx):
Find the grid where badges are rendered. Wrap the entire grid container in a 
motion.div with variants: container variant that staggers children with 
staggerChildren: 0.07, delayChildren: 0.1. Wrap each individual badge card in a 
motion.div with item variant: hidden = {opacity: 0, scale: 0.8, y: 20}, 
visible = {opacity: 1, scale: 1, y: 0} with spring transition type, stiffness 200, 
damping 15. For locked badges, the scale on visible should be 0.95 to visually 
distinguish them.

TASK 2 — LIVES SAVED COUNTER (DonorPortal.tsx):
Find the element showing the lives_saved count. Wrap it in a motion.span. 
When the lives_saved value changes (useEffect dependency), trigger a keyframe 
animation: y from -16 to 0, opacity from 0 to 1, over 0.4 seconds ease-out. 
This makes the number appear to "tick up" when the donor page loads or when 
the value updates via React Query refetch.

TASK 3 — CHAIN NODE STATUS TRANSITIONS (Emergency.tsx):
Find the 8-node chain timeline dot grid. Each dot has a background color that 
reflects chain status (pending/alerted/confirmed/declined). Instead of instant 
color changes (which currently happen via conditional Tailwind classes), use 
motion.div with animate prop that smoothly transitions backgroundColor over 0.4s. 
The color values for each status are: pending → gray, alerted → orange, 
confirmed → green, declined → red. Keep the existing status-to-color logic unchanged, 
only add the animate wrapper around it.

TASK 4 — NEO4J GRAPH PAGE ENTRANCE (Graph.tsx):
The force-graph component loads and then the graph appears abruptly. Wrap the entire 
graph container in a motion.div with initial={opacity: 0} and animate={opacity: 1} 
with a 0.6 second ease transition. Add a loading state: while data is being fetched, 
show a pulsing motion.div placeholder the same size as the graph area using 
animate={opacity: [0.3, 0.7, 0.3]} with repeat: Infinity and duration: 1.5.

TASK 5 — AVAILABILITY TOGGLE (DonorPortal.tsx):
The availability toggle button currently has no feedback animation. After the API 
call to POST /api/donors/{id}/availability completes, trigger a brief motion.div 
animation on the button: scale 1 → 1.08 → 1 over 0.3 seconds. If the toggle 
turns the donor active, also briefly animate the lives_saved section to draw 
the donor's eye to their impact area.

EXPECTED OUTCOME:
- Badge grid staggers in like a card deck on first load
- Number counters feel alive when values change
- Chain node status changes are smooth and satisfying to watch during demo
- No existing component logic, state, or API calls are modified
```

---

## Prompt B6 — Supabase RLS Hardening

```
CONTEXT:
BloodBridge AI uses Supabase PostgreSQL with Row Level Security enabled, but three 
sensitive tables have permissive policies: consent_records, donor_memory, and 
donor_verifications. The backend uses two Supabase clients: one with the anon key 
(for public-facing operations) and one with the service_role key (for backend-only 
operations). The fix is to lock down these tables so only the service_role key 
can access them, and add owner-only policies for the other donor tables.

TASK 1 — consent_records TABLE:
Write the SQL policy changes for consent_records. The existing permissive policy 
should be replaced with: SELECT and INSERT allowed only to service_role. No anon 
access at all. This table is never read by the frontend directly — it's only written 
by consent_service.py using the service role client.

TASK 2 — donor_memory TABLE:
For donor_memory: SELECT allowed to the donor who owns the record 
(where donor_id matches auth.uid() if using Supabase Auth, or service_role). 
UPDATE allowed only to service_role. No INSERT from anon. 
The donor portal reads donor memory data via the backend API (which uses service_role) 
not by querying Supabase directly from the browser.

TASK 3 — donor_verifications TABLE:
For donor_verifications: all operations restricted to service_role only. 
No row in this table should be readable or writable by any frontend client.

TASK 4 — donors TABLE:
For the donors table: SELECT allowed to anon for non-sensitive fields 
(name, blood_type, city, is_active, donation_count). Columns like phone, lat, lng, 
churn_score, medical_hold must be excluded from anon reads via a Postgres view 
called donors_public that selects only the safe columns. Update any frontend 
API calls that fetch donor lists to use this view.

TASK 5 — JWT SECRET:
In core/security.py, the JWT signing currently uses SUPABASE_SERVICE_KEY as the 
secret. Create a new environment variable JWT_SECRET (a 64-character random string) 
and use that exclusively for JWT signing and verification. Add JWT_SECRET to 
.env.example. The Supabase service key should only be used for Supabase client 
instantiation, never as a cryptographic secret.

TASK 6 — DOCUMENT:
Add a file SECURITY.md listing all RLS policies, which tables are service_role-only, 
and instructions for rotating the JWT_SECRET. This is needed for the hackathon 
responsible AI requirement.

EXPECTED OUTCOME:
- No sensitive donor data (phone, location, churn score) accessible from browser 
  without going through the authenticated backend
- DPDP 2023 compliance strengthened: consent data only accessible by service role
- JWT tokens signed with a dedicated secret independent of Supabase credentials
```

---

# Phase 4 — AWS Deployment (Hour 4)

---

## Prompt A7 — Dockerize Backend + EC2 Deployment

```
CONTEXT:
BloodBridge AI backend is a FastAPI + Uvicorn application running locally. 
It needs to be containerized and deployed to AWS EC2 so Telegram webhooks, 
Bolna.ai webhooks, and the frontend can reach it over HTTPS. The existing 
deployment target was Render.com — this is being replaced with AWS.

TASK 1 — DOCKERFILE:
Create a Dockerfile at the root of BloodBridge_AI_Backend/. 

Specification:
- Base image: python:3.11-slim (not alpine — some ML dependencies need glibc)
- Working directory: /app
- Copy requirements.txt first (for layer caching), run pip install with --no-cache-dir
- Copy the entire application directory
- Expose port 8000
- Startup command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

Add a .dockerignore that excludes: .env, venv/, __pycache__, *.pyc, .git, 
ml/models/*.joblib (models will be downloaded from S3 on startup), tests/

TASK 2 — S3 MODEL STORAGE:
Modify ml/antigen_scorer.py, ml/urgency_scorer.py, ml/churn_predictor.py to load 
their joblib files from an S3 bucket on cold start if the local path doesn't exist. 
Create a helper function in ml/__init__.py called load_model_from_s3(bucket, key, 
local_path) that uses boto3 to download the file to /tmp/models/ if not cached. 
This means model files don't need to be in the Docker image — they're pulled from 
S3 bucket named "bloodbridge-models" on first request.

TASK 3 — EC2 SETUP INSTRUCTIONS:
Create a file AWS_DEPLOY.md with step-by-step instructions:
1. Launch EC2 t3.micro (Amazon Linux 2023), open ports 22, 80, 443, 8000
2. Install Docker on the instance (Amazon Linux 2023 commands)
3. Create ECR repository called bloodbridge-backend
4. Build image locally: docker build -t bloodbridge-backend .
5. Tag and push to ECR using the aws ecr get-login-password flow
6. Pull and run on EC2 with all environment variables passed via --env-file
7. Install nginx, configure reverse proxy: port 80/443 → localhost:8000
8. Install Certbot, obtain Let's Encrypt cert for the EC2 domain
9. Set ALLOWED_ORIGINS in .env to the CloudFront distribution URL

TASK 4 — HEALTH CHECK ENDPOINT HARDENING:
The existing GET /health endpoint checks 5 services. For AWS deployment, add an 
additional check that verifies: AWS Bedrock reachability (test call to list_models), 
S3 bucket accessibility (list_objects on bloodbridge-models), Comprehend endpoint 
reachability. Return HTTP 200 only if all services pass. AWS load balancer health 
checks need a reliable 200 response.

EXPECTED OUTCOME:
- docker build produces a working image
- Image runs on EC2 t3.micro with all 40+ API endpoints accessible
- HTTPS terminates at nginx, Telegram and Bolna webhooks work at public URL
- ML models load from S3 on first request, cached locally after
```

---

## Prompt A8 — Telegram Webhook Re-registration + nginx HTTPS

```
CONTEXT:
After EC2 deployment, the Telegram bot's webhook URL needs to be updated from the 
ngrok development URL to the permanent EC2/nginx HTTPS URL. The bot currently 
requires a manual ngrok startup — this automates it for production.

TASK 1 — WEBHOOK REGISTRATION SCRIPT:
Create a script setup_webhook.py at the project root that:
1. Reads TELEGRAM_BOT_TOKEN and APP_BASE_URL from environment
2. Calls the Telegram Bot API setWebhook endpoint with 
   url = APP_BASE_URL + "/webhook/telegram"
3. Passes the TELEGRAM_WEBHOOK_SECRET as the secret_token parameter
4. Calls getWebhookInfo to verify registration succeeded
5. Prints the confirmed webhook URL, pending_update_count, and last_error_message

TASK 2 — NGINX CONFIG:
Create nginx/bloodbridge.conf. It should:
- Listen on port 80, redirect all HTTP → HTTPS
- Listen on port 443 with SSL cert paths from Certbot 
  (/etc/letsencrypt/live/your-domain/)
- Proxy all requests to 127.0.0.1:8000 with proper headers: 
  X-Real-IP, X-Forwarded-For, X-Forwarded-Proto, Host
- Set client_max_body_size 10m (for blood card photo uploads via Telegram)
- Set proxy_read_timeout 120s (LangGraph pipeline can take up to 60s)
- Add gzip compression for application/json responses

TASK 3 — STARTUP AUTOMATION:
Create a systemd service file bloodbridge.service that:
- Runs the Docker container on EC2 startup
- Passes the env file location
- Restarts on failure with 5-second delay
- After 10 seconds, calls setup_webhook.py to re-register the Telegram webhook

This ensures that after any server restart, the bot is automatically reconnected 
without manual intervention.

EXPECTED OUTCOME:
- After running setup_webhook.py once, Telegram delivers messages to EC2
- nginx handles HTTPS termination cleanly
- Server restart automatically re-registers webhook within 15 seconds
```

---

## Prompt B7 — Frontend S3 + CloudFront Deployment

```
CONTEXT:
The BloodBridge AI frontend is a React + Vite SPA. After pnpm build produces a 
dist/ folder, it needs to be hosted on AWS S3 with CloudFront as the CDN, so the 
frontend is accessible over HTTPS with fast global delivery.

TASK 1 — S3 BUCKET SETUP INSTRUCTIONS:
Add to AWS_DEPLOY.md a frontend section:
1. Create S3 bucket named bloodbridge-frontend, region ap-south-1
2. Disable Block Public Access (required for static website hosting)
3. Enable Static Website Hosting: index document = index.html, error document = index.html 
   (the error document must also be index.html for React Router client-side routing to work)
4. Bucket policy to allow s3:GetObject from * (public read)
5. Upload command: aws s3 sync dist/ s3://bloodbridge-frontend --delete
   The --delete flag removes files from S3 that no longer exist in dist/

TASK 2 — CLOUDFRONT DISTRIBUTION:
6. Create CloudFront distribution: origin = S3 website endpoint (not S3 REST endpoint — 
   this distinction matters for SPA routing)
7. Default root object = index.html
8. Create a Custom Error Response: HTTP 403 → response page /index.html, 
   response code 200 (this handles React Router deep links)
9. Price class: PriceClass_100 (US, Europe, Asia — covers India via Singapore PoP)
10. Enable compression (gzip + Brotli)

TASK 3 — ENVIRONMENT VARIABLE INJECTION:
Before running pnpm build, the CI/deployment process must set VITE_API_URL to the 
EC2 backend HTTPS URL. Create a deploy.sh script that:
1. Reads EC2_BACKEND_URL from the shell environment
2. Writes VITE_API_URL=$EC2_BACKEND_URL to .env.production
3. Runs pnpm build
4. Syncs dist/ to S3
5. Creates a CloudFront invalidation for /* to bust CDN cache

TASK 4 — CORS ALIGNMENT:
After CloudFront is created, the distribution URL (e.g. https://xxxx.cloudfront.net) 
must be added to the backend's ALLOWED_ORIGINS env variable. Update the backend 
.env on EC2 and restart the Docker container. Verify by checking that 
GET /health returns 200 when called from the CloudFront URL.

EXPECTED OUTCOME:
- Frontend accessible at the CloudFront URL over HTTPS
- React Router deep links work correctly (no 403 on refresh)
- New deploys: run deploy.sh, CloudFront cache clears within 60 seconds
- Backend CORS accepts requests only from the CloudFront distribution
```

---

## Prompt B8 — Final Smoke Test Checklist

```
CONTEXT:
Both backend (EC2) and frontend (CloudFront) are deployed. Before the hackathon 
demo, every major flow must be verified end-to-end. This prompt defines the 
complete smoke test checklist to run in sequence.

TASK — CREATE FILE: SMOKE_TEST.md

The file must contain a numbered checklist that can be executed by one person 
in 15 minutes. Structure it in 5 sections:

SECTION 1 — INFRASTRUCTURE (5 checks):
1. curl https://your-ec2-url/health → verify all 9 services return "ok" including 
   Bedrock, Comprehend, Neo4j, Supabase, S3
2. Open CloudFront URL in browser → landing page loads, no console errors
3. Open /dashboard/graph → Neo4j graph renders with real Hyderabad donor nodes
4. Open /dashboard/map → Leaflet map shows Hyderabad blood banks
5. WebSocket test: open browser devtools Network tab, navigate to /dashboard/emergency, 
   confirm ws:// connection establishes within 3 seconds

SECTION 2 — AUTHENTICATION (4 checks):
6. POST /api/auth/signup → create a test donor account
7. POST /api/donor/login → login with test account, receive JWT
8. POST /api/auth/login → login as staff, confirm /dashboard/emergency accessible
9. Verify that accessing /dashboard/admin without staff JWT returns 401

SECTION 3 — CORE PIPELINE (6 checks):
10. POST /api/emergencies with a test patient_id → pipeline triggers as background task
11. GET /api/emergencies/{id}/trace after 30 seconds → verify all 14 agent nodes 
    appear in trace with non-zero duration_ms
12. GET /api/emergencies/{id}/chain → confirm 8 donor chain built from seeded data
13. Telegram bot: send /start to the bot → receive consent message
14. Telegram bot: send a natural language message "am I eligible to donate?" → 
    receive eligibility check response (Bedrock tool-calling confirmed working)
15. GET /api/admin/forecast → demand forecast returns ai_summary and weekly breakdown

SECTION 4 — ML MODELS (3 checks):
16. GET /api/donors?sort_by=churn_score → donors sorted by churn, highest first, 
    values between 0 and 1
17. POST /api/models/retrain → returns 202 Accepted, check logs for retraining job
18. GET /api/donors/{id}/eligibility → returns eligibility based on real 
    next_eligible_date from seeded BWF data

SECTION 5 — DEMO SEQUENCE (3 checks):
19. Click "New Emergency" button on dashboard → watch chain nodes animate through 
    orange (alerted) states in real time via WebSocket
20. Check donor portal badges page → badge cards stagger-animate in correctly
21. Open Admin panel forecast chart → weekly blood demand bars render, 
    AI summary card shows text

FINAL INSTRUCTION IN THE FILE:
If any check fails, document the endpoint, error message, and timestamp. 
Do not proceed to demo until all 21 checks pass.

EXPECTED OUTCOME:
- Structured test document that any team member can run
- All 21 checks are executable with browser + curl alone
- Demo sequence (checks 19-21) are the visual highlights for judges
```

---

**Quick reference for running prompts with Antigravity:**

Give Prompt A1 and B1 simultaneously — they touch different files. Give A2 only after A1 completes (Neo4j seed needs Bedrock config). Give B3 only after B1 completes (voice fallback references the Telegram-confirmed donor state). Phase 4 prompts (A7, A8, B7) can only start after Phase 3 production build (A6) is verified locally first.