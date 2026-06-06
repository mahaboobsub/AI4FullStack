# BloodBridge AI — Live Tracker (v1)

> **MODE CHANGE (solo):** Dev 2 is out sick. From checkpoint C2 onward this is a **SINGLE-DEVELOPER**
> build. The Dev1/Dev2 split no longer applies — one developer runs ALL remaining prompts
> sequentially on one branch. Checkpoints are now just **commit + push + verify** milestones,
> not two-person merge gates.

Status keys: ⬜ NOT STARTED · 🟡 READY · 🔵 IN PROGRESS · ✅ DONE · 🔒 LOCKED (deps not met)

Current commit on main: `ec36ea1` (A1+A2+B1+B2 merged) · Branch: `dev-2` (== main, clean)
Checkpoints cleared: **C1 ✅, C2 ✅**
**Next action: run M1** (then M2 → M3 → M4 → M5 → M6 → A3 → A4 → B3 → B4 → A5 → A6 → B5 → B6 → A7 → A8 → B7 → B8)

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
| 1 | M1 Location schema + geohash + geo seed | 🟡 READY | C2 ✅ | Start here. |
| 2 | M2 Geo radius-tier + weighted matching | 🔒 | M1 | |
| 3 | M3 Hungarian multi-patient assignment | 🔒 | M2 | adds scipy |
| 4 | M4 Multi-location APIs | 🔒 | M1 | |
| 5 | M5 Donor health + auto-repair | 🔒 | M2 | extend existing availability tool |
| — | 🏁 C4 (commit+push: matching+health) | 🔒 | M2..M5 | (C3 collapses into solo flow) |
| 6 | M6 Location/zone UI (additive) | 🔒 | M4, M5 | |
| 7 | A3 Demand-forecast agent | 🔒 | C2 ✅ | |
| 8 | A4 Churn retrain | 🔒 | C2 ✅ | |
| 9 | B3 Voice hardening + SMS | 🔒 | B1 ✅ | own the scheduler job now (solo) |
| 10 | B4 Failure-learning loop | 🔒 | B1 ✅ | |
| — | 🏁 C5 (commit+push: agents) | 🔒 | A3,A4,B3,B4 | |
| 11 | A5 Demand-forecast admin UI | 🔒 | A3 | |
| 12 | A6 Production config | 🔒 | — | |
| 13 | B5 Framer-motion polish | 🔒 | — | |
| 14 | B6 RLS + JWT hardening | 🔒 | — | |
| — | 🏁 C6 (commit+push + verify pnpm build) | 🔒 | A5,A6,B5,B6 | |
| 15 | A7 Dockerize + EC2 | 🔒 | C6 | |
| 16 | A8 Telegram webhook + nginx HTTPS | 🔒 | A7 | |
| 17 | B7 S3 + CloudFront | 🔒 | C6 | |
| 18 | B8 Smoke test | 🔒 | A7,A8,B7 | |
| — | 🏁 C7 (FINAL smoke test) | 🔒 | all | |

---

## Solo merge rule (simplified)
Single developer + single branch. After each prompt: commit. After each 🏁 checkpoint: push to main
and (at C6) verify `pnpm build` + backend boots; (at C7) run SMOKE_TEST.md. No partner pulls needed.
Shared files (config.py, requirements.txt, scheduler/jobs.py, api/admin.py) are now all yours — edit
directly, no handoff notes required.

## Activity log
- ec36ea1: C1 + C2 cleared (A1, A2, B1, B2 merged). Dev 2 out sick → switching to SOLO mode.
- NEXT: run M1. Update this log + flip statuses after each prompt.
