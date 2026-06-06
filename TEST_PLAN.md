# BloodBridge AI — Comprehensive Test Plan

## Endpoint Connectivity Audit (47 Frontend → Backend Connections)

All frontend API functions in `lib/api.ts` map 1:1 to backend FastAPI routes. **0 broken endpoints.**

| # | Frontend Function | Backend Route | Method | Status |
|---|---|---|---|---|
| 1 | `getActiveEmergencies()` | `/api/emergencies` | GET | ✅ |
| 2 | `getChainStatus(id)` | `/api/emergencies/{id}/chain` | GET | ✅ |
| 3 | `getEmergencyTrace(id)` | `/api/emergencies/{id}/trace` | GET | ✅ |
| 4 | `triggerEmergency(data)` | `/api/emergencies` | POST | ✅ |
| 5 | `confirmOutcome(id)` | `/api/emergencies/{id}/confirm` | POST | ✅ |
| 6 | `getDonors()` | `/api/donors` | GET | ✅ |
| 7 | `getDonor(id)` | `/api/donors/{id}` | GET | ✅ |
| 8 | `getDonorByLookup(params)` | `/api/donors/lookup` | GET | ✅ |
| 9 | `getDonorImpactStories(id)` | `/api/donors/{id}/memory` | GET | ✅ |
| 10 | `getDonorRank(id)` | `/api/donors/{id}/rank` | GET | ✅ |
| 11 | `getDonorActiveRequest(id)` | `/api/donors/{id}/active-request` | GET | ✅ |
| 12 | `getDonorEligibility(id)` | `/api/donors/{id}/eligibility` | GET | ✅ |
| 13 | `getConsentSummary(id)` | `/api/donors/{id}/consent` | GET | ✅ |
| 14 | `getLeaderboard(city)` | `/api/donors/leaderboard` | GET | ✅ |
| 15 | `getGraphData(requestId)` | `/api/donors/graph/data` | GET | ✅ |
| 16 | `getDonorLocations(id)` | `/api/donors/{id}/locations` | GET | ✅ |
| 17 | `setDonorAvailability(id)` | `/api/donors/{id}/availability` | POST | ✅ |
| 18 | `triggerVoiceCall(id)` | `/api/donors/{id}/voice` | POST | ✅ |
| 19 | `triggerOutreach(id)` | `/api/donors/{id}/outreach` | POST | ✅ |
| 20 | `revokeConsent(id, type)` | `/api/donors/{id}/consent/revoke` | POST | ✅ |
| 21 | `exportDonorData(id)` | `/api/donors/{id}/my-data` | GET | ✅ |
| 22 | `eraseDonorData(id)` | `/api/donors/{id}/data` | DELETE | ✅ |
| 23 | `updateDonorHealthStatus(id)` | `/api/donors/{id}/health-status` | POST | ✅ |
| 24 | `addDonorLocation(id, loc)` | `/api/donors/{id}/locations` | POST | ✅ |
| 25 | `deleteDonorLocation(id, lid)` | `/api/donors/{id}/locations/{lid}` | DELETE | ✅ |
| 26 | `setDonorPrimaryLocation(id)` | `/api/donors/{id}/locations/{lid}` | PATCH | ✅ |
| 27 | `uploadBloodCard(file)` | `/api/donors/upload-card` | POST | ✅ |
| 28 | `getBloodStock(city)` | `/api/blood-banks` | GET | ✅ |
| 29 | `refreshBloodBanks()` | `/api/blood-banks/refresh` | POST | ✅ |
| 30 | `getPatientProfile(id)` | `/api/patients/{id}` | GET | ✅ |
| 31 | `getPatientSchedule(id)` | `/api/patients/{id}/schedule` | GET | ✅ |
| 32 | `getPatientChainHistory(id)` | `/api/patients/{id}/chain-history` | GET | ✅ |
| 33 | `getPatientLocations(id)` | `/api/patients/{id}/locations` | GET | ✅ |
| 34 | `addPatientLocation(id, loc)` | `/api/patients/{id}/locations` | POST | ✅ |
| 35 | `deletePatientLocation(id, lid)` | `/api/patients/{id}/locations/{lid}` | DELETE | ✅ |
| 36 | `setPatientPrimaryLocation(id)` | `/api/patients/{id}/locations/{lid}` | PATCH | ✅ |
| 37 | `triggerAutoSchedule(id)` | `/api/patients/{id}/auto-schedule` | POST | ✅ |
| 38 | `getSystemHealth()` | `/api/health` | GET | ✅ |
| 39 | `getAgentTraces()` | `/api/admin/traces` | GET | ✅ |
| 40 | `getAnalytics()` | `/api/admin/analytics` | GET | ✅ |
| 41 | `getAgentConfig()` | `/api/admin/config` | GET | ✅ |
| 42 | `updateAgentConfig(config)` | `/api/admin/config` | POST | ✅ |
| 43 | `retrainModels()` | `/api/admin/retrain` | POST | ✅ |
| 44 | `getStaffMembers()` | `/api/admin/staff` | GET | ✅ |
| 45 | `addStaffMember(data)` | `/api/admin/staff` | POST | ✅ |
| 46 | `deleteStaffMember(username)` | `/api/admin/staff/{username}` | DELETE | ✅ |
| 47 | `optimizeAssignments()` | `/api/admin/optimize-assignments` | POST | ✅ |
| 48 | `getDemandForecast()` | `/api/admin/forecast` | GET | ✅ |
| 49 | `runDemandForecast()` | `/api/admin/forecast/run` | POST | ✅ |
| 50 | `getScheduleEntries()` | `/api/schedule` | GET | ✅ |
| 51 | `login(identifier, password)` | `/api/auth/login` | POST | ✅ |
| 52 | `signup(data)` | `/api/auth/signup` | POST | ✅ |
| 53 | `telegramLogin(token)` | `/api/auth/telegram-login` | GET | ✅ |

---

## Frontend Component Rendering Tests

### Test Framework: Vitest + React Testing Library

```
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @testing-library/user-event msw
```

---

### TC-F01: Landing Page
| ID | Test Case | Expected |
|---|---|---|
| F01.1 | Page renders without crash | No console errors, main heading visible |
| F01.2 | CTA buttons link to /signup and /login | href attributes correct |
| F01.3 | Stats section shows "1L+ Patients", "14 AI Agents" | Text present in DOM |

### TC-F02: Login Page
| ID | Test Case | Expected |
|---|---|---|
| F02.1 | Form renders with identifier + password fields | Inputs accessible |
| F02.2 | Submit with valid credentials → stores token in localStorage | localStorage.auth_token set |
| F02.3 | Submit with invalid creds → shows error | Error message visible |
| F02.4 | Eye toggle shows/hides password | Input type toggles text/password |

### TC-F03: SignUp Page
| ID | Test Case | Expected |
|---|---|---|
| F03.1 | Role tabs (Donor/Patient/Staff) switch form fields | Blood Group appears for donor/patient only |
| F03.2 | Card upload triggers OCR endpoint | uploadBloodCard called, result displayed |
| F03.3 | OCR success auto-fills blood group select | Select value matches OCR response |
| F03.4 | Antigen badges display after card scan | Antigen chips visible with +/− |
| F03.5 | Submit redirects to correct login page per role | Donor→/donor/login, Patient→/patient/login |

### TC-F04: DonorPortal
| ID | Test Case | Expected |
|---|---|---|
| F04.1 | Profile card renders with name, blood type, stats | All fields populated from API |
| F04.2 | Badges grid shows unlocked/locked states | Unlocked badges have ✓, locked are greyscale |
| F04.3 | Availability toggle calls setDonorAvailability | API called, button text toggles |
| F04.4 | Active emergency card appears when activeRequest exists | Card shows patient name + urgency |
| F04.5 | Eligibility card shows eligible/not-eligible state | Green or amber background |
| F04.6 | Leaderboard renders top 10 entries for donor's city | Entries with rank, name, badges |
| F04.7 | DPDP consent grid shows consent statuses | granted/revoked badges correct |
| F04.8 | "Export My Data" triggers download | Blob URL created + a.click() |
| F04.9 | "Delete My Account" with confirm → erases data | API called, redirect to / |
| F04.10 | Revoke All Consents → refreshes consent summary | Updated states shown |
| F04.11 | Telegram connection status shows Connected/Not Connected | Based on telegram_chat_id |
| F04.12 | Impact stories display or show placeholder | Stories text or italic message |

### TC-F05: Emergency Dashboard
| ID | Test Case | Expected |
|---|---|---|
| F05.1 | Emergency cards render from WebSocket data | Cards with request_id, patient_id |
| F05.2 | Chain dots animate per status (green/amber/red) | Correct colors per CHAIN_DOT_COLORS |
| F05.3 | "New Emergency" dialog creates emergency | API called, toast success |
| F05.4 | "Mark Resolved" button calls confirmOutcome | Toast success, button disabled during |
| F05.5 | "View AI Agent Trace" opens slide-out drawer | Drawer visible with node list |
| F05.6 | Trace drawer shows node status icons + timing | CheckCircle/AlertTriangle/X per status |
| F05.7 | Chain break alert renders when chainBreak received | Red alert banner visible |
| F05.8 | Stats cards (Active, Alerted, Confirmed, Chain Size) calculate correctly | Numbers match chain data |

### TC-F06: Map View
| ID | Test Case | Expected |
|---|---|---|
| F06.1 | Map renders with Leaflet markers for blood banks | Markers visible on map |
| F06.2 | Blood type filter pills change displayed units | Sorted banks update |
| F06.3 | Refresh button calls refreshBloodBanks + reloads data | Toast "Inventory refreshed" |
| F06.4 | Zero-unit warning appears when a bank has 0 units | Amber alert visible |
| F06.5 | Bank card click highlights with ring | ring-2 ring-teal-500 applied |

### TC-F07: Admin Panel
| ID | Test Case | Expected |
|---|---|---|
| F07.1 | Service health cards render from /api/health | Cards with status badges |
| F07.2 | Agent traces accordion expands with node visualization | Trace nodes visible |
| F07.3 | "Retrain" button triggers progress dialog | Dialog opens, progress bar animates |
| F07.4 | Staff list CRUD (add/delete) works | Staff appears/disappears |
| F07.5 | CSV bulk upload calls /api/donors/bulk-import-csv | Toast with imported/skipped counts |
| F07.6 | Schedule overview lists entries from getScheduleEntries | Patient IDs + dates shown |
| F07.7 | Config editor saves with updateAgentConfig | Toast "Agent config updated" |
| F07.8 | Demand forecast panel renders forecast data | Charts/summaries visible |

### TC-F08: Donors List
| ID | Test Case | Expected |
|---|---|---|
| F08.1 | Table renders all donors from getDonors | Rows with name, blood type, city |
| F08.2 | Sort by churn_score changes order | Highest risk first |
| F08.3 | Voice call button handles INITIATED/QUEUED/ERROR | Correct toast per status |
| F08.4 | Outreach button sends Telegram message | Toast success |

### TC-F09: Patient Dashboard
| ID | Test Case | Expected |
|---|---|---|
| F09.1 | Patient profile renders from getPatientProfile | Name, blood type, hospital shown |
| F09.2 | Schedule table shows entries from getPatientSchedule | Dates + status |
| F09.3 | Chain history accordion shows past emergencies | Donor names, timestamps |
| F09.4 | Location manager CRUD works | Locations appear/disappear |

### TC-F10: Telegram Login Page
| ID | Test Case | Expected |
|---|---|---|
| F10.1 | No token param → shows error state | "No token provided" message |
| F10.2 | Valid token → success state → redirect to /donor | Loading → ✓ → redirect |
| F10.3 | Invalid/expired token → error state | "Login Failed" with message |

### TC-F11: Graph Visualization
| ID | Test Case | Expected |
|---|---|---|
| F11.1 | Force graph renders nodes and links | SVG/Canvas with circles + lines |
| F11.2 | Node click shows donor/patient details | Tooltip or panel appears |

---

## Backend API Tests

### Test Framework: pytest + httpx (async)

```
pip install pytest pytest-asyncio httpx
```

---

### TC-B01: Authentication
| ID | Test Case | Expected |
|---|---|---|
| B01.1 | POST /api/auth/signup with valid donor data | 200, returns success + user |
| B01.2 | POST /api/auth/signup duplicate phone | 400, "already registered" |
| B01.3 | POST /api/auth/login valid credentials | 200, returns access_token |
| B01.4 | POST /api/auth/login invalid password | 401 |
| B01.5 | GET /api/auth/telegram-login?token=valid | 200, returns access_token + donor_id |
| B01.6 | GET /api/auth/telegram-login?token=expired | 401 |

### TC-B02: Donor CRUD
| ID | Test Case | Expected |
|---|---|---|
| B02.1 | GET /api/donors → returns list | 200, array of DonorResponse |
| B02.2 | GET /api/donors/{valid_id} | 200, single donor |
| B02.3 | GET /api/donors/{invalid_id} | 404 |
| B02.4 | GET /api/donors/lookup?phone=+917075899966 | 200, donor found |
| B02.5 | GET /api/donors/lookup (no params) | 400 |
| B02.6 | GET /api/donors/{id}/memory | 200, badges + impact_stories |
| B02.7 | GET /api/donors/{id}/rank | 200, rank + city |
| B02.8 | GET /api/donors/{id}/active-request (no active) | 200, null |
| B02.9 | GET /api/donors/{id}/eligibility | 200, eligible/reason |
| B02.10 | POST /api/donors/{id}/availability | 200, success |

### TC-B03: Emergency Operations
| ID | Test Case | Expected |
|---|---|---|
| B03.1 | GET /api/emergencies → active list | 200, array |
| B03.2 | POST /api/emergencies (valid) | 200, requestId returned |
| B03.3 | POST /api/emergencies (duplicate idempotency key) | 200, same requestId |
| B03.4 | GET /api/emergencies/{id}/chain | 200, ChainNode array |
| B03.5 | GET /api/emergencies/{id}/trace | 200, trace with nodes |
| B03.6 | POST /api/emergencies/{id}/confirm | 200, success |

### TC-B04: Voice & Outreach
| ID | Test Case | Expected |
|---|---|---|
| B04.1 | POST /api/donors/{id}/voice (within TRAI hours) | 200, callSid |
| B04.2 | POST /api/donors/{id}/voice (outside TRAI hours) | 202, queued |
| B04.3 | POST /api/donors/{id}/voice (no phone) | 400 |
| B04.4 | POST /api/donors/{id}/outreach (has telegram) | 200, messageId |
| B04.5 | POST /api/donors/{id}/outreach (no telegram) | 400 |

### TC-B05: DPDP Compliance
| ID | Test Case | Expected |
|---|---|---|
| B05.1 | GET /api/donors/{id}/consent | 200, consents map |
| B05.2 | POST /api/donors/{id}/consent/revoke (type=all) | 200, success |
| B05.3 | POST /api/donors/{id}/consent/revoke (type=invalid) | 400 |
| B05.4 | GET /api/donors/{id}/my-data | 200, full export JSON |
| B05.5 | DELETE /api/donors/{id}/data | 200, data erased |

### TC-B06: Blood Bank & OCR
| ID | Test Case | Expected |
|---|---|---|
| B06.1 | GET /api/blood-banks?city=Hyderabad | 200, array of BloodBank |
| B06.2 | POST /api/blood-banks/refresh | 200, success |
| B06.3 | POST /api/donors/upload-card (valid image) | 200, blood_group + antigens |
| B06.4 | POST /api/donors/upload-card (non-image) | 400 |
| B06.5 | POST /api/donors/upload-card (>10MB) | 400 |

### TC-B07: Admin Endpoints
| ID | Test Case | Expected |
|---|---|---|
| B07.1 | GET /api/health | 200, ServiceHealth array |
| B07.2 | GET /api/admin/traces (with auth) | 200, trace array |
| B07.3 | GET /api/admin/analytics | 200, EngagementMetrics |
| B07.4 | GET /api/admin/config | 200, AgentConfig |
| B07.5 | POST /api/admin/config (update) | 200, success |
| B07.6 | POST /api/admin/retrain | 200, jobId |
| B07.7 | GET /api/admin/staff | 200, staff array |
| B07.8 | POST /api/admin/staff | 200, success |
| B07.9 | DELETE /api/admin/staff/{username} | 200, success |
| B07.10 | POST /api/admin/optimize-assignments | 200, assignments |
| B07.11 | GET /api/admin/forecast | 200, DemandForecast |
| B07.12 | POST /api/admin/forecast/run | 200, status |
| B07.13 | POST /api/donors/bulk-import-csv | 200, imported/skipped counts |

### TC-B08: Patient Endpoints
| ID | Test Case | Expected |
|---|---|---|
| B08.1 | GET /api/patients/{id} | 200, PatientProfile |
| B08.2 | GET /api/patients/{id}/schedule | 200, ScheduleEntry array |
| B08.3 | GET /api/patients/{id}/chain-history | 200, ChainHistoryEntry array |
| B08.4 | POST /api/patients/{id}/auto-schedule | 200, success |
| B08.5 | GET /api/patients/{id}/locations | 200, LocationEntry array |
| B08.6 | POST /api/patients/{id}/locations | 200, success + location |

### TC-B09: Donor Locations & Health
| ID | Test Case | Expected |
|---|---|---|
| B09.1 | GET /api/donors/{id}/locations | 200, array |
| B09.2 | POST /api/donors/{id}/locations | 200, new location |
| B09.3 | DELETE /api/donors/{id}/locations/{lid} | 200, success |
| B09.4 | PATCH /api/donors/{id}/locations/{lid} | 200, success |
| B09.5 | POST /api/donors/{id}/health-status (unavailable) | 200, auto-repair triggered |
| B09.6 | POST /api/donors/{id}/health-status (available) | 200, hold cleared |

### TC-B10: Leaderboard & Gamification
| ID | Test Case | Expected |
|---|---|---|
| B10.1 | GET /api/donors/leaderboard?city=Hyderabad | 200, top-10 array |
| B10.2 | GET /api/donors/leaderboard (no city param) | 422, validation error |

### TC-B11: Schedule & WebSocket
| ID | Test Case | Expected |
|---|---|---|
| B11.1 | GET /api/schedule | 200, ScheduleEntry array |
| B11.2 | WS /ws → receives chain_update events | JSON with type + data |
| B11.3 | WS /ws → receives chain_break events | JSON with position + patient_id |

---

## Integration / E2E Test Scenarios

### TC-E01: Full Emergency Flow
1. POST /api/emergencies → creates request
2. LangGraph pipeline runs (intake → matching → outreach)
3. WebSocket broadcasts chain_update to Emergency dashboard
4. Donor receives Telegram alert
5. Donor replies YES → chain confirms
6. Dashboard shows CONFIRMED status live
7. Staff marks resolved → outcome logged

### TC-E02: Donor Registration via Telegram
1. User sends /start to @ummedrakho_bot
2. Bot asks for name, blood type, city, phone
3. User uploads blood card photo
4. OCR extracts blood_group + antigens (Kell, Duffy, etc.)
5. Donor record created in Supabase with antigen flags
6. Donor can log into web portal via deep-link

### TC-E03: AI Voice Escalation
1. Emergency created, donor alerted via Telegram
2. Donor doesn't respond within 1 min (test) / 7 min (prod)
3. Monitor agent triggers Bolna voice call
4. Call connects, donor confirms verbally
5. Chain status updates to CONFIRMED

### TC-E04: Bulk CSV Import
1. Admin uploads CSV with 10 donors
2. Backend validates columns, skips duplicates
3. Returns imported/skipped/failed counts
4. New donors appear in getDonors() response

### TC-E05: DPDP Right to Erasure
1. Donor clicks "Delete My Account" on DonorPortal
2. Backend erases from donors, donor_memory, blood_chains, consent_records
3. localStorage cleared, user redirected to /
4. Subsequent getDonor(id) → 404

---

## Test Execution Commands

```bash
# Backend tests
cd BloodBridge_AI_Backend
python -m pytest tests/ -v --asyncio-mode=auto

# Frontend tests
cd BloodBridge_AI_frontend/artifacts/bloodbridge
npx vitest run

# E2E (manual or Playwright)
# Start backend: python -m uvicorn main:app --host 0.0.0.0 --port 8000
# Start frontend: npm run dev
# Run: npx playwright test
```

---

## Coverage Targets

| Layer | Target | Metric |
|---|---|---|
| Backend API routes | 95% | All 53 endpoints have at least 1 test |
| Frontend components | 85% | All pages render + key interactions tested |
| Integration flows | 100% | All 5 E2E scenarios pass |
| OCR + Antigen parsing | 90% | Known card formats parsed correctly |
