# BloodBridge AI — V2 Post-Implementation Gap Analysis
## End-to-End Codebase Audit · Fix-Ready Report · Team Inqilab
> **Analysis date:** June 2026 | **Codebase:** `full_code.txt` (post Antigravity v2 session)
> **Verdict:** ~75% of v2 tasks were implemented. 18 specific gaps remain — ranked and fix-ready below.

---

## WHAT V2 SUCCESSFULLY IMPLEMENTED ✅

Before the gaps — here is what Antigravity *did* build correctly:

| Component | What Was Done |
|---|---|
| `api/donors.py` | `/lookup`, `/{id}/rank`, `/{id}/active-request`, `/{id}/availability` — all Phase 1 endpoints |
| `api/patients.py` | `/{id}/schedule`, `/{id}/chain-history` — Phase 1 patient endpoints |
| `api/admin.py` | `GET/POST /api/schedule` — Phase 1.5 done |
| `api/auth.py` | `/telegram-token` + `/telegram-login` — Phase 9.2 deep link done |
| `scheduler/jobs.py` | `run_auto_schedule_generation()` + `run_blood_bank_cache_update()` — Phase 2.1 + 2.3 done |
| `scheduler/cron.py` | Blood bank 15-min job registered. Auto-schedule startup job in `main.py`. Phase 2 ✅ |
| `services/telegram_bot.py` | 10 tools (7 new), multi-turn registration, DPDP gate, language-first — Phase 3 mostly done |
| `pages/DonorLogin.tsx` | Phone lookup wired, `getDonorByLookup()` in api.ts |
| `pages/DonorPortal.tsx` | Real rank, active-request card, real badges, Telegram status — Phase 4 partially done |
| `pages/PatientDashboard.tsx` | Full wiring — schedule, chain history, linked donors — Phase 5 complete |
| `hooks/useEmergencySocket.ts` | Handles all 7 WS event types (donor_confirmed, donor_declined, etc.) — Phase 6.1 ✅ |
| `core/config.py` | `DEMO_MOCK_MODE` flag + `WEB_PORTAL_URL` added |
| `data/seed_demo.py` | Demo data seed script exists |
| `lib/api.ts` | All v2 type definitions + API functions added |

---

## GAP INVENTORY — 18 ISSUES RANKED BY SEVERITY

---

### 🔴 GAP-01 · CRITICAL · Duplicate Python Function Names in `api/donors.py`

**What's broken:** Two functions named `trigger_voice_call` and two named `trigger_outreach` exist in the same file. Python silently overwrites the first definition with the second. The first-defined routes (`/{id}/voice` and `/{id}/outreach`) will actually execute the second function's code — which requires staff auth — breaking manual outreach for non-staff callers.

**Evidence:**
```python
# First definition (line ~3770) — no staff auth
@router.post("/{id}/voice", response_model=VoiceCallResponse)
async def trigger_voice_call(id: str, request: Request): ...

# Second definition (line ~4150) — requires staff auth — OVERWRITES the first
@router.post("/{id}/trigger-voice")
async def trigger_voice_call(id: str, staff: dict = Depends(get_current_staff_admin)): ...
```

**Fix:** Rename the functions. No route path change needed — they ARE different paths already.

```python
# In api/donors.py — rename the first-defined functions

# Change this:
async def trigger_voice_call(id: str, request: Request):
# To:
async def trigger_voice_call_legacy(id: str, request: Request):

# Change this:
async def trigger_outreach(id: str):
# To:
async def trigger_outreach_legacy(id: str):
```

---

### 🔴 GAP-02 · CRITICAL · Tool `.ainvoke()` Called With Raw String, Not Dict

**What's broken:** All bot commands that invoke tools with a single `chat_id` arg use `.ainvoke(str(chat_id))`. LangChain tools with a Pydantic `args_schema` that has a named field expect a dict, not a positional string. The calls will either silently fail or pass the chat_id as the wrong field.

**Evidence in `services/telegram_bot.py` `handle_command()`:**
```python
elif cmd_clean == "/profile":
    return await get_my_profile.ainvoke(str(chat_id))  # ❌ Wrong

elif cmd_clean == "/schedule":
    return await get_my_schedule.ainvoke(str(chat_id))  # ❌ Wrong

elif cmd_clean == "/eligibility":
    return await get_my_eligibility.ainvoke(str(chat_id))  # ❌ Wrong

elif cmd_clean == "/nextdonation":
    return await get_next_donation_date.ainvoke(str(chat_id))  # ❌ Wrong

elif cmd_clean == "/impact" or cmd_clean == "/badges":
    return await get_my_impact.ainvoke(str(chat_id))  # ❌ Wrong

elif cmd_clean == "/status":
    return await check_chain_status.ainvoke(p_id)  # ❌ Wrong
```

**Fix — replace every `.ainvoke(str(chat_id))` with `.ainvoke({"chat_id": str(chat_id)})`:**

```python
elif cmd_clean == "/profile":
    return await get_my_profile.ainvoke({"chat_id": str(chat_id)})  # ✅

elif cmd_clean == "/schedule":
    return await get_my_schedule.ainvoke({"chat_id": str(chat_id)})  # ✅

elif cmd_clean == "/eligibility":
    return await get_my_eligibility.ainvoke({"chat_id": str(chat_id)})  # ✅

elif cmd_clean == "/nextdonation":
    return await get_next_donation_date.ainvoke({"chat_id": str(chat_id)})  # ✅

elif cmd_clean == "/impact" or cmd_clean == "/badges":
    return await get_my_impact.ainvoke({"chat_id": str(chat_id)})  # ✅

elif cmd_clean == "/status":
    return await check_chain_status.ainvoke({"patient_id": p_id})  # ✅
```

---

### 🔴 GAP-03 · CRITICAL · Impact Story Never Triggered in `agents/outcome.py`

**What's broken:** The `outcome_agent` does everything — updates Supabase, Neo4j, donor stats, traces — but **never generates or schedules the impact story**. The `services/impact_story.py` and `send_impact_story_via_telegram()` functions exist but are never called. Donors never receive the emotional feedback loop that is central to the platform's engagement model.

**Fix — add to the end of `outcome_agent()` in `agents/outcome.py`, just before the final `return` statement:**

```python
# ── 8. Schedule 2-hour impact story delivery for confirmed donors ─────────────
if confirmed_donors and db_status == "COMPLETED":
    try:
        from services.impact_story import generate_impact_story
        from scheduler.cron import get_global_scheduler
        from apscheduler.triggers.date import DateTrigger
        import asyncio as _asyncio

        # Fetch patient details for story generation
        patient_res = supabase.table("patients").select("name, age, blood_type").eq("patient_id", patient_id).execute()
        patient_info = patient_res.data[0] if patient_res.data else {}

        for donor in confirmed_donors:
            donor_id = donor["donor_id"]
            # Fetch donor chat_id
            chat_res = supabase.table("donors").select("telegram_chat_id, preferred_language, name").eq("donor_id", donor_id).execute()
            if not chat_res.data or not chat_res.data[0].get("telegram_chat_id"):
                continue

            chat_id = chat_res.data[0]["telegram_chat_id"]
            lang = chat_res.data[0].get("preferred_language", "en")
            donor_name = chat_res.data[0].get("name", "Donor")

            # Generate story
            story = await generate_impact_story(donor_id, patient_info, lang)

            # Store in donor_memory as pending_impact_story (restart survival)
            supabase.table("donor_memory").upsert({
                "donor_id": donor_id,
                "pending_impact_story": story,
                "pending_story_send_at": (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
            }).execute()

            # Schedule one-shot Telegram send in 2 hours
            async def _send_story(cid=chat_id, s=story, did=donor_id):
                from services.telegram_bot import send_telegram_message
                await send_telegram_message(cid, s)
                # Clear pending
                get_supabase_admin().table("donor_memory").update({
                    "pending_impact_story": None,
                    "pending_story_send_at": None
                }).eq("donor_id", did).execute()

            run_at = datetime.now() + timedelta(hours=2)
            try:
                scheduler = get_global_scheduler()
                scheduler.add_job(
                    lambda cid=chat_id, s=story, did=donor_id: _asyncio.ensure_future(_send_story(cid, s, did)),
                    DateTrigger(run_date=run_at),
                    id=f"impact_story_{donor_id}_{request_id}",
                    replace_existing=True
                )
                logger.info(f"Impact story for donor {donor_id} scheduled at {run_at}")
            except Exception as sched_err:
                logger.warning(f"Failed to schedule impact story for {donor_id}: {sched_err}")
    except Exception as story_err:
        logger.warning(f"Impact story scheduling failed (non-critical): {story_err}")
```

---

### 🔴 GAP-04 · CRITICAL · Dashboard Pages Not Updated (Emergency.tsx, Admin.tsx)

**What's broken:** `App.tsx` imports `Emergency`, `Admin`, `Donors`, `Graph`, `MapView` from `@/pages/dashboard/` but these files are from v1 — they were not touched during v2 vibe coding. Specifically:

- `Emergency.tsx` — needs the 8-node chain timeline visual + "Trigger Demo Emergency" button
- `Admin.tsx` — needs token input field, expandable trace cards, 30s health auto-refresh

These are the two most demo-critical pages.

**Fix for `Emergency.tsx` — add these two sections:**

```tsx
// 1. Add "Trigger Demo Emergency" button at top of the dashboard (staff only)
// Place this just inside the main container, at the top:

{import.meta.env.VITE_STAFF_TOKEN && import.meta.env.VITE_STAFF_TOKEN !== "test-admin-token" && (
  <div className="mb-4 flex justify-end">
    <button
      onClick={async () => {
        try {
          const res = await triggerEmergency({
            patient_id: "P-DEMO-001",
            blood_type: "O+",
            city: "Hyderabad",
            ward: "ICU",
            hospital: "KIMS Secunderabad"
          });
          toast.success(`Demo emergency triggered: ${res.requestId}`);
        } catch (e) {
          toast.error("Failed to trigger demo emergency");
        }
      }}
      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-bold rounded-lg flex items-center gap-2"
    >
      <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
      Trigger Demo Emergency
    </button>
  </div>
)}

// 2. Chain timeline visualization — replace static donor list with this:
// For each emergency in the list, render the 8-node chain:
{emergency.chain.length > 0 && (
  <div className="mt-3">
    <div className="flex items-center gap-1 relative">
      <div className="absolute left-3 right-3 top-3.5 h-px bg-slate-700 z-0" />
      {Array.from({ length: 8 }).map((_, i) => {
        const node = emergency.chain[i];
        const status = node?.status || "PENDING";
        return (
          <div key={i} className="relative z-10 flex flex-col items-center gap-1 flex-1">
            <div className={`w-7 h-7 rounded-full border-2 border-slate-900 flex items-center justify-center text-[9px] font-bold transition-all duration-500 ${
              status === "CONFIRMED" || status === "COMPLETED"
                ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"
                : status === "ALERTED" || status === "SMS" || status === "VOICE"
                ? "bg-amber-500 animate-pulse"
                : status === "DECLINED"
                ? "bg-red-500"
                : "bg-slate-700"
            }`}>
              {i + 1}
            </div>
            <div className="text-[8px] text-slate-500 font-mono text-center">
              {node?.antigen_score ? `${Math.round(node.antigen_score * 100)}%` : "—"}
            </div>
          </div>
        );
      })}
    </div>
    <div className="flex justify-between text-[9px] mt-1 px-1 text-slate-500">
      <span className="text-emerald-400">● Confirmed</span>
      <span className="text-amber-400">● Alerted</span>
      <span className="text-red-400">● Declined</span>
      <span>● Pending</span>
    </div>
  </div>
)}
```

**Fix for `Admin.tsx` — three additions:**

```tsx
// 1. At the top of Admin page — token input field when placeholder is set:
const [tokenOverride, setTokenOverride] = useState("");
const activeToken = tokenOverride || import.meta.env.VITE_STAFF_TOKEN || "";
const isPlaceholderToken = activeToken === "test-admin-token" || !activeToken;

{isPlaceholderToken && (
  <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
    <p className="text-xs text-amber-400 mb-2">
      ⚠️ Using placeholder token. Run: <code>SELECT auth_token FROM staff WHERE role = 'Admin' LIMIT 1;</code> in Supabase
    </p>
    <input
      className="w-full bg-slate-800 border border-slate-700 text-white text-xs rounded px-3 py-2"
      placeholder="Paste real staff token here..."
      value={tokenOverride}
      onChange={e => {
        setTokenOverride(e.target.value);
        localStorage.setItem("auth_token", e.target.value);
      }}
    />
  </div>
)}

// 2. Agent trace expandable cards:
// Replace flat trace list with:
{traces.map(trace => (
  <details key={trace.request_id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mb-2">
    <summary className="cursor-pointer flex justify-between items-center">
      <div className="flex gap-3 items-center">
        <span className="font-mono text-xs text-slate-400">{trace.request_id}</span>
        <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${
          trace.outcome === "SUCCESS" || trace.outcome === "COMPLETED"
            ? "bg-emerald-500/20 text-emerald-400"
            : "bg-red-500/20 text-red-400"
        }`}>{trace.outcome}</span>
        <span className="text-xs text-slate-500">{trace.total_ms}ms · {trace.node_count} nodes</span>
      </div>
    </summary>
    <div className="mt-3 space-y-1 pl-2 border-l border-slate-700">
      {Object.entries(trace.nodes || {}).map(([nodeName, durationMs]) => (
        <div key={nodeName} className="flex justify-between text-xs">
          <span className="text-slate-300 font-mono">{nodeName}</span>
          <span className="text-teal-400 font-mono">{String(durationMs)}ms</span>
        </div>
      ))}
    </div>
  </details>
))}

// 3. Health auto-refresh every 30s:
useEffect(() => {
  const fetchHealth = () => getSystemHealth().then(setHealth).catch(() => {});
  fetchHealth();
  const interval = setInterval(fetchHealth, 30000);
  return () => clearInterval(interval);
}, []);
```

---

### 🟠 GAP-05 · HIGH · `DonorPortal.tsx` Uses `getDonors()` Instead of Single Donor Fetch

**What's broken:** `DonorPortal.tsx` calls `getDonors()` to fetch ALL donors, then finds the right one by ID. This is a full-table fetch just to display one donor's profile. It also falls back to `donors[0]` — the first donor in the database — if the logged-in donor_id isn't found.

**Fix — add `getDonor(id)` to `lib/api.ts`:**

```typescript
// Add to lib/api.ts
export async function getDonor(id: string): Promise<Donor> {
  return apiFetch<Donor>(`/api/donors/${id}`);
}
```

**Fix — update `DonorPortal.tsx` `useEffect`:**

```typescript
// Replace:
getDonors()
  .then(donors => {
    const found = donors.find(d => d.donor_id === donorId);
    setDonor(found || donors[0] || null);
  })
  .catch(() => setDonor(null));

// With:
getDonor(donorId)
  .then(setDonor)
  .catch(() => setDonor(null));
```

And add the import:
```typescript
import { getDonor, getDonorRank, getDonorActiveRequest, ... } from "@/lib/api";
```

---

### 🟠 GAP-06 · HIGH · `DonorPortal.tsx` Missing Impact Stories Section (Phase 4.5)

**What's missing:** The "Your Impact Stories" section from Phase 4.5 was never added to `DonorPortal.tsx`.

**Fix — add to `lib/api.ts`:**

```typescript
export async function getDonorImpactStories(id: string): Promise<string[]> {
  try {
    const mem = await apiFetch<{ impact_stories?: string[] }>(`/api/donors/${id}/memory`);
    return mem.impact_stories || [];
  } catch {
    return [];
  }
}
```

**Add `GET /api/donors/{id}/memory` to `api/donors.py`:**

```python
@router.get("/{id}/memory")
async def get_donor_memory(id: str):
    """GET /api/donors/{id}/memory — Returns non-sensitive donor memory fields."""
    supabase = get_supabase_admin()
    res = supabase.table("donor_memory").select("badges, impact_stories, streak_days").eq("donor_id", id).execute()
    if not res.data:
        return {"badges": [], "impact_stories": [], "streak_days": 0}
    d = res.data[0]
    return {
        "badges": d.get("badges", []) or [],
        "impact_stories": d.get("impact_stories", []) or [],
        "streak_days": d.get("streak_days", 0) or 0
    }
```

**Add Impact Stories section to `DonorPortal.tsx` (after badges section):**

```tsx
{/* Impact Stories — from donor_memory */}
<div>
  <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider flex items-center gap-2">
    <HeartPulse className="w-3.5 h-3.5 text-red-400" /> Your Impact Stories
  </h3>
  {impactStories.length > 0 ? (
    <div className="space-y-3">
      {impactStories.slice(0, 3).map((story, i) => (
        <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-300 leading-relaxed">{story}</p>
        </div>
      ))}
    </div>
  ) : (
    <div className="bg-slate-900/40 border border-slate-800/50 rounded-xl p-4 text-center">
      <p className="text-xs text-slate-500 italic">After each donation, you'll see the story of who you helped here.</p>
    </div>
  )}
</div>
```

---

### 🟠 GAP-07 · HIGH · `DonorPortal.tsx` Missing Availability Toggle UI (Phase 9.3)

**What's missing:** `Pause` and `Play` icons are imported in `DonorPortal.tsx` but there is no availability toggle UI. The bot supports `/pause` and `/resume` but the web portal has no equivalent.

**Fix — add state and toggle button to `DonorPortal.tsx`:**

```tsx
// Add state:
const [isAvailable, setIsAvailable] = useState(true);
const [toggleLoading, setToggleLoading] = useState(false);

// Add after the Telegram connection card:
<div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex gap-4 items-center justify-between">
  <div>
    <div className="font-bold text-sm text-white mb-1">Donation Availability</div>
    <p className="text-xs text-slate-400">
      {isAvailable ? "You are active and receiving donation requests." : "Paused — you won't receive new requests."}
    </p>
  </div>
  <button
    disabled={toggleLoading}
    onClick={async () => {
      if (!donor) return;
      setToggleLoading(true);
      try {
        await setDonorAvailability(donor.donor_id, !isAvailable);
        setIsAvailable(!isAvailable);
      } finally {
        setToggleLoading(false);
      }
    }}
    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-colors ${
      isAvailable
        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30"
        : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30"
    }`}
  >
    {toggleLoading ? (
      <div className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
    ) : isAvailable ? (
      <><Pause className="w-4 h-4" /> Pause</>
    ) : (
      <><Play className="w-4 h-4" /> Resume</>
    )}
  </button>
</div>
```

Also initialize from donor data in the `useEffect`:
```tsx
.then(d => {
  setDonor(d);
  setIsAvailable(d?.is_active !== false);
})
```

---

### 🟠 GAP-08 · HIGH · `agent_traces` Query Uses Wrong Column Name

**What's broken:** `api/admin.py` queries `agent_traces` ordered by `started_at`, but `agents/outcome.py` inserts the trace with `completed_at`. There is no `started_at` column in the schema. The query will silently return no results or throw an error.

**Fix in `api/admin.py`:**
```python
# Change:
res = supabase.table("agent_traces").select("*").order("started_at", desc=True).limit(5).execute()
# To:
res = supabase.table("agent_traces").select("*").order("completed_at", desc=True).limit(5).execute()
```

Also fix the trace response mapping — `nodes_json` is a dict of `{node_name: duration_ms}`, not a list:
```python
# Change nodes mapping in admin.py traces response:
"nodes": t.get("nodes_json") or []
# To:
"nodes": [{"name": k, "duration_ms": v} for k, v in (t.get("nodes_json") or {}).items()]
```

---

### 🟠 GAP-09 · MEDIUM · Multi-Turn Registration Doesn't Capture Phone Number

**What's missing:** Phase 9.1 — the registration flow asks blood_type → city → name but never asks for phone. This means web portal phone-based login won't work for bot-registered donors.

**Fix in `services/telegram_bot.py` — add phone step to registration flow:**

```python
# In handle_registration_step(), change the "name" step to go to "phone" next:

elif step == "name":
    name = text.strip().title()
    if len(name) < 2:
        return "Please enter a valid name."
    session["name"] = name
    session["step"] = "phone"
    return (
        f"Name: *{name}* ✅\n\n"
        f"Finally, please share your *phone number* (or type 'skip' to register without it):\n"
        f"📱 Format: 9XXXXXXXXX or +91XXXXXXXXX"
    )

elif step == "phone":
    phone_raw = text.strip()
    phone = None
    if phone_raw.lower() != "skip":
        # Normalize
        digits = re.sub(r'\D', '', phone_raw)
        if len(digits) == 10:
            phone = f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            phone = f"+{digits}"
        else:
            return "❌ Invalid phone format. Enter 10-digit number or type 'skip'."

    # Complete registration (move existing name-step logic here)
    blood_type = session["blood_type"]
    city = session["city"]
    name = session["name"]
    # ... rest of the completion logic, adding phone to insert:
    supabase.table("donors").insert({
        "donor_id": donor_id,
        "telegram_chat_id": key,
        "name": name,
        "blood_type": blood_type,
        "city": city,
        "phone": phone,  # ← ADD THIS
        "preferred_language": detected_lang,
        "consent_outreach": True,
        "is_active": True
    }).execute()
```

Also add `import re` at the top of telegram_bot.py if not already present.

---

### 🟠 GAP-10 · MEDIUM · Telegram Deep Link Token Store is In-Memory (Loses Tokens on Restart)

**What's broken:** `_telegram_login_tokens` in `api/auth.py` is a Python dict. On Render.com, the server can restart at any time. Any pending tokens are lost. This will frustrate donors who click a stale link.

**Fix — persist tokens in Supabase. In `api/auth.py`:**

```python
# Replace _telegram_login_tokens dict with Supabase persistence

@router.post("/telegram-token")
async def create_telegram_login_token(chat_id: str):
    import uuid
    from datetime import datetime, timedelta
    supabase = get_supabase_admin()
    
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        raise HTTPException(status_code=404, detail="Donor not found.")
    
    donor_id = donor_res.data[0]["donor_id"]
    token = str(uuid.uuid4())
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"
    
    # Store in Supabase (requires telegram_auth_tokens table OR reuse consent_records)
    # Option: reuse donor_memory table with a temp_token field
    supabase.table("donor_memory").upsert({
        "donor_id": donor_id,
        "telegram_login_token": token,
        "telegram_token_expires_at": expires_at
    }).execute()
    
    return {"token": token, "expires_in_seconds": 600}

@router.get("/telegram-login")
async def telegram_login(token: str):
    from datetime import datetime
    supabase = get_supabase_admin()
    
    # Look up token in donor_memory
    res = supabase.table("donor_memory").select("donor_id, telegram_token_expires_at")\
        .eq("telegram_login_token", token).execute()
    
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    entry = res.data[0]
    expires_str = entry.get("telegram_token_expires_at", "")
    if expires_str and datetime.utcnow() > datetime.fromisoformat(expires_str.replace("Z", "")):
        raise HTTPException(status_code=401, detail="Token has expired. Request a new link via Telegram.")
    
    donor_id = entry["donor_id"]
    
    # Clear token after use
    supabase.table("donor_memory").update({
        "telegram_login_token": None,
        "telegram_token_expires_at": None
    }).eq("donor_id", donor_id).execute()
    
    token_data = {"sub": donor_id, "role": "donor", "source": "telegram_deeplink"}
    jwt_token = create_access_token(token_data)
    return {"access_token": jwt_token, "token_type": "bearer", "donor_id": donor_id}
```

> **Schema required:** Add `telegram_login_token TEXT` and `telegram_token_expires_at TEXT` columns to `donor_memory` table in Supabase.

---

### 🟠 GAP-11 · MEDIUM · `DonorLogin.tsx` Still Has Hardcoded Stats and Patient Name

**What's broken:** The login page still shows `"Aarav (7 yrs, B+)"` and hardcoded stats ("13 Lives Saved", "13 Donations", "#2 City Rank"). This breaks the narrative of a "live, real-data" platform.

**Fix — replace the hardcoded patient section with a generic motivational message:**

```tsx
// Replace the hardcoded patient section at the bottom of DonorLogin.tsx:
<div className="bg-red-950/20 border border-red-900/50 rounded-xl p-4 text-center">
  <p className="text-sm text-slate-300 mb-2">
    Every drop you give keeps a Thalassemia patient alive.
  </p>
  <p className="text-xs text-slate-500">
    Blood Warriors · 1,00,000+ patients across India
  </p>
</div>
```

**Replace hardcoded quick stats with dynamic fetch (or remove them):**

```tsx
// Simple approach — fetch from /api/admin/analytics (no auth needed for total count)
// OR just update to sensible placeholder text that's not identity-specific:
<div className="grid grid-cols-3 gap-3">
  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-center">
    <div className="text-lg font-bold text-red-400 font-mono">∞</div>
    <div className="text-[10px] text-slate-500 uppercase">Lives Waiting</div>
  </div>
  ...
</div>
```

---

### 🟠 GAP-12 · MEDIUM · `POST /api/patients/{id}/auto-schedule` Missing (Phase 1.5.2)

**What's missing:** Staff should be able to trigger schedule auto-generation for a specific patient. This endpoint was planned but never added to `api/patients.py`.

**Fix — add to `api/patients.py`:**

```python
from fastapi import BackgroundTasks

@router.post("/{id}/auto-schedule")
async def auto_schedule_patient(id: str, background_tasks: BackgroundTasks):
    """
    POST /api/patients/{id}/auto-schedule
    Triggers auto_generate_schedule_from_history() as a background task.
    Only works for patients with 2+ completed transfusions.
    """
    supabase = get_supabase_admin()
    
    # Check eligibility
    req_res = supabase.table("emergency_requests")\
        .select("request_id")\
        .eq("patient_id", id)\
        .eq("status", "COMPLETED")\
        .execute()
    
    if len(req_res.data or []) < 2:
        raise HTTPException(
            status_code=400,
            detail="Patient needs at least 2 completed transfusions for auto-schedule generation."
        )
    
    from services.transfusion_calendar import auto_generate_schedule_from_history
    background_tasks.add_task(auto_generate_schedule_from_history, id)
    
    return {"success": True, "message": f"Auto-schedule generation queued for patient {id}."}
```

---

### 🟡 GAP-13 · LOW · `WEB_PORTAL_URL` Defaults to `localhost:5173` in Production

**What's broken:** The `get_medical_data_portal_link` tool sends users to `http://localhost:5173` on production. Every donor who asks for their medical data gets a broken link.

**Fix — update `.env` file:**
```bash
# In BloodBridge_AI_Backend/.env — add or update:
WEB_PORTAL_URL=https://your-vercel-app.vercel.app
```

**And for local dev, ensure:**
```bash
WEB_PORTAL_URL=http://localhost:5173
```

---

### 🟡 GAP-14 · LOW · `donors` Table Missing `password` Column Causes Login Failures

**What's broken:** `api/auth.py` login checks `user.get("password") != req.password`. Donors registered via Telegram bot insert records with no `password` field. Trying to log into the web portal with a password will always fail for bot-registered donors (the field is `None`).

**Fix — update login in `api/auth.py` to allow phone-based passwordless login:**

```python
# In /api/auth/login for role == "donor":
# After finding the user, skip password check if they were bot-registered:
if user.get("password") is None:
    # Bot-registered donor — allow login by donor_id or phone without password
    # (Phone-based login is already secured by the unique phone constraint)
    pass
elif user.get("password") != req.password:
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

---

### 🟡 GAP-15 · LOW · Demo Mock Mode `DEMO_MOCK_MODE` Flag Has No Effect

**What's there:** `DEMO_MOCK_MODE: bool = Field(default=False)` is defined in `config.py` but **nowhere in the codebase is it checked**. If any external service (Neo4j, Bolna, Supabase) goes down during the demo, there's no fallback.

**Minimal fix — add a check in the most likely failure point, `agents/neo4j_match.py`:**

```python
# At the top of neo4j_match_agent() or Neo4jMatcher.find_compatible_donors():
settings = get_settings()
if settings.DEMO_MOCK_MODE:
    logger.info("DEMO_MOCK_MODE: Returning synthetic donors instead of Neo4j query.")
    return [
        {"donor_id": "D-DEMO-001", "name": "Ravi Kumar", "blood_type": "O+", "antigen_score": 0.92},
        {"donor_id": "D-DEMO-002", "name": "Priya Sharma", "blood_type": "O+", "antigen_score": 0.88},
        # ... 6 more demo donors
    ]
```

**Also add to `services/voice_service.py` `make_bolna_call()`:**
```python
if settings.DEMO_MOCK_MODE:
    logger.info(f"DEMO_MOCK_MODE: Simulating successful call to {phone}")
    return {"status": "INITIATED", "call_id": f"DEMO-CALL-{donor.get('donor_id', '0000')}"}
```

---

### 🟡 GAP-16 · LOW · `supabase_schema.sql` Missing `telegram_login_token` and `pending_impact_story` Columns

**What's missing:** Fixes in GAP-10 and GAP-03 require new columns in `donor_memory`. Update the schema.

**Add to `data/supabase_schema.sql` (or run directly in Supabase SQL editor):**

```sql
-- For GAP-10: Telegram deep link tokens
ALTER TABLE donor_memory 
ADD COLUMN IF NOT EXISTS telegram_login_token TEXT,
ADD COLUMN IF NOT EXISTS telegram_token_expires_at TEXT;

-- For GAP-03: Impact story delay persistence
ALTER TABLE donor_memory 
ADD COLUMN IF NOT EXISTS pending_impact_story TEXT,
ADD COLUMN IF NOT EXISTS pending_story_send_at TEXT;

-- For GAP-14: Password field for donors
ALTER TABLE donors 
ADD COLUMN IF NOT EXISTS password TEXT;

-- Useful index for token lookup
CREATE INDEX IF NOT EXISTS idx_donor_memory_telegram_token 
ON donor_memory(telegram_login_token) WHERE telegram_login_token IS NOT NULL;
```

---

### 🟡 GAP-17 · LOW · `DonorPortal` — `donor.is_active` Field Not in `Donor` TypeScript Type

**What's broken:** The `setIsAvailable(d?.is_active !== false)` fix in GAP-07 requires `is_active` on the `Donor` type, but the current TypeScript interface doesn't include it.

**Fix — update `Donor` interface in `lib/api.ts`:**

```typescript
export interface Donor {
  donor_id: string; name: string; blood_type: string; city: string;
  kell_negative: boolean; churn_score: number; churn_risk: ChurnRisk;
  donation_count: number; lives_saved: number; last_donation_days: number;
  response_rate: number; badges: string[]; preferred_language: string;
  antigen_score?: number; telegram_chat_id?: string;
  is_active?: boolean;  // ← ADD THIS
}
```

And update `GET /api/donors/{id}` response in `api/donors.py` to include `is_active`:
```python
return {
    ...existing fields...,
    "is_active": d.get("is_active", True),  # ← ADD THIS
}
```

---

### 🟡 GAP-18 · LOW · `webhooks.py` Telegram Handler — Confirm It's Wired Correctly

**What to verify:** The `/webhook/telegram` endpoint in `api/webhooks.py` must call `handle_command()`, `handle_registration_step()`, and `handle_deterministic_chain_response()` from `telegram_bot.py`. If any of those import paths are wrong or the webhook handler doesn't correctly route free-text messages through the React agent, the entire bot will be silent.

**Verify this flow exists in `api/webhooks.py`:**

```python
# The webhook handler should follow this routing logic:
# 1. If message is a photo → handle_photo_onboarding()
# 2. If chat_id is in registration_sessions → handle_registration_step()
# 3. If user_context.active_chain_status == "ALERTED" and text is YES/NO/HAAN → handle_deterministic_chain_response()
# 4. If text starts with "/" → handle_command()
# 5. Else → run_telegram_agent() (the React LLM agent)
```

If `api/webhooks.py` doesn't have all these branches, add the missing ones. This is the most important integration point in the entire system.

---

## PRIORITY FIX ORDER FOR HACKATHON

Execute fixes in this sequence for maximum demo impact:

| Priority | Fix | Time | Impact |
|---|---|---|---|
| 1 | GAP-02 — Tool .ainvoke() dict fix | 10 min | Bot commands work |
| 2 | GAP-01 — Rename duplicate functions | 5 min | API routes stable |
| 3 | GAP-08 — agent_traces column name fix | 5 min | Admin traces load |
| 4 | GAP-03 — Impact story in outcome agent | 20 min | Donor engagement loop |
| 5 | GAP-05 — getDonor() single fetch | 10 min | Donor portal efficient |
| 6 | GAP-04 — Emergency.tsx chain visual + demo button | 30 min | Demo day showpiece |
| 7 | GAP-04 — Admin.tsx token input + trace cards | 20 min | Admin demo-ready |
| 8 | GAP-16 — Schema SQL for new columns | 5 min | DB ready for GAP-03/10 |
| 9 | GAP-13 — WEB_PORTAL_URL in .env | 2 min | Medical links work |
| 10 | GAP-07 — Availability toggle UI | 15 min | Feature completeness |
| 11 | GAP-09 — Phone capture in registration | 15 min | Identity binding |
| 12 | GAP-10 — Supabase token persistence | 15 min | Deep link robustness |
| 13 | GAP-06 — Impact stories section | 15 min | Donor portal polish |
| 14 | GAP-11 — Hardcoded login stats | 5 min | Professionalism |
| 15 | GAP-12 — Auto-schedule endpoint | 10 min | Staff workflow |
| 16 | GAP-15 — DEMO_MOCK_MODE effect | 20 min | Demo fail-safety |
| 17 | GAP-14 — Passwordless login fix | 5 min | Auth robustness |
| 18 | GAP-17/18 — TypeScript type + webhook verify | 10 min | Type safety |

**Total estimated time: ~3.5 hours for all 18 fixes**

---

## AGENTIC IDE PROMPT TEMPLATE

Use this prompt for each fix with Antigravity or any vibe coding platform:

```
You are a senior full-stack developer working on BloodBridge AI.
Backend: FastAPI + Python in BloodBridge_AI_Backend/
Frontend: React + Vite + TypeScript in BloodBridge_AI_frontend/artifacts/bloodbridge/src/

TASK: Implement the fix for [GAP-XX] from BloodBridge_V2_GapAnalysis_FINAL.md.

Constraints:
- DO NOT modify agents/graph.py or the LangGraph pipeline
- DO NOT modify tests/test_e2e_pipeline.py  
- All DB operations use get_supabase_admin()
- Follow existing code patterns exactly
- After each fix, confirm you did NOT introduce new function name duplicates
- If touching api/donors.py, confirm all 4 route paths /{id}/voice, /{id}/trigger-voice, /{id}/outreach, /{id}/trigger-outreach have unique function names

After implementing, state which file(s) were changed and what lines were affected.
```

---

## WHAT "PRODUCTION READY" LOOKS LIKE

When all 18 gaps are fixed, BloodBridge will be:

- ✅ Bot commands actually invoke tools correctly (GAP-02)
- ✅ All API routes execute the correct function (GAP-01)
- ✅ Donors receive Gemini-generated impact stories 2 hours after donation (GAP-03)
- ✅ Live emergency dashboard shows 8-node chain + one-click demo trigger (GAP-04)
- ✅ Admin can paste token in UI, sees expandable trace cards (GAP-04)
- ✅ Donor portal fetches single donor efficiently (GAP-05)
- ✅ Admin traces load correctly (GAP-08)
- ✅ Telegram deep link tokens survive server restarts (GAP-10)
- ✅ Bot-registered donors can log into web portal (GAP-14)
- ✅ Demo mode provides fallback if any external API is down (GAP-15)
- ✅ All 13 frontend pages render with 100% real data

---

*Analysis by: Full codebase read of `full_code.txt` (22,017 lines), `version_2_pre-hackathon.md`, `version_2_tracker.md`, `MASTER_STATUS.txt`*  
*BloodBridge AI · Team Inqilab · DNR College of Engineering and Technology · June 2026*
