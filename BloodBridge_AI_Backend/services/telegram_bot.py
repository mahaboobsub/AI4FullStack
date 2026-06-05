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
from langchain_groq import ChatGroq
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
    res = supabase.table("staff").select("role, is_active").eq("telegram_chat_id", str(chat_id)).execute()
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
    donor_res = supabase.table("donors").select("donor_id, name, lives_saved, donation_count").eq("telegram_chat_id", str(chat_id)).execute()
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
# V2 NEW TOOLS (7 tools)
# ═══════════════════════════════════════════════════════════════════════════════

class ChatIdInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")

@tool(args_schema=ChatIdInput)
async def get_my_profile(chat_id: str) -> str:
    """Use this tool when a donor asks about their profile, their details, or who they are.
    Returns ONLY non-sensitive fields per DPDP 2023. Never returns phone, antibodies, or clinical data."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("*").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        return "You are not registered as a donor yet. Use /register to get started."

    d = donor_res.data[0]
    return (
        f"👤 *Your Profile:*\n\n"
        f"- Name: *{d.get('name', 'N/A')}*\n"
        f"- Blood Type: *{d.get('blood_type', 'N/A')}*\n"
        f"- City: *{d.get('city', 'N/A')}*\n"
        f"- Donations: *{d.get('donation_count', 0)}*\n"
        f"- Lives Saved: *{d.get('lives_saved', 0)}*\n"
        f"- Status: *{'Active ✅' if d.get('is_active') else 'Inactive ⏸️'}*\n"
        f"- Language: *{LANGUAGE_NAMES.get(d.get('preferred_language', 'en'), d.get('preferred_language', 'English'))}*\n\n"
        f"🛡️ For detailed medical records (antibody flags, antigen data), please visit the secure web portal."
    )


@tool(args_schema=ChatIdInput)
async def get_my_schedule(chat_id: str) -> str:
    """Use this tool when a donor asks about their upcoming donations, schedule, or next appointment."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        return "You are not registered. Use /register to get started."

    donor_id = donor_res.data[0]["donor_id"]

    # Find chains this donor was part of → get patient IDs → get their schedules
    chain_res = supabase.table("blood_chains")\
        .select("request_id")\
        .eq("donor_id", donor_id)\
        .in_("status", ["CONFIRMED", "COMPLETED", "ALERTED"])\
        .execute()

    if not chain_res.data:
        return "📅 No upcoming donations scheduled. You'll get a notification via Telegram when a patient needs your blood type. 🩸"

    request_ids = list(set(c["request_id"] for c in chain_res.data))

    # Get schedules linked to these requests
    today = date.today()
    results = []
    for rid in request_ids[:5]:
        sched_res = supabase.table("transfusion_schedule")\
            .select("scheduled_date, hospital, status")\
            .eq("request_id", rid)\
            .gte("scheduled_date", today.isoformat())\
            .order("scheduled_date")\
            .limit(2)\
            .execute()
        for s in (sched_res.data or []):
            sd = date.fromisoformat(s["scheduled_date"])
            days_until = (sd - today).days
            results.append(f"- 📅 *{s['scheduled_date']}* at *{s['hospital']}* ({days_until} days away) — Status: {s['status']}")

    if not results:
        return "📅 No upcoming donations scheduled. You'll get a notification via Telegram when a patient needs your blood type. 🩸"

    return "📅 *Your Upcoming Donations:*\n\n" + "\n".join(results[:4])


@tool(args_schema=ChatIdInput)
async def get_my_eligibility(chat_id: str) -> str:
    """Use this tool when a donor asks if they are eligible to donate blood."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("*").eq("telegram_chat_id", str(chat_id)).execute()
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
        hold_until = donor.get("medical_hold_until")
        reasons.append(f"You are on medical hold{f' until {hold_until}' if hold_until else ''}.")

    last_date = donor.get("last_donation_date")
    if last_date:
        delta = (date.today() - date.fromisoformat(str(last_date))).days
        if delta < 56:
            eligible = False
            remaining = 56 - delta
            reasons.append(f"Only {delta} days since your last donation. You need {remaining} more days (56-day minimum).")

    if eligible:
        return "✅ *You are eligible to donate!* Thank you for being ready to save lives. 🩸"
    else:
        return f"❌ *Not eligible right now:*\n" + "\n".join(f"- {r}" for r in reasons)


@tool(args_schema=ChatIdInput)
async def get_next_donation_date(chat_id: str) -> str:
    """Use this tool when a donor asks when they can next donate blood."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("last_donation_date, preferred_language").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        return "You are not registered. Use /register to get started."

    donor = donor_res.data[0]
    last_date = donor.get("last_donation_date")
    lang = donor.get("preferred_language", "en")

    if not last_date:
        return "🩸 You can donate any time! No previous donation recorded."

    last = date.fromisoformat(str(last_date))
    next_date = last + timedelta(days=56)
    today = date.today()

    if next_date <= today:
        return f"✅ You are already eligible to donate! Your last donation was on {last.isoformat()}."

    days_remaining = (next_date - today).days

    # Format date in locale-friendly way
    months_hi = {1: "जनवरी", 2: "फ़रवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
                 7: "जुलाई", 8: "अगस्त", 9: "सितम्बर", 10: "अक्टूबर", 11: "नवम्बर", 12: "दिसम्बर"}
    months_te = {1: "జనవరి", 2: "ఫిబ్రవరి", 3: "మార్చి", 4: "ఏప్రిల్", 5: "మే", 6: "జూన్",
                 7: "జూలై", 8: "ఆగస్ట్", 9: "సెప్టెంబర్", 10: "అక్టోబర్", 11: "నవంబర్", 12: "డిసెంబర్"}

    if lang and lang[:2] == "hi":
        date_str = f"{next_date.day} {months_hi.get(next_date.month, '')} {next_date.year}"
    elif lang and lang[:2] == "te":
        date_str = f"{next_date.day} {months_te.get(next_date.month, '')} {next_date.year}"
    else:
        date_str = next_date.strftime("%d %B %Y")

    return f"📅 Your next eligible donation date: *{date_str}* ({days_remaining} days from now)."


class LanguageInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")
    language_code: str = Field(description="Language code: hi, te, ta, en, kn, ml, mr, bn, gu, pa")

@tool(args_schema=LanguageInput)
async def update_my_language(chat_id: str, language_code: str) -> str:
    """Use this tool when a donor wants to change their preferred language."""
    lang = language_code.lower().strip()[:2]
    if lang not in LANGUAGE_NAMES:
        return f"❌ Unsupported language code '{language_code}'. Supported: {', '.join(LANGUAGE_NAMES.keys())}"

    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        return "You are not registered. Use /register to get started."

    supabase.table("donors").update({"preferred_language": lang}).eq("telegram_chat_id", str(chat_id)).execute()

    lang_name = LANGUAGE_NAMES[lang]
    confirmations = {
        "hi": f"✅ भाषा बदलकर {lang_name} कर दी गई है।",
        "te": f"✅ భాష {lang_name}కి మార్చబడింది.",
        "ta": f"✅ மொழி {lang_name} ஆக மாற்றப்பட்டது.",
        "en": f"✅ Language changed to {lang_name}."
    }
    return confirmations.get(lang, f"✅ Language updated to {lang_name}.")


class AvailabilityInput(BaseModel):
    chat_id: str = Field(description="The user's Telegram Chat ID from system prompt")
    available: bool = Field(description="True to set available, False to pause")
    until_date: Optional[str] = Field(default=None, description="Date until which unavailable (ISO format)")

@tool(args_schema=AvailabilityInput)
async def set_my_availability(chat_id: str, available: bool, until_date: Optional[str] = None) -> str:
    """Use this tool when a donor wants to pause or resume their donation availability."""
    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id, name").eq("telegram_chat_id", str(chat_id)).execute()
    if not donor_res.data:
        return "You are not registered. Use /register to get started."

    donor_id = donor_res.data[0]["donor_id"]
    name = donor_res.data[0]["name"]

    update_data = {"is_active": available, "medical_hold": not available}
    if until_date and not available:
        try:
            date.fromisoformat(until_date)
            update_data["medical_hold_until"] = until_date
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD."
    elif available:
        update_data["medical_hold"] = False
        update_data["medical_hold_until"] = None

    supabase.table("donors").update(update_data).eq("donor_id", donor_id).execute()

    if available:
        return f"✅ Welcome back, {name}! Your donation availability has been resumed. We'll notify you when a patient needs you."
    else:
        until_msg = f" until {until_date}" if until_date else ""
        return f"⏸️ Understood, {name}! We'll pause donation requests{until_msg}. Thank you for letting us know. 🙏"


@tool(args_schema=ChatIdInput)
async def get_medical_data_portal_link(chat_id: str) -> str:
    """Use this tool when a donor asks for medical records, antibody flags, antigen data, hemoglobin levels,
    or any clinical diagnostic information. DPDP 2023 requires this data to be accessed only via the secure web portal."""
    settings = get_settings()
    portal_url = settings.WEB_PORTAL_URL

    supabase = get_supabase_admin()
    donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()

    if donor_res.data:
        donor_id = donor_res.data[0]["donor_id"]
        portal_url = f"{portal_url}/donor?id={donor_id}"

    return (
        f"🛡️ *Medical Data Protected (DPDP Act 2023)*\n\n"
        f"Detailed medical records (antibody flags, antigen compatibility, hemoglobin levels, clinical history) "
        f"are classified as sensitive personal data under the Digital Personal Data Protection Act, 2023.\n\n"
        f"For your safety, this data can only be accessed through our secure web portal:\n"
        f"🔗 {portal_url}\n\n"
        f"Log in with your Donor ID or phone number to view your complete medical profile."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# REACT AGENT COMPILATION (V2: 10 tools)
# ═══════════════════════════════════════════════════════════════════════════════

def get_telegram_agent():
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is missing. Telegram React Agent cannot be initialized.")
        return None
        
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=settings.GROQ_API_KEY
    )
    tools = [
        trigger_blood_emergency, check_chain_status, get_my_impact,
        get_my_profile, get_my_schedule, get_my_eligibility,
        get_next_donation_date, update_my_language, set_my_availability,
        get_medical_data_portal_link
    ]
    
    system_prompt = """You are the BloodBridge AI Assistant on Telegram.  
You help hospital staff coordinate emergencies and donors track their impact.  
RULES:  
1. ALWAYS check the user's role provided in the system prompt context. If a DONOR tries to trigger an emergency, politely deny and explain they can only view their impact.  
2. Always reply ONLY in the donor's preferred language. If preferred_language is 'hi', reply in Hindi (Devanagari script). If 'te', reply in Telugu script. If 'en' or unknown, reply in English. Do NOT reply in English first then translate.
3. Keep responses under 150 words. Use emojis appropriately (🩸, 🚨, ✅, 📅).  
4. If a tool returns a success message, relay it warmly.
5. You MUST pass the user's exact Telegram Chat ID (from system prompt context) to the tools.
6. NEVER provide antibody_flags, antigen_scores, hemoglobin_level, kell_negative status, or any clinical diagnostic data via Telegram. If asked for medical/clinical data, ALWAYS invoke the get_medical_data_portal_link tool.
7. When asked about profile, use get_my_profile. When asked about eligibility, use get_my_eligibility. When asked about schedule/next donation, use get_my_schedule or get_next_donation_date.
"""
    return create_react_agent(llm, tools, state_modifier=system_prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE BOT WORKFLOWS & ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

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
        
        # Check active alerted node
        chain_res = supabase.table("blood_chains")\
            .select("*")\
            .eq("donor_id", donor_id)\
            .in_("status", ["ALERTED", "SMS", "VOICE"])\
            .order("alerted_at", desc=True)\
            .limit(1)\
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
            "trace_id": f"REPAIR-BG"
        }
        
        from agents.repair import chain_repair_agent
        from agents.outreach import outreach_agent
        
        repair_res = await chain_repair_agent(state)
        state.update(repair_res)
        
        if state.get("outreach_plan"):
            logger.info(f"Background Repair: Re-running outreach for request {request_id}...")
            await outreach_agent(state)
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
        
        thanks_msg = "🩸 Thank you! Your donation is confirmed. The hospital staff has been notified. We will contact you with scheduling details."
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
        donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
        donor_id = donor_res.data[0]["donor_id"] if donor_res.data else None

        # Check if in registration flow — use OCR result for blood type
        if str(chat_id) in registration_sessions:
            session = registration_sessions[str(chat_id)]
            result = await extract_blood_type_from_image(image_bytes, donor_id)
            blood_type = result["blood_type"]
            if blood_type and blood_type in KNOWN_BLOOD_TYPES:
                session["blood_type"] = blood_type
                session["step"] = "city"
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"📸 Detected blood type: *{blood_type}*! Now, what is your city?",
                    parse_mode="Markdown"
                )
                return
        
        result = await extract_blood_type_from_image(image_bytes, donor_id)
        blood_type = result["blood_type"]
        confidence = result["confidence"]
        
        if blood_type:
            resp_msg = f"📸 *OCR Scan Success!*\n\nExtracted Blood Type: *{blood_type}*\nConfidence: *{confidence:.0%}*"
            if donor_id:
                resp_msg += "\n\nYour donor profile has been updated automatically."
            else:
                resp_msg += f"\n\nTo complete registration, reply: `/register {blood_type}`"
        else:
            resp_msg = "📸 OCR Scan failed to detect a valid blood group card. Please try again with a clearer image."
            
        await bot.send_message(chat_id=chat_id, text=resp_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed photo onboarding: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════════
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
            exist_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
            if exist_res.data:
                supabase.table("donors").update({"blood_type": blood_type}).eq("telegram_chat_id", str(chat_id)).execute()
                return f"Updated your registered blood type to *{blood_type}*."

            donor_id = f"D-{random.randint(10000, 99999)}"
            supabase.table("donors").insert({
                "donor_id": donor_id,
                "telegram_chat_id": str(chat_id),
                "name": f"Telegram Donor {chat_id[-4:] if len(str(chat_id)) >= 4 else chat_id}",
                "blood_type": blood_type,
                "city": "Hyderabad",
                "consent_outreach": True,
                "is_active": True
            }).execute()
            await consent_service.grant_consent(donor_id, ['data_storage', 'outreach_telegram'])
            return f"🎉 Registration complete! Registered as *{blood_type}* in Hyderabad. Thank you!"

        # Start multi-turn registration
        registration_sessions[str(chat_id)] = {"step": "blood_type"}
        return "Let's get you registered! 🩸\n\nWhat is your *blood type*? (e.g., B+, O-, AB+)\n\n📸 You can also send a photo of your blood group card."

    elif cmd_clean == "/profile":
        return await get_my_profile.ainvoke(str(chat_id))

    elif cmd_clean == "/schedule":
        return await get_my_schedule.ainvoke(str(chat_id))

    elif cmd_clean == "/eligibility":
        return await get_my_eligibility.ainvoke(str(chat_id))

    elif cmd_clean == "/nextdonation":
        return await get_next_donation_date.ainvoke(str(chat_id))

    elif cmd_clean == "/language":
        if not args:
            langs = "\n".join(f"- `{code}` = {name}" for code, name in LANGUAGE_NAMES.items())
            return f"Please specify a language code:\n{langs}\n\nExample: `/language hi`"
        return await update_my_language.ainvoke({"chat_id": str(chat_id), "language_code": args[0]})

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
        return await set_my_availability.ainvoke({"chat_id": str(chat_id), "available": False, "until_date": until_date})

    elif cmd_clean == "/resume":
        if user_context.get("role") != "Donor":
            return "Only registered donors can resume availability."
        return await set_my_availability.ainvoke({"chat_id": str(chat_id), "available": True})

    elif cmd_clean == "/status":
        if not args:
            return "Please provide a Patient ID. Example: `/status P-1002`"
        p_id = args[0].strip()
        return await check_chain_status.ainvoke(p_id)
        
    elif cmd_clean == "/impact":
        return await get_my_impact.ainvoke(str(chat_id))
        
    elif cmd_clean == "/badges":
        return await get_my_impact.ainvoke(str(chat_id))
        
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
        
        success = await consent_service.revoke_consent(user_context["donor_id"], c_type)
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
    key = str(chat_id)
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

        # Complete registration
        blood_type = session["blood_type"]
        city = session["city"]
        supabase = get_supabase_admin()

        # Check if already registered
        exist_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", key).execute()
        if exist_res.data:
            supabase.table("donors").update({
                "name": name, "blood_type": blood_type, "city": city
            }).eq("telegram_chat_id", key).execute()
            del registration_sessions[key]
            return f"🎉 Profile updated! Name: *{name}*, Blood Type: *{blood_type}*, City: *{city}*"

        donor_id = f"D-{random.randint(10000, 99999)}"

        # Detect language from first message if possible
        detected_lang = "en"
        try:
            from langdetect import detect
            detected_lang = detect(name + " " + city)[:2]
            if detected_lang not in LANGUAGE_NAMES:
                detected_lang = "en"
        except Exception:
            pass

        supabase.table("donors").insert({
            "donor_id": donor_id,
            "telegram_chat_id": key,
            "name": name,
            "blood_type": blood_type,
            "city": city,
            "preferred_language": detected_lang,
            "consent_outreach": True,
            "is_active": True
        }).execute()

        await consent_service.grant_consent(donor_id, ['data_storage', 'outreach_telegram'])

        # Initialize donor memory
        supabase.table("donor_memory").insert({
            "donor_id": donor_id,
            "preferred_language": detected_lang
        }).execute()

        del registration_sessions[key]
        return (
            f"🎉 *Registration Complete!*\n\n"
            f"- Name: *{name}*\n"
            f"- Blood Type: *{blood_type}*\n"
            f"- City: *{city}*\n"
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
