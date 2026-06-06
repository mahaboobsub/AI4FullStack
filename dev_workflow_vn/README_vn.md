# BloodBridge AI — Developer Workflow (vn)

This folder is the **single source of truth** for how the two developers build the
remaining BloodBridge AI work in parallel using Antigravity (vibe coding).

> **Version note:** This folder uses the suffix `vn` so it is never confused with the
> product version docs (`next_tasksv4.md`, PRD v6, etc.). Files inside are versioned
> `_v1`, `_v2`… as they are revised. Current active versions:
> - `DEV_MAP_v1.md`  — the full end-to-end task plan for Dev 1 and Dev 2
> - `TRACKER_v1.md`  — live status board (what's done, in progress, blocked, next)

---

## Files in this folder

| File | Purpose |
|---|---|
| `README_vn.md` | This file. How the system works. |
| `DEV_WORKFLOW_v1.md` | **★ The execution file — copy prompts from here.** All A/B/M prompts arranged in exact run order, tagged [DEV 1]/[DEV 2], with inline 🏁 checkpoints. |
| `DEV_MAP_v1.md` | The planning view: ownership, dependencies, shared-file rules, checkpoint summary. |
| `TRACKER_v1.md` | Live status of every prompt. Updated as work completes. |

`DEV_WORKFLOW_v1.md` is now self-contained (prompt text copied in) — devs do not need to open
`../next_tasksv4.md`, though it remains the original reference.

---

## How the AI uses this folder (the mechanic)

When a developer types either:
- a **prompt number** (e.g. "do A2", "run M1", "continue B3"), OR
- **"continue with the tracker"** / "what's next"

…the AI must:
1. Open `TRACKER_v1.md` and find the next not-done prompt for that developer (respecting
   dependencies and checkpoints).
2. Open `DEV_MAP_v1.md` to read that prompt's ownership, dependencies, and the file it touches.
3. Open `../next_tasksv4.md` and execute the matching prompt (A/B/M) text.
4. After completing, **update `TRACKER_v1.md`**: set that prompt to ✅ DONE, set the next one to
   🔵 IN PROGRESS or 🟡 READY, and note any new blockers.
5. If the completed prompt is the **last item before a CHECKPOINT**, the AI must STOP and print:
   "⛔ CHECKPOINT Cn reached — both developers merge to main before continuing."

---

## The golden rules (read once before starting)

1. **Branch per developer.** `dev-1` and `dev-2`. Never both push to `main` directly. Merge via PR.
2. **A1 and M1 are MERGE GATES.** The owning dev runs them ALONE and merges before the other dev
   starts dependent work. (A1 rewrites LLM imports everywhere; M1 creates the location tables
   everything else needs.)
3. **Dev 1 owns these shared files** — Dev 2 never edits them, only requests changes:
   `core/config.py`, `requirements.txt`, `scheduler/jobs.py`, `api/admin.py`.
4. **Small PRs.** Merge after each prompt, not in giant batches. `git pull main` before each new prompt.
5. **Stop at every CHECKPOINT and merge.** Do not run past a checkpoint with unmerged code.
6. **Frontend (B5, B7, M6) never conflicts with backend** — fully parallel-safe anytime after its data deps.
