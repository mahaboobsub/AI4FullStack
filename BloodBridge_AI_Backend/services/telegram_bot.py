"""
Agentic Telegram Bot Service for BloodBridge AI.
Implements tool-calling with Groq/LangGraph, hybrid routing, security checks, and OCR integrations.
V2: 10+ tools, multi-turn registration, language-first responses, DPDP medical data gate.
"""
import asyncio
import logging
import random
import hashlib
from datetime import datetime, timezone, date, timedelta
from typing import List, Dict, Any, Optional
from io import BytesIO

from telegram import Bot, Update
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from core.llm_provider import get_fast_llm
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from core.config import get_settings
from core.database import get_supabase_admin
from core.neo4j_client import get_driver
from api.websocket import ws_manager
import services.consent_service as consent_service

logger = logging.getLogger(__name__)

KNOWN_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

# ── Multi-turn registration session state ──────────────────────────────────────
# In-memory store keyed by chat_id. Each session tracks the registration flow step.
registration_sessions: Dict[str, Dict[str, Any]] = {}

# Sensitive fields that must NOT be sent via Telegram (DPDP 2023)
SENSITIVE_FIELDS = {
    "phone", "antibody_flags", "antibody_kell", "antibody_duffy", "antibody_kidd",
    "antibody_rh_e", "antibody_rh_c", "antibody_mns", "antigen_data", "antigen_score",
    "hemoglobin", "kell_negative", "duffy_negative", "kidd_negative",
    "medical_hold", "medical_hold_until", "medical_hold_reason"
}

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi (हिन्दी)", "te": "Telugu (తెలుగు)",
    "ta": "Tamil (தமிழ்)", "kn": "Kannada (ಕನ್ನಡ)", "ml": "Malayalam (മലയാളം)",
    "mr": "Marathi (मराठी)", "bn": "Bengali (বাংলা)", "gu": "Gujarati (ગુજરાતી)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)"
}

async def get_user_context(chat_id: str) -> dict:
    """Fetch role, language, name, and active alerted chain node for a given chat_id.
    V2: Strips sensitive clinical fields from donor_profile before returning."""
    supabase = get_supabase_admin()
    
    # 1. Staff check
    staff_res = supabase.table("staff").select("*").eq("telegram_chat_id", str(chat_id)).execute()
    if staff_res.data:
        s = staff_res.data[0]
        return {
            "role": s["role"],
            "name": s["telegram_username"],
            "lang": "en",
            "chat_id": chat_id,
            "active_chain_status": "NONE"
        }
        
    # 2. Donor check
    donor_res = supabase.table("donors").select("*").eq("telegram_chat_id", str(chat_id)).execute()
    if donor_res.data:
        d = donor_res.data[0]
        donor_id = d["donor_id"]
        
        # Check active alerted chain
        chain_res = supabase.table("blood_chains")\
            .select("*")\
            .eq("donor_id", donor_id)\
            .eq("status", "ALERTED")\
            .execute()
            
        active_node = chain_res.data[0] if chain_res.data else None

        # Strip sensitive fields from donor profile before passing to LLM (DPDP gate)
        safe_profile = {k: v for k, v in d.items() if k not in SENSITIVE_FIELDS}
        
        return {
            "role": "Donor",
            "donor_id": donor_id,
            "name": d["name"],
            "lang": d.get("preferred_language", "en"),
            "chat_id": chat_id,
            "active_chain_status": "ALERTED" if active_node else "NONE",
            "active_node": active_node,
            "donor_profile": safe_profile
        }
        
    return {
        "role": "Guest",
        "name": "Guest",
        "lang": "en",
        "chat_id": chat_id,
        "active_chain_status": "NONE"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT TOOLS DEFINITION (Original 3 + 7 New)
# ═══════════════════════════════════════════════════════════════════════════════

class EmergencyInput(BaseModel):
    blood_type: str = Field(description="Blood type needed, e.g., B+, O-")
    hospital: str = Field(description="Hospital name, e.g., KIMS Secunderabad")
    patient_id: str = Field(description="Patient ID, e.g., P-10234")
    city: str = Field(description="City name, e.g., Hyderabad")
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")

@tool(args_schema=EmergencyInput)
async def trigger_blood_emergency(blood_type: str, hospital: str, patient_id: str, city: str, chat_id: str) -> str:
    """Use this tool ONLY when an authorized hospital staff member requests an emergency blood transfusion.
    This will autonomously trigger the 8-donor matching pipeline in the background."""
    supabase = get_supabase_admin()
    
    # 1. Verify user role is 'Staff' or 'Admin' (check staff table via telegram_chat_id)
    res = supabase.table("staff").select("role, is_active").eq("telegram_chat_id", chat_id).execute()
    if not res.data or not res.data[0].get("is_active", True):
        return "❌ Error: Unauthorized. You are not registered as active Staff/Admin. Emergency request denied."
        
    role = res.data[0].get("role")
    if role not in ["Staff", "Admin", "Coordinator"]:
        return "❌ Error: Unauthorized role. Registered Staff or Admin role required."
        
    # Check duplicate emergency
    from core.security import generate_idempotency_key
    idem_key = generate_idempotency_key(patient_id, blood_type, city)
    dup_res = supabase.table("emergency_requests")\
        .select("request_id")\
        .eq("idempotency_key", idem_key)\
        .eq("status", "IN_PROGRESS")\
        .execute()
        
    if dup_res.data:
        return f"⚠️ Duplicate warning: This emergency is already active (Request ID: {dup_res.data[0]['request_id']}). Spamming is blocked."
        
    # Trigger pipeline as background task
    import random
    req_id = f"REQ-{random.randint(10000, 99999)}"
    
    from agents.graph import run_emergency_pipeline
    asyncio.create_task(run_emergency_pipeline({
        "request_id": req_id,
        "patient_id": patient_id,
        "blood_type": blood_type,
        "city": city,
        "hospital_name": hospital,
        "request_mode": "emergency",
        "triggered_by": f"staff_bot_{chat_id}"
    }))
    
    return f"🚨 Emergency initiated successfully for Patient {patient_id}. 8 donors are being alerted. I will update you as they respond."

class StatusInput(BaseModel):
    patient_id: str = Field(description="Patient ID to check status for")

@tool(args_schema=StatusInput)
async def check_chain_status(patient_id: str) -> str:
    """Use this tool to check the real-time status of a blood donation chain."""
    supabase = get_supabase_admin()
    req_res = supabase.table("emergency_requests")\
        .select("request_id, status")\
        .eq("patient_id", patient_id)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
        
    if not req_res.data:
        return f"No active emergency requests found for patient {patient_id}."
        
    req = req_res.data[0]
    request_id = req["request_id"]
    req_status = req["status"]
    
    chain_res = supabase.table("blood_chains")\
        .select("status")\
        .eq("request_id", request_id)\
        .execute()
        
    chain = chain_res.data or []
    confirmed = sum(1 for d in chain if d["status"] in ["CONFIRMED", "COMPLETED"])
    alerted = sum(1 for d in chain if d["status"] in ["ALERTED", "SMS", "VOICE"])
    declined = sum(1 for d in chain if d["status"] == "DECLINED")
    pending = sum(1 for d in chain if d["status"] == "PENDING")
    
    return (
        f"📊 *Chain Status for Patient {patient_id}* (Request: {request_id})\n"
        f"- Overall Request Status: *{req_status}*\n"
        f"- Confirmed: {confirmed} ✅\n"
        f"- Alerted/Outreached: {alerted} ⏳\n"
        f"- Declined: {declined} ❌\n"
        f"- Pending: {pending} 💤"
    )

class ImpactInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")

@tool(args_schema=ImpactInput)
async def get_my_impact(chat_id: str) -> str:
    """Use this tool when a donor asks about their stats, badges, or lives saved."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id, name, lives_saved, donation_count").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not currently registered as a donor. Please use /register to onboard."
        
    donor = donor_res.data[0]
    donor_id = donor["donor_id"]
    
    from services.donor_memory import get_memory
    mem = await get_memory(donor_id)
    
    badges_str = ", ".join(mem.get("badges", [])) or "None yet! Keep donating to earn badges."
    
    return (
        f"🏆 *Your BloodBridge Impact Profile:*\n\n"
        f"- Donor Name: *{donor['name']}*\n"
        f"- Lives Saved: *{donor['lives_saved']}* 🩸\n"
        f"- Total Donations: *{donor['donation_count']}*\n"
        f"- Current Streak: *{mem.get('streak_days', 0)} days*\n"
        f"- Badges Earned: {badges_str}\n\n"
        f"Thank you for being a vital part of the Blood Warriors community!"
    )


# ═══════════════════════════════════════════════════════════════════════════════

class ChatIdInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")

@tool(args_schema=ChatIdInput)
async def get_donor_profile(chat_id: str) -> str:
    """Use this tool when a donor asks about their profile, their details, or who they are."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("*").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered as a donor yet. Use /register to get started."

    d = donor_res.data[0]
    return (
        f"👤 *Your Profile:*\n"
        f"- Name: *{d.get('name', 'N/A')}*\n"
        f"- Blood Type: *{d.get('blood_type', 'N/A')}*\n"
        f"- City: *{d.get('city', 'N/A')}*\n"
        f"- Donations: *{d.get('donation_count', 0)}*\n"
        f"- Lives Saved: *{d.get('lives_saved', 0)}*\n"
        f"- Status: *{'Active ✅' if d.get('is_active') else 'Inactive ⏸️'}*\n"
    )

@tool(args_schema=ChatIdInput)
async def check_eligibility(chat_id: str) -> str:
    """Use this tool when a donor asks if they are eligible to donate blood."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("*").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered. Use /register to get started."

    donor = donor_res.data[0]
    eligible = True
    reasons = []

    if not donor.get("is_active"):
        eligible = False
        reasons.append("Your profile is currently inactive.")
    if donor.get("medical_hold"):
        eligible = False
        reasons.append(f"You are on medical hold.")

    last_date = donor.get("last_donation_date")
    if last_date:
        from datetime import date, timedelta
        delta = (date.today() - date.fromisoformat(str(last_date))).days
        if delta < 56:
            eligible = False
            reasons.append(f"Only {delta} days since your last donation. You need {56 - delta} more days (56-day minimum).")

    if eligible:
        return "✅ *You are eligible to donate!* Thank you for being ready to save lives. 🩸"
    return f"❌ *Not eligible right now:*\n" + "\n".join(f"- {r}" for r in reasons)

@tool(args_schema=ChatIdInput)
async def get_donation_history(chat_id: str) -> str:
    """Use this tool when a donor asks about their past donations or history."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."

    donor_id = donor_res.data[0]["donor_id"]
    chain_res = supabase.table("blood_chains")\
        .select("request_id, confirmed_at, status")\
        .eq("donor_id", donor_id)\
        .in_("status", ["CONFIRMED", "COMPLETED"])\
        .execute()

    if not chain_res.data:
        return "You haven't made any donations yet."
        
    res = ["Your donation history:"]
    for c in chain_res.data:
        d = c.get('confirmed_at', 'Unknown date')[:10] if c.get('confirmed_at') else 'Unknown date'
        res.append(f"- {d} (Req: {c['request_id']}) - {c['status']}")
    return "\n".join(res)

class AvailabilityInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")
    available: bool = Field(description="True to set available, False to pause")

@tool(args_schema=AvailabilityInput)
async def toggle_availability(chat_id: str, available: bool) -> str:
    """Use this tool when a donor wants to pause or resume their donation availability."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id, name").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."

    donor_id = donor_res.data[0]["donor_id"]
    name = donor_res.data[0]["name"]

    supabase.table("donors").update({"is_active": available, "medical_hold": not available, "medical_hold_until": None}).eq("donor_id", donor_id).execute()
    return f"✅ Availability updated to {'Active' if available else 'Paused'} for {name}."

@tool(args_schema=ChatIdInput)
async def get_badges(chat_id: str) -> str:
    """Use this tool when a donor asks about their badges or achievements."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."
    
    from services.donor_memory import get_memory
    mem = await get_memory(donor_res.data[0]["donor_id"])
    badges = mem.get("badges", [])
    if not badges:
        return "You haven't earned any badges yet. Keep donating to earn NGO engagement badges!"
    return "Your Badges:\n" + "\n".join(f"🏅 {b}" for b in badges)

@tool(args_schema=ChatIdInput)
async def get_leaderboard(chat_id: str) -> str:
    """Use this tool when a donor asks about the city leaderboard or top donors."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("city").eq("telegram_chat_id", chat_id).execute()
    city = donor_res.data[0]["city"] if donor_res.data else "Hyderabad"
    
    res = supabase.table("leaderboard_cache").select("donor_id, lives_saved, rank").eq("city", city).order("rank").limit(10).execute()
    if not res.data:
        return f"No leaderboard data available for {city} right now."
        
    lines = [f"🏆 *Top 10 Donors in {city}:*\n"]
    for row in res.data:
        d_res = supabase.table("donors").select("name").eq("donor_id", row["donor_id"]).execute()
        name = d_res.data[0]["name"] if d_res.data else f"Donor {row['donor_id'][-4:]}"
        lines.append(f"{row['rank']}. {name} - {row['lives_saved']} lives")
    return "\n".join(lines)

@tool(args_schema=ChatIdInput)
async def get_impact_story(chat_id: str) -> str:
    """Use this tool when a donor asks for their impact story or lives saved summary."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."
    from services.donor_memory import get_memory
    mem = await get_memory(donor_res.data[0]["donor_id"])
    story = mem.get("impact_story")
    if story:
        return f"🌟 Your Impact Story:\n\n{story}"
    return "You have saved lives, but your personalized impact story is not generated yet."

@tool(args_schema=ChatIdInput)
async def get_next_donation_date(chat_id: str) -> str:
    """Use this tool when a donor asks when they can next donate blood."""
    supabase = get_supabase_admin()
    from datetime import date, timedelta
    donor_res = supabase.table("donors").select("last_donation_date").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."

    last_date = donor_res.data[0].get("last_donation_date")
    if not last_date:
        return "🩸 You can donate any time! No previous donation recorded."

    next_date = date.fromisoformat(str(last_date)) + timedelta(days=56)
    days_rem = (next_date - date.today()).days
    if days_rem <= 0:
        return "✅ You are already eligible to donate!"
    return f"📅 Your next eligible donation date is *{next_date.isoformat()}* ({days_rem} days from now)."

class MedicalHoldInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")
    days: int = Field(description="Number of days to hold")

@tool(args_schema=MedicalHoldInput)
async def report_medical_hold(chat_id: str, days: int) -> str:
    """Use this tool when a donor reports a medical issue and needs to be placed on hold."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."

    from datetime import date, timedelta
    donor_id = donor_res.data[0]["donor_id"]
    until = (date.today() + timedelta(days=max(1, days))).isoformat()

    # Route through the M5 health-status flow so active chains auto-repair and
    # staff/patient get notified (instead of just flipping the flag).
    try:
        from api.donors import update_health_status, HealthStatusUpdate
        from starlette.background import BackgroundTasks
        bg = BackgroundTasks()
        await update_health_status(
            donor_id,
            HealthStatusUpdate(available=False, reason="reported_via_telegram", hold_until=until),
            bg,
        )
        await bg()  # execute queued repair tasks
    except Exception as e:
        logger.warning(f"report_medical_hold M5 routing failed, falling back to direct update: {e}")
        supabase.table("donors").update(
            {"medical_hold": True, "medical_hold_until": until, "is_active": False}
        ).eq("donor_id", donor_id).execute()

    return f"🏥 You have been placed on medical hold until {until}. We've paused your requests and updated the team. Get well soon! 🙏"

@tool(args_schema=ChatIdInput)
async def get_my_bridge(chat_id: str) -> str:
    """Use this tool when a donor asks about their assigned patient bridge, transfusion dates, or cycle status."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
    if not donor_res.data:
        return "You are not registered."

    donor_id = donor_res.data[0]["donor_id"]
    mem_res = supabase.table("bridge_memberships").select("bridge_id, status").eq("donor_id", donor_id).eq("status", "ACTIVE").execute()
    if not mem_res.data:
        return "You are not currently assigned to any patient bridge."
        
    b_id = mem_res.data[0]["bridge_id"]
    bridge_res = supabase.table("bridges").select("patient_id, next_expected_transfusion").eq("bridge_id", b_id).execute()
    
    if not bridge_res.data:
        return "You are assigned to a bridge, but details are missing."
        
    bridge = bridge_res.data[0]
    return f"🌉 *Your Bridge:*\nYou are actively supporting Patient {bridge['patient_id']}.\nNext expected transfusion date: {bridge.get('next_expected_transfusion', 'Unknown')}.\nYou are currently on-cycle."

from langchain_core.messages import ToolMessage, AIMessage

async def handle_message(chat_id: str, text: str, user_context: dict) -> str:
    """Custom Agentic Loop with Bedrock Nova Lite"""
    try:
        llm = get_fast_llm()
    except Exception as e:
        logger.error(f"Error getting LLM: {e}")
        return "Sorry, I am currently unavailable."
        
    tools = [
        get_donor_profile, check_eligibility, get_donation_history, toggle_availability,
        get_badges, get_leaderboard, get_impact_story, get_next_donation_date, report_medical_hold, get_my_bridge
    ]
    
    llm_with_tools = llm.bind_tools(tools)
    
    from services.donor_memory import get_memory
    donor_id = user_context.get("donor_id")
    mem_context = ""
    if donor_id:
        mem = await get_memory(donor_id)
        anchors = ", ".join(mem.get('emotional_anchors', [])) if mem.get('emotional_anchors') else ""
        badges = ", ".join(mem.get('badges', [])) if mem.get('badges') else ""
        mem_context = f"Tone: {mem.get('tone_profile')}, Anchors: {anchors}, Badges: {badges}, Streak: {mem.get('streak_days')} days."

    system_prompt = f"""You are the BloodBridge AI Assistant. You are an NGO donor assistant — tone is gratitude-first and community-driven.
Use tools when appropriate.
Context:
Role: {user_context.get('role')}
Chat ID: {chat_id}
Preferred Language: {user_context.get('lang', 'en')}
Donor Memory: {mem_context}

RULES:
1. NEVER provide antibody_flags, antigen_scores, hemoglobin_level, kell_negative status, or any clinical diagnostic data via Telegram.
2. Reply in {user_context.get('lang', 'en')} (or the language the user asked in). If the user asks in Hindi, reply in Hindi script.
3. Keep responses under 150 words.
4. Pass exactly `{chat_id}` to the chat_id parameter in all tools. Do not make up a chat_id.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    
    max_steps = 5
    for step in range(max_steps):
        try:
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)
            
            if not response.tool_calls:
                break
                
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                tool_func = {t.name: t for t in tools}.get(tool_name)
                if tool_func:
                    try:
                        tool_res = await tool_func.ainvoke(tool_args)
                    except Exception as e:
                        tool_res = f"Error executing tool: {e}"
                else:
                    tool_res = f"Tool {tool_name} not found"
                    
                messages.append(ToolMessage(content=str(tool_res), tool_call_id=tool_call["id"]))
        except Exception as e:
            logger.error(f"Error in agentic loop: {e}", exc_info=True)
            return "Sorry, an error occurred while processing your request."

    final_reply = response.content if isinstance(response, AIMessage) else str(response)
    
    if donor_id:
        from services.donor_memory import update_memory_after_interaction
        await update_memory_after_interaction(donor_id, "outreach_sent", {})
        
    return final_reply

async def run_repair_in_background(request_id: str, patient_id: str, position: int):
    """Triggers ChainRepairAgent and OutreachAgent in the background."""
    supabase = get_supabase_admin()
    try:
        req_res = supabase.table("emergency_requests").select("*").eq("request_id", request_id).execute()
        if not req_res.data:
            return
        req = req_res.data[0]
        
        p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
        patient = p_res.data[0] if p_res.data else None
        
        bc_res = supabase.table("blood_chains")\
            .select("*")\
            .eq("request_id", request_id)\
            .order("chain_position")\
            .execute()
        db_chain = bc_res.data or []
        
        state = {
            "request_id": request_id,
            "patient_id": patient_id,
            "blood_type": req["blood_type"],
            "city": req["city"],
            "hospital_name": req["hospital_name"],
            "ward": req.get("ward"),
            "triggered_by": req.get("triggered_by", "staff"),
            "request_mode": req.get("request_mode", "emergency"),
            "patient": patient,
            "chain": db_chain,
            "stale_positions": [position],
            "chain_break_detected": True,
            "errors": [],
            "outcome": req["status"],
            "trace_id": f"REPAIR-BG",
            "language": "en"
        }
        
        from agents.repair import chain_repair_agent
        from agents.outreach import outreach_agent
        
        repair_res = await chain_repair_agent(state) # type: ignore
        state.update(repair_res)
        
        if state.get("outreach_plan"):
            logger.info(f"Background Repair: Re-running outreach for request {request_id}...")
            await outreach_agent(state) # type: ignore
    except Exception as e:
        logger.error(f"Error in run_repair_in_background: {e}", exc_info=True)

async def handle_deterministic_chain_response(chat_id: str, user_text: str, user_context: dict):
    """Bypasses LLM for active donor alerted responses to ensure reliability."""
    settings = get_settings()
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
    
    donor_id = user_context["donor_id"]
    active_node = user_context["active_node"]
    request_id = active_node["request_id"]
    pos = active_node["chain_position"]
    text_clean = user_text.lower().strip()

    # Need full donor profile for eligibility check (not the stripped one)
    supabase = get_supabase_admin()
    donor_full_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
    donor_profile = donor_full_res.data[0] if donor_full_res.data else {}
    
    # Resolve patient_id
    req_res = supabase.table("emergency_requests").select("patient_id").eq("request_id", request_id).execute()
    patient_id = req_res.data[0]["patient_id"] if req_res.data else None
    
    is_yes = text_clean in ['yes', 'haan', 'ha', 'ok']
    
    if is_yes:
        # Re-validate eligibility
        p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
        patient = p_res.data[0] if p_res.data else {}
        
        from ml.eligibility_filter import check_donor_eligibility
        elig = check_donor_eligibility(donor_profile, patient)
        
        if not elig["eligible"]:
            reason = elig["reason"]
            msg = f"Thank you! Unfortunately, you are not eligible to donate right now: {reason}."
            if bot:
                await bot.send_message(chat_id=chat_id, text=msg)
            else:
                logger.info(f"Mock Bot message to {chat_id}: {msg}")
                
            # Update status to DECLINED
            supabase.table("blood_chains")\
                .update({
                    "status": "DECLINED", 
                    "notes": f"eligibility_failed_on_confirm: {reason}",
                    "declined_at": datetime.utcnow().isoformat() + "Z"
                })\
                .eq("request_id", request_id)\
                .eq("donor_id", donor_id)\
                .execute()
                
            from agents.neo4j_match import Neo4jMatcher
            await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "DECLINED")
            
            from services.donor_memory import update_memory_after_interaction
            await update_memory_after_interaction(donor_id, "declined", {"consecutive_declines": 1})
            
            # Run repair in background
            asyncio.create_task(run_repair_in_background(request_id, patient_id, pos))
            return
            
        # Eligible - Confirm
        supabase.table("blood_chains")\
            .update({
                "status": "CONFIRMED",
                "confirmed_at": datetime.utcnow().isoformat() + "Z"
            })\
            .eq("request_id", request_id)\
            .eq("donor_id", donor_id)\
            .execute()
            
        from agents.neo4j_match import Neo4jMatcher
        await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "CONFIRMED")
        
        thanks_msg = "≡ƒ⌐╕ Thank you! Your donation is confirmed. The hospital staff has been notified. We will contact you with scheduling details."
        if bot:
            await bot.send_message(chat_id=chat_id, text=thanks_msg)
        else:
            logger.info(f"Mock Bot message to {chat_id}: {thanks_msg}")
            
        from services.donor_memory import update_memory_after_interaction
        await update_memory_after_interaction(donor_id, "confirmed", {})
        
        await ws_manager.broadcast({
            "type": "donor_confirmed",
            "request_id": request_id,
            "donor_name": donor_profile["name"],
            "position": pos
        })
    else:
        # User replied NO
        supabase.table("blood_chains")\
            .update({
                "status": "DECLINED",
                "declined_at": datetime.utcnow().isoformat() + "Z"
            })\
            .eq("request_id", request_id)\
            .eq("donor_id", donor_id)\
            .execute()
            
        from agents.neo4j_match import Neo4jMatcher
        await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "DECLINED")
        
        no_msg = "Understood. Thank you for letting us know. We will reach out to you next time."
        if bot:
            await bot.send_message(chat_id=chat_id, text=no_msg)
        else:
            logger.info(f"Mock Bot message to {chat_id}: {no_msg}")
            
        from services.donor_memory import update_memory_after_interaction
        dec_count_res = supabase.table("blood_chains").select("status").eq("donor_id", donor_id).eq("status", "DECLINED").execute()
        dec_count = len(dec_count_res.data or [])
        await update_memory_after_interaction(donor_id, "declined", {"consecutive_declines": dec_count})
        
        await ws_manager.broadcast({
            "type": "donor_declined",
            "request_id": request_id,
            "donor_name": donor_profile["name"],
            "position": pos
        })
        
        # Run repair in background
        asyncio.create_task(run_repair_in_background(request_id, patient_id, pos))

async def handle_photo_onboarding(chat_id: str, file_id: str):
    """Downloads photo, sends to OCR, and creates/updates donor record."""
    settings = get_settings()
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
    if not bot:
        logger.warning("No telegram bot token, mocking photo onboarding.")
        return
        
    try:
        # Download file bytes
        file_obj = await bot.get_file(file_id)
        img_buffer = BytesIO()
        await file_obj.download_to_memory(out=img_buffer)
        image_bytes = img_buffer.getvalue()
        
        # Call OCR Service
        from services.ocr_service import extract_blood_type_from_image
        # Check if donor is registered
        supabase = get_supabase_admin()
        donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
        donor_id = donor_res.data[0]["donor_id"] if donor_res.data else None

        # Check if in registration flow ΓÇö use OCR result for blood type
        if chat_id in registration_sessions:
            session = registration_sessions[chat_id]
            result = await extract_blood_type_from_image(image_bytes, donor_id)
            blood_type = result.get("blood_group")
            if blood_type and blood_type in KNOWN_BLOOD_TYPES:
                session["blood_type"] = blood_type
                session["step"] = "city"
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"≡ƒô╕ Detected blood type: *{blood_type}*! Now, what is your city?",
                    parse_mode="Markdown"
                )
                return
        
        result = await extract_blood_type_from_image(image_bytes, donor_id)
        blood_type = result.get("blood_group")
        name = result.get("name")
        
        if blood_type:
            resp_msg = f"📸 *OCR Scan Success!*\n\nExtracted Blood Type: *{blood_type}*"
            if name:
                resp_msg += f"\nExtracted Name: *{name}*"
            if donor_id:
                resp_msg += "\n\nYour donor profile has been updated automatically."
            else:
                resp_msg += f"\n\nTo complete registration, reply: `/register {blood_type}`"
        else:
            resp_msg = "≡ƒô╕ OCR Scan failed to detect a valid blood group card. Please try again with a clearer image."
            
        await bot.send_message(chat_id=chat_id, text=resp_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed photo onboarding: {e}", exc_info=True)


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# COMMAND HANDLER (V2: All commands including /pause, /resume, /profile, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_command(chat_id: str, cmd: str, args: List[str], user_context: dict) -> Optional[str]:
    """Processes bot commands deterministically."""
    cmd_clean = cmd.lower()
    supabase = get_supabase_admin()
    
    if cmd_clean == "/start":
        from services.consent_service import CONSENT_TEXTS
        lang = user_context.get("lang", "en")
        consent_prompt = CONSENT_TEXTS.get(lang, CONSENT_TEXTS['en'])
        
        welcome = (
            f"🩸 *Welcome to BloodBridge AI!*\n\n"
            f"We coordinate rare matched blood donations for Thalassemia patients.\n\n"
            f"🛡️ *DPDP Act Compliance & Data Consent:*\n"
            f"{consent_prompt}\n\n"
            f"Reply *HAAN* or *YES* to accept and start. Reply *NO* to reject."
        )
        return welcome

    elif cmd_clean == "/register":
        # V2: Multi-turn registration flow
        if user_context.get("role") == "Donor":
            return "You are already registered! Use /profile to see your details."

        if args and args[0].upper() in KNOWN_BLOOD_TYPES:
            # Legacy single-command registration (backwards compatible)
            blood_type = args[0].upper()
            exist_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", chat_id).execute()
            if exist_res.data:
                supabase.table("donors").update({"blood_type": blood_type}).eq("telegram_chat_id", chat_id).execute()
                return f"Updated your registered blood type to *{blood_type}*."

            donor_id = f"D-{random.randint(10000, 99999)}"
            supabase.table("donors").insert({
                "donor_id": donor_id,
                "telegram_chat_id": chat_id,
                "name": f"Telegram Donor {chat_id[-4:] if len(chat_id) >= 4 else chat_id}",
                "blood_type": blood_type,
                "city": "Hyderabad",
                "consent_outreach": True,
                "is_active": True
            }).execute()
            await consent_service.ConsentService.grant_consent(donor_id, ['data_storage', 'outreach_telegram'], "telegram", "en")
            return f"🎉 Registration complete! Registered as *{blood_type}* in Hyderabad. Thank you!"

        # Start multi-turn registration
        registration_sessions[chat_id] = {"step": "blood_type"}
        return "Let's get you registered! 🩸\n\nWhat is your *blood type*? (e.g., B+, O-, AB+)\n\n📸 You can also send a photo of your blood group card."

    elif cmd_clean == "/profile":
        return await get_donor_profile.ainvoke({"chat_id": chat_id})

    elif cmd_clean == "/schedule":
        return await get_donation_history.ainvoke({"chat_id": chat_id})

    elif cmd_clean == "/eligibility":
        return await check_eligibility.ainvoke({"chat_id": chat_id})

    elif cmd_clean == "/nextdonation":
        return await get_next_donation_date.ainvoke({"chat_id": chat_id})

    elif cmd_clean == "/language":
        if not args:
            langs = "\n".join(f"- `{code}` = {name}" for code, name in LANGUAGE_NAMES.items())
            return f"Please specify a language code:\n{langs}\n\nExample: `/language hi`"
        return await get_donor_profile.ainvoke({"chat_id": chat_id, "language_code": args[0]})

    elif cmd_clean == "/pause":
        if user_context.get("role") != "Donor":
            return "Only registered donors can pause availability."
        days = 14
        if args:
            try:
                days = int(args[0])
            except ValueError:
                return "Please provide a number of days. Example: `/pause 14`"
        until_date = (date.today() + timedelta(days=days)).isoformat()
        return await toggle_availability.ainvoke({"chat_id": chat_id, "available": False, "until_date": until_date})

    elif cmd_clean == "/resume":
        if user_context.get("role") != "Donor":
            return "Only registered donors can resume availability."
        return await toggle_availability.ainvoke({"chat_id": chat_id, "available": True})

    elif cmd_clean == "/status":
        if not args:
            return "Please provide a Patient ID. Example: `/status P-1002`"
        p_id = args[0].strip()
        return await get_my_bridge.ainvoke({"patient_id": p_id})
        
    elif cmd_clean == "/impact":
        return await get_impact_story.ainvoke({"chat_id": chat_id})
        
    elif cmd_clean == "/badges":
        return await get_impact_story.ainvoke({"chat_id": chat_id})
        
    elif cmd_clean == "/leaderboard":
        city = "Hyderabad"
        if user_context.get("role") == "Donor":
            city = user_context.get("donor_profile", {}).get("city", "Hyderabad")
            
        res = supabase.table("leaderboard_cache")\
            .select("donor_id, lives_saved, rank")\
            .eq("city", city)\
            .order("rank")\
            .limit(5)\
            .execute()
            
        lines = [f"🏆 *Leaderboard for {city}* this month:\n"]
        for idx, row in enumerate(res.data or []):
            donor_res = supabase.table("donors").select("name").eq("donor_id", row["donor_id"]).execute()
            name = donor_res.data[0]["name"] if donor_res.data else f"Donor {row['donor_id'][-4:]}"
            lines.append(f"{row['rank']}. {name} - {row['lives_saved']} lives saved 🩸")
            
        if not res.data:
            lines.append("No leaderboard entries found for this month.")
            
        return "\n".join(lines)
        
    elif cmd_clean == "/consent":
        if user_context.get("role") != "Donor":
            return "Consent settings are only applicable to registered donors."
        donor_id = user_context["donor_id"]
        
        res = supabase.table("consent_records")\
            .select("consent_type, action")\
            .eq("donor_id", donor_id)\
            .execute()
            
        lines = ["🛡️ *Your Data Consent Status:*"]
        for c in (res.data or []):
            emoji = "✅" if c["action"] == "granted" else "❌"
            lines.append(f"- {c['consent_type']}: {emoji} {c['action'].capitalize()}")
            
        if not res.data:
            lines.append("No explicit consent records found.")
            
        return "\n".join(lines)
        
    elif cmd_clean == "/revoke":
        if user_context.get("role") != "Donor":
            return "Only registered donors can revoke consent."
        if not args:
            return "Please provide consent type (e.g. `outreach_telegram`, `outreach_sms`, or `all`)."
        c_type = args[0].strip()
        
        success = await consent_service.ConsentService.revoke_consent(user_context["donor_id"], c_type)
        if success:
            return f"Successfully revoked consent for *{c_type}*. We will no longer contact you via this channel."
        return "Failed to revoke consent. Please verify the consent type name."
        
    elif cmd_clean == "/mydata":
        # DPDP Right to Access — V2: stripped of sensitive fields
        if user_context.get("role") != "Donor":
            return "No data records found."
        donor = user_context.get("donor_profile", {})
        return (
            f"🛡️ *DPDP Right to Access - Your Personal Data Export:*\n\n"
            f"Name: {donor.get('name')}\n"
            f"Blood Type: {donor.get('blood_type')}\n"
            f"City: {donor.get('city')}\n"
            f"Donations: {donor.get('donation_count', 0)}\n"
            f"Lives Saved: {donor.get('lives_saved', 0)}\n"
            f"Registered At: {donor.get('created_at')}\n\n"
            f"🔒 Sensitive medical data is only accessible via the secure web portal."
        )
        
    elif cmd_clean == "/deletedata":
        if user_context.get("role") != "Donor":
            return "No data records found."
        if len(args) > 0 and args[0].upper() == "CONFIRM":
            donor_id = user_context["donor_id"]
            supabase.table("donors").delete().eq("donor_id", donor_id).execute()
            return "🚮 *Right to Erasure Executed.* Your profile and all history have been permanently deleted from our servers."
        return "⚠️ *WARNING:* This will permanently erase your profile and donation history. To proceed, type `/deletedata CONFIRM`."

    elif cmd_clean == "/help":
        lang = user_context.get("lang", "en")
        if lang and lang[:2] == "hi":
            return (
                "🩸 *BloodBridge AI — उपलब्ध कमांड:*\n\n"
                "👤 /profile — अपनी प्रोफाइल देखें\n"
                "📅 /schedule — आगामी दान देखें\n"
                "✅ /eligibility — पात्रता जांचें\n"
                "📅 /nextdonation — अगली दान तिथि\n"
                "🌐 /language [कोड] — भाषा बदलें\n"
                "⏸️ /pause [दिन] — उपलब्धता रोकें\n"
                "▶️ /resume — उपलब्धता शुरू करें\n"
                "🏆 /impact — प्रभाव और बैज\n"
                "🏅 /leaderboard — शहर लीडरबोर्ड\n"
                "🛡️ /consent — सहमति स्थिति\n"
                "📊 /mydata — डेटा निर्यात\n"
                "❌ /revoke [प्रकार] — सहमति रद्द करें\n"
                "🚮 /deletedata — डेटा हटाएं"
            )
        elif lang and lang[:2] == "te":
            return (
                "🩸 *BloodBridge AI — అందుబాటులో ఉన్న కమాండ్‌లు:*\n\n"
                "👤 /profile — మీ ప్రొఫైల్ చూడండి\n"
                "📅 /schedule — రాబోయే దానాలు\n"
                "✅ /eligibility — అర్హత తనిఖీ\n"
                "📅 /nextdonation — తదుపరి దాన తేదీ\n"
                "🌐 /language [కోడ్] — భాష మార్చండి\n"
                "⏸️ /pause [రోజులు] — లభ్యత ఆపండి\n"
                "▶️ /resume — లభ్యత పునఃప్రారంభించండి\n"
                "🏆 /impact — ప్రభావం & బ్యాడ్జ్‌లు\n"
                "🏅 /leaderboard — నగర లీడర్‌బోర్డ్\n"
                "🛡️ /consent — సమ్మతి స్థితి\n"
                "📊 /mydata — డేటా ఎగుమతి\n"
                "❌ /revoke [రకం] — సమ్మతి రద్దు\n"
                "🚮 /deletedata — డేటా తొలగించండి"
            )
        return (
            "🩸 *BloodBridge AI — Available Commands:*\n\n"
            "👤 /profile — View your profile\n"
            "📅 /schedule — View upcoming donations\n"
            "✅ /eligibility — Check donation eligibility\n"
            "📅 /nextdonation — Next donation date\n"
            "🌐 /language [code] — Change language (hi, te, ta, en)\n"
            "⏸️ /pause [days] — Pause donation availability\n"
            "▶️ /resume — Resume availability\n"
            "🏆 /impact — View impact & badges\n"
            "🏅 /leaderboard — City leaderboard\n"
            "🛡️ /consent — View consent status\n"
            "📊 /mydata — Export your data (DPDP)\n"
            "❌ /revoke [type] — Revoke consent\n"
            "🚮 /deletedata — Delete all data"
        )
        
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-TURN REGISTRATION HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_registration_step(chat_id: str, text: str) -> Optional[str]:
    """Handles multi-turn registration conversation flow.
    Returns a response string if in registration, None otherwise."""
    key = chat_id
    if key not in registration_sessions:
        return None

    session = registration_sessions[key]
    step = session.get("step")

    if step == "blood_type":
        bt = text.upper().strip()
        if bt not in KNOWN_BLOOD_TYPES:
            return f"Invalid blood type '{text}'. Please enter one of: A+, A-, B+, B-, AB+, AB-, O+, O-"
        session["blood_type"] = bt
        session["step"] = "city"
        return f"Great! Blood type: *{bt}* ✅\n\nNow, what is your *city*?"

    elif step == "city":
        city = text.strip().title()
        if len(city) < 2:
            return "Please enter a valid city name."
        session["city"] = city
        session["step"] = "name"
        return f"City: *{city}* ✅\n\nLastly, what is your *name*?"

    elif step == "name":
        name = text.strip().title()
        if len(name) < 2:
            return "Please enter a valid name."
        session["name"] = name
        session["step"] = "phone"
        return (
            f"Name: *{name}* ✅\n\n"
            f"Finally, please share your *phone number* (or type 'skip'):\n"
            f"📱 Format: 9XXXXXXXXX or +91XXXXXXXXX"
        )

    elif step == "phone":
        import re as _re
        phone_raw = text.strip()
        phone = None
        if phone_raw.lower() != "skip":
            digits = _re.sub(r'\D', '', phone_raw)
            if len(digits) == 10:
                phone = f"+91{digits}"
            elif len(digits) == 12 and digits.startswith("91"):
                phone = f"+{digits}"
            else:
                return "❌ Invalid phone format. Enter 10-digit number or type 'skip'."

        # Complete registration
        blood_type = session["blood_type"]
        city = session["city"]
        name = session["name"]
        supabase = get_supabase_admin()

        # Check if already registered
        exist_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", key).execute()
        if exist_res.data:
            update_data = {"name": name, "blood_type": blood_type, "city": city}
            if phone:
                update_data["phone"] = phone
            supabase.table("donors").update(update_data).eq("telegram_chat_id", key).execute()
            del registration_sessions[key]
            phone_str = phone or "not provided"
            return f"🎉 Profile updated! Name: *{name}*, Blood Type: *{blood_type}*, City: *{city}*, Phone: {phone_str}"

        donor_id = f"D-{random.randint(10000, 99999)}"

        # Default to English during registration, let them update it later if desired
        detected_lang = "en"

        insert_data = {
            "donor_id": donor_id,
            "telegram_chat_id": key,
            "name": name,
            "blood_type": blood_type,
            "city": city,
            "preferred_language": detected_lang,
            "consent_outreach": True,
            "is_active": True
        }
        
        is_new_donor = True
        
        if phone:
            # GAP-18: Handle duplicate phone number gracefully
            phone_check = supabase.table("donors").select("donor_id").eq("phone", phone).execute()
            if phone_check.data:
                # Phone exists — link Telegram to existing web/hospital-registered donor
                existing_donor_id = phone_check.data[0]["donor_id"]
                donor_id = existing_donor_id # Switch to existing ID for consent/memory
                is_new_donor = False
                
                update_data = {
                    "telegram_chat_id": key,
                    "name": name,
                    "blood_type": blood_type,
                    "city": city,
                    "preferred_language": detected_lang
                }
                supabase.table("donors").update(update_data).eq("donor_id", existing_donor_id).execute()
            else:
                insert_data["phone"] = phone
                supabase.table("donors").insert(insert_data).execute()
        else:
            supabase.table("donors").insert(insert_data).execute()

        await consent_service.ConsentService.grant_consent(donor_id, ['data_storage', 'outreach_telegram'], "telegram", detected_lang)

        # Initialize donor memory only if it's a new donor or memory doesn't exist
        if is_new_donor:
            supabase.table("donor_memory").insert({
                "donor_id": donor_id,
                "preferred_language": detected_lang
            }).execute()

        del registration_sessions[key]
        phone_line = f"- Phone: `{phone}`\n" if phone else ""
        return (
            f"🎉 *Registration Complete!*\n\n"
            f"- Name: *{name}*\n"
            f"- Blood Type: *{blood_type}*\n"
            f"- City: *{city}*\n"
            f"{phone_line}"
            f"- Donor ID: `{donor_id}`\n\n"
            f"Type /help to see all available commands. Thank you for joining Blood Warriors! 🩸"
        )

    return None


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """Send outreach message via Telegram."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning(f"TELEGRAM_BOT_TOKEN not configured. Mocking send to chat_id: {chat_id}")
        return True
        
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        logger.info(f"Telegram message successfully sent to chat_id: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message to chat_id {chat_id}: {e}")
        return False
