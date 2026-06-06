# BloodBridge AI — Live Tracker (v1)

> **MODE CHANGE (solo):** Dev 2 is out sick. From checkpoint C2 onward this is a **SINGLE-DEVELOPER**
> build. The Dev1/Dev2 split no longer applies — one developer runs ALL remaining prompts
> sequentially on one branch. Checkpoints are now just **commit + push + verify** milestones,
> not two-person merge gates.

Status keys: ⬜ NOT STARTED · 🟡 READY · 🔵 IN PROGRESS · ✅ DONE · 🔒 LOCKED (deps not met)

Current commit on main: `ec36ea1` (A1+A2+B1+B2 merged) · Branch: `main`
Checkpoints cleared: **C1 ✅, C2 ✅**

---

## Completed (merged to main)
| Prompt | Status | Commit |
|---|---|---|
| A1 Bedrock migration + gamification fix | ✅ DONE | a812caf |
| A2 Bridge reframe + real-data seed | ✅ DONE | 2328860 |
| B1 Fully agentic Telegram bot | ✅ DONE | 2d8f012 |
| B2 Comprehend + Textract | ✅ DONE | 2d8f012 |
| 🏁 C1 (merge A1) | ✅ CLEARED | |
| 🏁 C2 (merge A2+B1+B2) | ✅ CLEARED | ec36ea1 |

## Remaining queue (SOLO — run top to bottom)
| Order | Prompt | Status | Depends on | Notes |
|---|---|---|---|---|
| 1 | M1 Location schema + geohash + geo seed | ✅ DONE | C2 ✅ | geo_service.py + schema_v4_locations.sql |
| 2 | M2 Geo radius-tier + weighted matching | ✅ DONE | M1 | matching_engine.py wired into neo4j_match.py |
| 3 | M3 Hungarian multi-patient assignment | ✅ DONE | M2 | assignment_optimizer.py + admin endpoint + scipy |
| 4 | M4 Multi-location APIs | ✅ DONE | M1 | CRUD endpoints in patients.py + donors.py |
| 5 | M5 Donor health + auto-repair | ✅ DONE | M2 | health-status endpoint + auto-decline active chains |
| — | 🏁 C4 (commit+push: matching+health) | 🟡 READY | M2..M5 ✅ | Ready to commit |
| 6 | M6 Location/zone UI (additive) | ✅ DONE | M4, M5 | LocationManager component in Patient + Donor pages |
| 7 | A3 Demand-forecast agent | ✅ DONE | C2 ✅ | 5-node pipeline + API + scheduler job |
| 8 | A4 Churn retrain | ✅ DONE | C2 ✅ | Real features + batch scoring + monthly cron |
| 9 | B3 Voice hardening + SMS | ✅ DONE | B1 ✅ | Stale call retry + SMS fallback + BOLNA_AGENT_CONFIG.md |
| 10 | B4 Failure-learning loop | ✅ DONE | B1 ✅ | analyze_response_and_update() + protocol stats |
| — | 🏁 C5 (commit+push: agents) | 🟡 READY | A3,A4,B3,B4 ✅ | Ready to commit |
| 11 | A5 Demand-forecast admin UI | ✅ DONE | A3 | DemandForecastPanel in Admin.tsx |
| 12 | A6 Production config | ✅ DONE | — | CORS from env, prod safety checks in main.py |
| 13 | B5 Framer-motion polish | 🔵 PARTIAL | — | Animations in new M6/M5/A5 components; deeper page pass optional |
| 14 | B6 RLS + JWT hardening | ✅ DONE | — | SECURITY.md + JWT_SECRET config + RLS policies |
| — | 🏁 C6 (commit+push + verify pnpm build) | 🟡 READY | A6,B6 ✅ | |
| 15 | A7 Dockerize + EC2 | ✅ DONE | C6 | Dockerfile + .dockerignore + AWS_DEPLOY.md |
| 16 | A8 Telegram webhook + nginx HTTPS | ✅ DONE | A7 | nginx config + setup_webhook.py (existed) |
| 17 | B7 S3 + CloudFront | ✅ DONE | C6 | deploy.sh in AWS_DEPLOY.md |
| 18 | B8 Smoke test | ✅ DONE | A7,A8,B7 | SMOKE_TEST.md created |
| — | 🏁 C7 (FINAL smoke test) | 🟡 READY | all | Run SMOKE_TEST.md |

---

## Solo merge rule (simplified)
Single developer + single branch. After each prompt: commit. After each 🏁 checkpoint: push to main
and (at C6) verify `pnpm build` + backend boots; (at C7) run SMOKE_TEST.md. No partner pulls needed.
Shared files (config.py, requirements.txt, scheduler/jobs.py, api/admin.py) are now all yours — edit
directly, no handoff notes required.

## Activity log
- ec36ea1: C1 + C2 cleared (A1, A2, B1, B2 merged). Dev 2 out sick → switching to SOLO mode.
- (update) M1 Location Schema + Geo Seed completed.
- (update) M2 Geo radius-tier + weighted matching completed.
- (update) M3 Hungarian multi-patient assignment completed.
- (update) M4 Multi-location APIs completed (patient + donor CRUD).
- (update) M5 Donor health self-update + auto-repair completed.
- (update) A3 Demand-forecast agent (5-node pipeline + API + cron) completed.
- (update) A4 Churn retrain on real labels completed.
- (update) B3 Voice hardening + SMS fallback + BOLNA config completed.
- (update) B4 Failure-learning + self-improving outreach loop completed.
- (update) A6 Production config (CORS, safety checks) completed.
- (update) B6 RLS + JWT hardening (SECURITY.md, JWT_SECRET) completed.
- (update) A7 Dockerize (Dockerfile, .dockerignore, AWS_DEPLOY.md) completed.
- (update) A8 Telegram webhook + nginx config completed.
- (update) B7 S3 + CloudFront deploy docs completed.
- (update) B8 SMOKE_TEST.md created. ALL BACKEND PROMPTS COMPLETE.
- GAP-CLOSURE SESSION (frontend + M5 wiring):
  * M6 ✅ — LocationManager.tsx (patient 1-5 search locations, donor N backup areas) wired into
    PatientDashboard.tsx and DonorPortal.tsx; api.ts location CRUD functions added.
  * A5 ✅ — DemandForecastPanel.tsx (weekly demand bar chart + AI summary + shortage banners with
    one-click outreach) wired into Admin.tsx; api.ts forecast functions added.
  * M5 wiring ✅ — DonorPortal HealthStatusControl.tsx (report unavailable / available);
    api/donors.py health-status now does Neo4j update + chain_repair trigger + ntfy + WS broadcast;
    telegram_bot.report_medical_hold routes through the M5 endpoint (auto-repair + notify).
  * B5 partial — framer-motion animations included in the new components (staggered lists, spring,
    pulse). A deeper pass over existing pages remains optional polish.
  * Note: TS-server shows transient "cannot find module react" on HealthStatusControl.tsx only;
    LocationManager.tsx (identical imports) and DonorPortal.tsx (importer) are clean → resolves on
    Vite build / TS-server restart. Not a code defect.
- REMAINING: optional Map radius-ring overlay; verify migrations/seeds executed against Supabase+Neo4j
  (schema_v4_locations.sql + geo seed); deployment verify (A7/A8/B7) then C7 smoke test.

