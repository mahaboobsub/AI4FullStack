# BloodBridge AI — Final Smoke Test Checklist (B8)

> **Time**: ~15 minutes | **Tools**: Browser + curl + Telegram app  
> **Prerequisite**: Backend (EC2) + Frontend (CloudFront) deployed  
> Log endpoint + error + timestamp for any failure. Do NOT demo until all checks pass.

---

## SECTION 1 — INFRASTRUCTURE (3 min)

- [ ] **1.1** `curl $API_URL/api/health` → 200, all services "online" (incl. Bedrock, Comprehend, S3, Neo4j, Supabase)
- [ ] **1.2** Frontend landing page loads at CloudFront URL (no 403/blank)
- [ ] **1.3** `/dashboard/graph` shows real Hyderabad bridge network (nodes + links render)
- [ ] **1.4** `/dashboard/map` shows blood banks with markers
- [ ] **1.5** WebSocket connects < 3 seconds (check browser DevTools → Network → WS)

## SECTION 2 — AUTH (2 min)

- [ ] **2.1** Sign up test donor → profile created in Supabase
- [ ] **2.2** Donor login → JWT returned in response
- [ ] **2.3** Staff login → admin dashboard reachable
- [ ] **2.4** Admin endpoint without JWT → 401 Unauthorized

## SECTION 3 — CORE PIPELINE (5 min)

- [ ] **3.1** `POST /api/emergency/outreach` with valid patient → pipeline runs
- [ ] **3.2** Agent trace shows all nodes with non-zero ms
- [ ] **3.3** Blood chain built from seeded bridge donors (≥ 1 donor in chain)
- [ ] **3.4** Telegram `/start` → DPDP consent message with Yes/No buttons
- [ ] **3.5** Natural language "which patient do I support?" → bridge answer (Bedrock tool-calling confirmed)
- [ ] **3.6** Natural language "am I eligible?" → eligibility check with next_eligible_date
- [ ] **3.7** `GET /api/admin/forecast` → AI summary + weekly breakdown + supply gap
- [ ] **3.8** `POST /api/admin/forecast/run` → 202 accepted (background trigger)
- [ ] **3.9** `GET /api/admin/optimize-assignments` → optimal assignment preview (if active requests)

## SECTION 4 — ML & MATCHING (3 min)

- [ ] **4.1** Donors sorted by churn_score (0–1, real values, not all 0.5)
- [ ] **4.2** `POST /api/models/retrain` → 202 + job ID in response
- [ ] **4.3** Eligibility check uses real next_eligible_date + 56-day rule
- [ ] **4.4** Matching returns donors with ring (1/2/3) and match_score fields
- [ ] **4.5** `POST /api/donors/{id}/health-status` with available=false → medical_hold set

## SECTION 5 — DEMO HIGHLIGHTS (2 min)

- [ ] **5.1** Trigger outreach → chain dots animate orange→green live via WebSocket
- [ ] **5.2** Donor badges grid renders with stagger animation (if Framer Motion applied)
- [ ] **5.3** Admin forecast chart renders demand vs supply with AI summary card
- [ ] **5.4** Location APIs work: `POST /api/patients/{id}/locations` adds geohashed location
- [ ] **5.5** Chain cards show ring + match_score for transparency

---

## Pass Criteria

| Result | Action |
|--------|--------|
| All checks pass ✅ | Proceed to demo |
| 1-2 minor failures | Document, proceed with known issues noted |
| Any Section 1/3 failure | **STOP** — fix before demo |

## Quick Debug Commands

```bash
# Check backend logs
docker logs bloodbridge --tail 100

# Check container status
docker ps

# Re-register Telegram webhook
python setup_webhook.py

# Force restart
docker restart bloodbridge

# Check Supabase data
curl -s $API_URL/api/donors | python -m json.tool | head -20
```
