# BloodBridge AI — End-to-End Developer Map (v1)

Prompt text lives in `../next_tasksv4.md`. This map controls **order, ownership, dependencies,
and merge checkpoints**. Dev 1 = Developer A. Dev 2 = Developer B.

Legend: ★ = merge gate (run alone, merge before partner continues). ⛔ = stop & merge checkpoint.

---

## Roles

- **Dev 1 (A)** — Data, schema, AI agents, ML, matching engine, infra/deploy.
- **Dev 2 (B)** — Agents comms (Telegram/voice), failure-learning, APIs, frontend.

## Shared files (Dev 1 owns — Dev 2 requests changes, never edits directly)
`core/config.py` · `requirements.txt` · `scheduler/jobs.py` · `api/admin.py`

---

## STAGE 0 — Setup (both, 5 min, together)
- Create branches `dev-1`, `dev-2` off `main`.
- Confirm AWS creds + Bedrock model access (Dev 1), Bolna dashboard access (Dev 2).
- Both read `README_vn.md`.

---

## STAGE 1 — Foundation
| Order | Prompt | Owner | Depends on | Touches | Notes |
|---|---|---|---|---|---|
| 1 | **A1** Bedrock migration + gamification fix ★ | Dev 1 | — | `core/llm_provider.py`, all agents, `config.py`, `requirements.txt` | Dev 2 does NOT code yet. |
| — | (Dev 2 prep) | Dev 2 | — | none | Configure Bolna dashboard, read codebase. |

### ⛔ CHECKPOINT C1 — merge A1 to main. Both `git pull`. (LLM adapter now exists.)

| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 2 | **A2** Bridge-model reframe + real-data seed | Dev 1 | A1 | `data/*.sql`, `data/seed_*.py`, `bridges`/`bridge_memberships` |
| 3 | **B1** Fully agentic Telegram bot | Dev 2 | C1 | `services/telegram_bot.py` (imports `core/llm_provider`) |
| 4 | **B2** Comprehend + Textract | Dev 2 | C1 | `services/language_service.py`, `ocr_service.py`, `requirements.txt`* |

\* B2 removes pytesseract/Pillow from requirements.txt → Dev 2 **requests** this; Dev 1 applies it.

### ⛔ CHECKPOINT C2 — merge A2 + B1 + B2 to main. Both `git pull`. (Bridge schema + real data live.)

---

## STAGE 1.5 — Smart Matching Module (the geo/multi-location/health fixes)
> Fixes: patient lat/lng missing, brittle city matching, no multi-location, donor health path,
> antigen leak. **A2 must be merged (C2) before any M-prompt.**

| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 5 | **M1** Location schema + geohash + geo seed ★ | Dev 1 | C2 | `data/schema_v4_locations.sql`, `services/geo_service.py`, `seed_*.py` |

### ⛔ CHECKPOINT C3 — merge M1 to main. Both `git pull`. (Location tables exist — Dev 2 can start M4.)

| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 6 | **M2** Geo radius-tier + weighted matching | Dev 1 | M1 | `services/matching_engine.py`, `agents/neo4j_match.py` |
| 7 | **M4** Multi-location APIs | Dev 2 | M1 (C3) | `api/patients.py`, `api/donors.py`, `lib/api.ts` |
| 8 | **M3** Hungarian multi-patient assignment | Dev 1 | M2 | `services/assignment_optimizer.py`, `api/admin.py`*, `requirements.txt`* (scipy) |
| 9 | **M5** Donor health self-update + auto-repair | Dev 2 | M2, B1 | `api/donors.py`, `services/telegram_bot.py` (EXTEND existing `set_my_availability` tool — do NOT add a duplicate), `agents/repair.py` reuse |

\* M3 edits shared `api/admin.py` + `requirements.txt` (Dev 1 owns both — fine, same dev).

### ⛔ CHECKPOINT C4 — merge M2 + M3 + M4 + M5 to main. Both `git pull`. (Matching engine + health flow live.)

| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 10 | **M6** Location & zone UI (additive) | Dev 2 | M4, M5 | `PatientDashboard.tsx`, `DonorPortal.tsx`, `Map.tsx`, `Emergency.tsx` |

---

## STAGE 2 — Intelligence Agents
| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 11 | **A3** Demand-Forecast LangGraph agent | Dev 1 | C2 (real data) | `agents/demand_forecast_agent.py`, `scheduler/jobs.py`, `api/admin.py` |
| 12 | **A4** Churn retrain on real labels | Dev 1 | C2 | `ml/train_churn.py`, `ml/churn_predictor.py`, `scheduler/jobs.py` |
| 13 | **B3** Voice hardening + SMS fallback | Dev 2 | B1 | `agents/voice.py`, `api/webhooks.py`, `scheduler/jobs.py`* |
| 14 | **B4** Failure-learning loop | Dev 2 | B1 | `services/donor_memory.py`, `agents/planner.py`, `api/webhooks.py`, `agents/outcome.py` |

\* B3 adds a job to `scheduler/jobs.py` (Dev 1-owned). Dev 2 gives Dev 1 the job function to wire in,
OR appends a separate function and Dev 1 merges the registration block last.

### ⛔ CHECKPOINT C5 — merge A3 + A4 + B3 + B4. Both `git pull`. (All agents complete.)

---

## STAGE 3 — Frontend & Hardening
| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 15 | **A5** Demand-forecast admin UI | Dev 1 | A3 | `dashboard/Admin.tsx`, `lib/api.ts` |
| 16 | **A6** Production config | Dev 1 | — | `vite.config.ts`, `core/config.py`, `main.py` |
| 17 | **B5** Framer-motion polish (additive) | Dev 2 | — | `DonorPortal.tsx`, `Emergency.tsx`, `Graph.tsx` |
| 18 | **B6** RLS + JWT hardening | Dev 2 | — | SQL policies, `core/security.py`, `SECURITY.md` |

### ⛔ CHECKPOINT C6 — merge A5 + A6 + B5 + B6. Both `git pull`. Verify `pnpm build` + local run.

---

## STAGE 4 — AWS Deployment (only after C6 verifies locally)
| Order | Prompt | Owner | Depends on | Touches |
|---|---|---|---|---|
| 19 | **A7** Dockerize + EC2 | Dev 1 | C6 | `Dockerfile`, `.dockerignore`, `ml/__init__.py`, `AWS_DEPLOY.md` |
| 20 | **A8** Telegram webhook + nginx HTTPS | Dev 1 | A7 | `setup_webhook.py`, `nginx/bloodbridge.conf`, `bloodbridge.service` |
| 21 | **B7** S3 + CloudFront frontend | Dev 2 | C6 | `AWS_DEPLOY.md`, `deploy.sh`, `.env.production` |
| 22 | **B8** Smoke test checklist | Dev 2 | A7,A8,B7 | `SMOKE_TEST.md` |

### ⛔ CHECKPOINT C7 — FINAL. Run SMOKE_TEST.md (21 checks). All must pass before demo.

---

## Checkpoint summary (where both devs STOP and merge)
- **C1** after A1 — LLM adapter (merge gate)
- **C2** after A2 + B1 + B2 — bridge schema + real data
- **C3** after M1 — location tables (merge gate)
- **C4** after M2 + M3 + M4 + M5 — matching engine + health
- **C5** after A3 + A4 + B3 + B4 — agents
- **C6** after A5 + A6 + B5 + B6 — frontend + hardening (verify build)
- **C7** after A7 + A8 + B7 + B8 — deployed + smoke tested

## Conflict-risk files (coordinate explicitly)
- `requirements.txt` → **Dev 1 only** (B2 removes pytesseract; M3 adds scipy — Dev 1 applies).
- `scheduler/jobs.py` → Dev 1 owns; A3/A4 add jobs; B3 hands its job to Dev 1.
- `api/admin.py` → Dev 1 (A3 forecast endpoint, M3 optimize endpoint, A5 reads it).
- `core/config.py` → Dev 1 (A1 AWS keys, A6 prod validation, B6 JWT_SECRET → Dev 1 adds).
- `lib/api.ts` → M4 (Dev 2) + A5 (Dev 1). Different functions; merge carefully or sequence A5 after M4.
