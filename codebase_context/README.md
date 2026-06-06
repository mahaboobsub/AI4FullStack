# 🧠 CODEBASE CONTEXT MEMORY

This folder is the **AI memory layer** for BloodBridge AI. It eliminates the need for AI tools to re-scan the entire codebase each session, saving **~90% of tokens** and improving accuracy.

---

## 📖 What This Is

Instead of asking an AI tool to "scan the codebase and understand it" every time (15,000–80,000+ tokens wasted), you can now just say:

> "Read the codebase context from `codebase_context/`. The task is: [YOUR TASK]"

The AI tool reads these 5 lightweight files (~10,000 tokens total) instead of 60+ Python source files. It gets **the same understanding, much faster**.

---

## 📁 Files In This Folder

| File | Purpose | When to Read | Size |
|------|---------|-----------|------|
| **QUICK_REF.md** | Ultra-compressed project cheatsheet (50 lines) | Every session, **FIRST** | ~2 KB |
| **CODEBASE_MAP.md** | Full architecture, module index, data models, API routes | Once per session or when unfamiliar | ~50 KB |
| **CODEBASE_TRACKER.md** | Session logs, TODO list, open bugs, architecture decisions | Every session start (check progress) | ~15 KB |
| **ACTIVE_SESSION.md** | Current session task, context, working notes | Overwrite at session start | ~3 KB |
| **README.md** | This file — instructions for the system | Onboarding only | ~5 KB |

---

## 🚀 HOW TO USE THIS SYSTEM

### ✅ STARTING A NEW AI SESSION

Give your AI tool this prompt:

```
Read the codebase context from this folder:
1. codebase_context/QUICK_REF.md (first)
2. codebase_context/CODEBASE_TRACKER.md (check TODOs)
3. codebase_context/ACTIVE_SESSION.md (see last session notes)

Then update codebase_context/ACTIVE_SESSION.md with:
- Today's date
- Session number (from CODEBASE_TRACKER.md)
- Your task: [YOUR SPECIFIC TASK]

Do NOT scan the full codebase. Use CODEBASE_MAP.md only if you need deeper context.
Read specific source files only when needed for your task.
```

**Example Task Prompts:**
- "Fix BUG-001 (Vapi webhook reliability). Implement retry logic with exponential backoff."
- "Implement Neo4j geohashing optimization. See TODO High Priority #2."
- "Add 3 new gamification challenge types. Update services/gamification_service.py."

### 🏁 ENDING A SESSION

Give your AI tool this prompt:

```
Session complete. Update the codebase context:

1. Update codebase_context/CODEBASE_TRACKER.md:
   - Add new session entry at the TOP of the SESSION LOG
   - Include: Goal, Status, Files Modified/Added/Deleted, What Was Done, Blockers
   - Move any completed TODOs from "Open" to "FEATURE REGISTRY"
   
2. If architecture changed:
   - Update codebase_context/CODEBASE_MAP.md (new agents/routes/tables/services)
   
3. Clear codebase_context/ACTIVE_SESSION.md for next session
```

### 🔄 WHEN TO UPDATE CODEBASE_MAP.md

Update `CODEBASE_MAP.md` when:
- ✏️ **New file/folder** added to the project
- ✏️ **New API route** created (add to 🌐 API / ROUTES section)
- ✏️ **Data model changed** (add to 🗃️ DATA MODELS section)
- ✏️ **New external service** integrated (add to 🔌 EXTERNAL INTEGRATIONS section)
- ✏️ **New agent node** added to LangGraph (add to agents/ folder structure + graph.py)
- ✏️ **New environment variable** required (add to 🌍 ENVIRONMENT VARIABLES section)
- ✏️ **Major refactor** occurred

**Do NOT update CODEBASE_MAP.md** for:
- Small bug fixes
- Logic changes in existing functions
- Changes within a single file that don't affect the module index

---

## 📊 TOKEN COMPARISON

| Scenario | Tokens Used | Time | Cost |
|----------|------------|------|------|
| **Full codebase scan every session** | 15,000–80,000+ | 2–5 min | ~$1–5 per session |
| **Using this context system** | ~10,000 | 30 sec | ~$0.10 per session |
| **Savings per session** | ~70,000 | ~4.5 min | ~$4.90 |
| **Savings over 100 sessions** | 7,000,000 | 450 min (7.5 hrs) | ~$490 |

**Bottom line:** You save ~90% tokens + time by using this system consistently.

---

## 🔐 IMPORTANT NOTES

### ⚠️ Keep This Folder Updated
- **Stale context map = worse than no map.** If the codebase changes and CODEBASE_MAP.md isn't updated, the AI tool will make wrong assumptions.
- At the END of every session, add an entry to CODEBASE_TRACKER.md's SESSION LOG.
- If architecture changed, update CODEBASE_MAP.md before closing the session.

### ✅ Commit to Version Control
```bash
git add codebase_context/
git commit -m "chore: update codebase context after session #N"
git push
```

This folder is part of the codebase. Keep it in git so all team members + AI tools see the latest context.

### 📝 Session Log Format
```
### Session [N] — [DATE] — [AI Tool Used]

**Goal:** [What we set out to do]

**Status:** ✅ Completed / 🟡 Partial / ❌ Blocked

**Files Modified:**
- `[path]` — [what changed]

**Files Added:**
- `[path]` — [what it is]

**What Was Done:**
- [bullet 1]
- [bullet 2]

**Notes for Next Session:**
- [what to pick up on]
```

---

## 🎯 USAGE PATTERNS

### Pattern 1: Small Bug Fix
```
1. Read QUICK_REF.md + CODEBASE_TRACKER.md (1 min)
2. Check which file has the bug (from CODEBASE_MAP.md)
3. Read that specific file
4. Fix the bug
5. Update CODEBASE_TRACKER.md with bug status
```

### Pattern 2: New Feature
```
1. Read QUICK_REF.md + CODEBASE_TRACKER.md (1 min)
2. Check similar feature in CODEBASE_MAP.md (find patterns)
3. Read files involved in similar feature
4. Implement new feature following same patterns
5. Add new route/agent/service to CODEBASE_MAP.md
6. Update CODEBASE_TRACKER.md with session log + new feature in FEATURE REGISTRY
```

### Pattern 3: Performance Optimization
```
1. Read QUICK_REF.md + CODEBASE_TRACKER.md (1 min)
2. Find performance TODOs in CODEBASE_TRACKER.md
3. Read relevant files from CODEBASE_MAP.md module index
4. Implement optimization (e.g., geohashing for Neo4j)
5. Update CODEBASE_TRACKER.md with TODO status
6. If architecture changed, update CODEBASE_MAP.md
```

---

## 🔧 MAINTENANCE

### Monthly Checklist
- [ ] Review CODEBASE_TRACKER.md SESSION LOG — any stale sessions?
- [ ] Check open TODOs — any completed items to mark?
- [ ] Review open BUGS — any fixed?
- [ ] Verify CODEBASE_MAP.md reflects current state (run `git log --oneline codebase_context/` last 30 days)

### Before Production Deploy
- [ ] CODEBASE_TRACKER.md is up to date?
- [ ] All new features documented in CODEBASE_MAP.md?
- [ ] No TODOs blocking critical paths?

---

## 📞 TROUBLESHOOTING

### AI Tool Reads Wrong Information
→ Check if CODEBASE_MAP.md is stale. Run `git log` to see when it was last updated.
→ If stale, update it immediately with latest architecture.

### AI Tool Misses a File or Function
→ The file might not be in CODEBASE_MAP.md module index.
→ Add it under the appropriate section (📋 MODULE INDEX).

### Token Usage Still High
→ You might be asking AI to scan full source files unnecessarily.
→ First read QUICK_REF.md + CODEBASE_TRACKER.md, THEN ask AI to read source files only if needed.

### Merge Conflicts in This Folder
→ Unlikely, but if they happen:
  - Keep all session entries (merge in CODEBASE_TRACKER.md)
  - For CODEBASE_MAP.md, take the newest (higher date in header)
  - Re-scan if unsure

---

## 📚 EXAMPLES

### Example 1: Fixing BUG-001
```
AI Prompt:
"I need to fix BUG-001 (Vapi webhook reliability). 
Read codebase_context/CODEBASE_TRACKER.md to see the bug.
Then read codebase_context/CODEBASE_MAP.md to understand 
the Vapi integration. 
Implement retry logic with exponential backoff.
Update voice_service.py and webhooks.py."

AI reads:
- QUICK_REF.md (30 sec)
- CODEBASE_TRACKER.md (find BUG-001)
- CODEBASE_MAP.md (find services/voice_service.py + api/webhooks.py)
- Actual source files (services/voice_service.py, api/webhooks.py)
- Implements fix
- Updates CODEBASE_TRACKER.md with session log
```

### Example 2: Adding New Agent
```
AI Prompt:
"Add a new LangGraph agent for real-time inventory management.
Read QUICK_REF.md for stack overview.
Read CODEBASE_MAP.md to understand:
  - LangGraph structure (agents/graph.py)
  - How other agents are built
  - Where to add the node
Then create agents/inventory_agent.py, 
wire it into agents/graph.py,
and document it in CODEBASE_MAP.md."

AI reads:
- QUICK_REF.md (understand stack)
- CODEBASE_MAP.md (understand agent pattern)
- agents/graph.py (see how other nodes are wired)
- agents/repair.py (inventory_agent already exists! check it)
- Realizes inventory_agent exists, documents it better in CODEBASE_MAP.md
```

---

## ✅ SUCCESS CHECKLIST

This system works when:
- ✅ QUICK_REF.md is **the** first file every AI reads
- ✅ CODEBASE_TRACKER.md **SESSION LOG** is updated at end of every session
- ✅ CODEBASE_MAP.md is updated when **architecture changes**
- ✅ Team reviews CODEBASE_TRACKER.md **weekly** to see progress
- ✅ No AI tool scans full source files without **first reading** context files
- ✅ This folder is **committed to git** with every change

---

## 🎓 ONBOARDING NEW TEAM MEMBERS

New developer or AI instance?

1. **Start here:** Read `codebase_context/QUICK_REF.md` (5 min)
2. **Then:** Run `python BloodBridge_AI_Backend/main.py` to verify setup works
3. **Then:** Read `codebase_context/CODEBASE_MAP.md` for deep dive
4. **Then:** Check `codebase_context/CODEBASE_TRACKER.md` for latest progress
5. **Then:** Ask: "What should I work on?" → Pick from TODO list in CODEBASE_TRACKER.md

That's it. You're ready to contribute without wasting 2–5 hours re-learning the codebase.

---

## 📞 QUESTIONS?

- **How do I know if CODEBASE_MAP.md is stale?** → Check the "Generated" date in the header. If > 2 weeks old and code changed, it's stale.
- **Should I read CODEBASE_MAP.md for every task?** → No. Only if unfamiliar. QUICK_REF.md + CODEBASE_TRACKER.md usually enough.
- **What if I make a change not documented here?** → Update the relevant section in CODEBASE_MAP.md, then update CODEBASE_TRACKER.md session log.
- **Can I use this for other projects?** → Yes! Copy this folder structure to any other monorepo. Adapt the templates.

---

**Generated:** 2026-06-06
**Last Updated:** [will update per session]

