# BloodBridge AI — Live Tracker (v1)

> The AI updates this file after each prompt. Status keys:
> ⬜ NOT STARTED · 🟡 READY (deps met) · 🔵 IN PROGRESS · ✅ DONE · ⛔ BLOCKED · 🔒 LOCKED (deps not met)
>
> **How to use:** Say a prompt number ("do A2") or "continue with the tracker". The AI finds the
> next actionable prompt for you here, runs it from `../next_tasksv4.md`, then updates this file.
> When a 🏁 CHECKPOINT row is reached, STOP and merge before continuing.

Current stage: **STAGE 0 — Setup** · Next action: Dev 1 → A1

---

## Dev 1 (Developer A) queue
| # | Prompt | Status | Depends on | Notes |
|---|---|---|---|---|
| 1 | A1 Bedrock migration + gamification fix ★ | ✅ DONE | — | Run ALONE. Merge gate. |
| 2 | A2 Bridge reframe + real-data seed | ✅ DONE | C1 | |
| 5 | M1 Location schema + geohash + seed ★ | 🔒 LOCKED | C2 | Merge gate. |
| 6 | M2 Geo radius-tier + weighted matching | 🔒 LOCKED | M1 | |
| 8 | M3 Hungarian multi-patient assignment | 🔒 LOCKED | M2 | adds scipy |
| 11 | A3 Demand-forecast agent | 🔒 LOCKED | C2 | |
| 12 | A4 Churn retrain | 🔒 LOCKED | C2 | |
| 15 | A5 Demand-forecast admin UI | 🔒 LOCKED | A3 | |
| 16 | A6 Production config | 🔒 LOCKED | — (do in Stage 3) | |
| 19 | A7 Dockerize + EC2 | 🔒 LOCKED | C6 | |
| 20 | A8 Webhook + nginx HTTPS | 🔒 LOCKED | A7 | |

## Dev 2 (Developer B) queue
| # | Prompt | Status | Depends on | Notes |
|---|---|---|---|---|
| — | Prep (Bolna dashboard, read code) | ✅ DONE | — | While A1 runs. No coding. |
| 3 | B1 Fully agentic Telegram bot | ✅ DONE | C1 | import from core/llm_provider |
| 4 | B2 Comprehend + Textract | ✅ DONE | C1 | requests requirements.txt change |
| 7 | M4 Multi-location APIs | 🔒 LOCKED | C3 | |
| 9 | M5 Donor health + auto-repair | 🔒 LOCKED | M2, B1 | EXTEND existing availability tool |
| 10 | M6 Location/zone UI (additive) | 🔒 LOCKED | M4, M5 | |
| 13 | B3 Voice hardening + SMS | 🔒 LOCKED | B1 | hands job to Dev 1 |
| 14 | B4 Failure-learning loop | 🔒 LOCKED | B1 | |
| 17 | B5 Framer-motion polish | 🔒 LOCKED | — (Stage 3) | |
| 18 | B6 RLS + JWT hardening | 🔒 LOCKED | — (Stage 3) | |
| 21 | B7 S3 + CloudFront | 🔒 LOCKED | C6 | |
| 22 | B8 Smoke test | 🔒 LOCKED | A7,A8,B7 | |

---

## Checkpoints (🏁 = stop & merge)
| Checkpoint | Unlocks | Status |
|---|---|---|
| 🏁 C1 — merge A1 | A2, B1, B2 | ✅ DONE |
| 🏁 C2 — merge A2+B1+B2 | M1, A3, A4 | ✅ DONE |
| 🏁 C3 — merge M1 | M2, M4 | ⬜ pending |
| 🏁 C4 — merge M2+M3+M4+M5 | M6 | ⬜ pending |
| 🏁 C5 — merge A3+A4+B3+B4 | Stage 3 | ⬜ pending |
| 🏁 C6 — merge A5+A6+B5+B6 (verify build) | Stage 4 | ⬜ pending |
| 🏁 C7 — FINAL smoke test | demo | ⬜ pending |

---

## Activity log (AI appends here)
- (init) Tracker created. Next action: Dev 1 runs A1 alone; Dev 2 preps. Stop at C1.
- (update) A1 Bedrock migration + gamification fix completed. Next action: Checkpoint C1 (merge).
- (update) Checkpoint C1 cleared. Dev 2 starting B1 (Fully agentic Telegram bot).
- (update) Dev 1 completed A2 (Universal donor rules + Vision LLM update).
- (update) B1 and B2 completed by Dev 2. Checkpoint C2 cleared.

