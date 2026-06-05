"""
Agentic Telegram Bot Service for BloodBridge AI.
Implements tool-calling with Groq/LangGraph, hybrid routing, security checks, and OCR integrations.
"""
import asyncio
import logging
import random
import hashlib
from datetime import datetime, timezone
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

# --- AGENT TOOLS DEFINITION ---

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

# --- REACT AGENT COMPILATION ---

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
    tools = [trigger_blood_emergency, check_chain_status, get_my_impact]
    
    system_prompt = """You are the BloodBridge AI Assistant on Telegram.  
You help hospital staff coordinate emergencies and donors track their impact.  
RULES:  
1. ALWAYS check the user's role provided in the system prompt context. If a DONOR tries to trigger an emergency, politely deny and explain they can only view their impact.  
2. Reply with English as the primary language first, followed by the user's preferred language (if it differs from English).
3. Keep responses under 150 words. Use emojis appropriately (🩸, 🚨, ✅).  
4. If a tool returns a success message, relay it warmly.
5. You MUST pass the user's exact Telegram Chat ID (from system prompt context) to the tools get_my_impact and trigger_blood_emergency.
"""
    return create_react_agent(llm, tools, state_modifier=system_prompt)

# --- COREBOT WORKFLOWS & ROUTERS ---

async def get_user_context(chat_id: str) -> dict:
    """Fetch role, language, name, and active alerted chain node for a given chat_id."""
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
        
        return {
            "role": "Donor",
            "donor_id": donor_id,
            "name": d["name"],
            "lang": d.get("preferred_language", "en"),
            "chat_id": chat_id,
            "active_chain_status": "ALERTED" if active_node else "NONE",
            "active_node": active_node,
            "donor_profile": d
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
    
    # Resolve patient_id
    supabase = get_supabase_admin()
    req_res = supabase.table("emergency_requests").select("patient_id").eq("request_id", request_id).execute()
    patient_id = req_res.data[0]["patient_id"] if req_res.data else None
    
    is_yes = text_clean in ['yes', 'haan', 'ha', 'ok']
    
    if is_yes:
        # Re-validate eligibility
        p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
        patient = p_res.data[0] if p_res.data else {}
        
        donor_profile = user_context["donor_profile"]
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
        if not args:
            return "Please provide your blood type. Example: `/register B+`"
        blood_type = args[0].upper().strip()
        if blood_type not in KNOWN_BLOOD_TYPES:
            return "Invalid blood type. Supported: A+, A-, B+, B-, AB+, AB-, O+, O-"
            
        # Create donor record
        donor_id = f"D-{random.randint(10000, 99999)}"
        # Check if already registered
        exist_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
        if exist_res.data:
            supabase.table("donors").update({"blood_type": blood_type}).eq("telegram_chat_id", str(chat_id)).execute()
            return f"Updated your registered blood type to *{blood_type}*."
            
        supabase.table("donors").insert({
            "donor_id": donor_id,
            "telegram_chat_id": str(chat_id),
            "name": f"Telegram Donor {chat_id[-4:]}",
            "blood_type": blood_type,
            "city": "Hyderabad",  # default
            "consent_outreach": True,
            "is_active": True
        }).execute()
        
        # Grant consent in records
        await consent_service.grant_consent(donor_id, ['data_storage', 'outreach_telegram'])
        
        return f"🎉 Registration complete! Registered as *{blood_type}* in Hyderabad. Thank you!"
        
    elif cmd_clean == "/status":
        if not args:
            return "Please provide a Patient ID. Example: `/status P-1002`"
        p_id = args[0].strip()
        # Direct tool call simulation
        return await check_chain_status.ainvoke(p_id)
        
    elif cmd_clean == "/impact":
        return await get_my_impact.ainvoke(str(chat_id))
        
    elif cmd_clean == "/badges":
        return await get_my_impact.ainvoke(str(chat_id))
        
    elif cmd_clean == "/leaderboard":
        # Get city
        city = "Hyderabad"
        if user_context.get("role") == "Donor":
            city = user_context["donor_profile"].get("city", "Hyderabad")
            
        # Fetch leaderboard
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
        # DPDP Right to Access
        if user_context.get("role") != "Donor":
            return "No data records found."
        donor = user_context["donor_profile"]
        return (
            f"🛡️ *DPDP Right to Access - Your Personal Data Export:*\n\n"
            f"Name: {donor.get('name')}\n"
            f"Phone: {donor.get('phone')}\n"
            f"Blood Type: {donor.get('blood_type')}\n"
            f"City: {donor.get('city')}\n"
            f"Consent Outreach: {donor.get('consent_outreach')}\n"
            f"Registered At: {donor.get('created_at')}"
        )
        
    elif cmd_clean == "/deletedata":
        # DPDP Right to Erasure
        if user_context.get("role") != "Donor":
            return "No data records found."
        if len(args) > 0 and args[0].upper() == "CONFIRM":
            donor_id = user_context["donor_id"]
            supabase.table("donors").delete().eq("donor_id", donor_id).execute()
            return "🚮 *Right to Erasure Executed.* Your profile and all history have been permanently deleted from our servers."
        return "⚠️ *WARNING:* This will permanently erase your profile and donation history. To proceed, type `/deletedata CONFIRM`."
        
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
