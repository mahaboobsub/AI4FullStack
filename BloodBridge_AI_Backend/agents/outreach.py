"""
Outreach Agent for BloodBridge AI.
Handles personalized outreach generation via Groq and delivery to matching channels.
"""
import time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from models.state import AgentState
from core.database import get_supabase_admin
from core.config import get_settings
from core.neo4j_client import get_driver
from agents.neo4j_match import Neo4jMatcher
from api.websocket import ws_manager

# Services imports
from services.consent_service import consent_service  # module-level singleton = ConsentService()
from services.donor_memory import build_memory_context_for_llm
from services.telegram_bot import send_telegram_message, send_outreach_message
from core.llm_provider import get_fast_llm

logger = logging.getLogger(__name__)

OUTREACH_SYSTEM_PROMPT = """You are BloodBridge AI — emergency blood donation coordinator India.  
Generate a concise Telegram message requesting blood donation.  
MUST: be in donor's language, under 150 words, include blood type + hospital + urgency,  
reference donation history if provided, end with "Reply YES to confirm".  
10 supported languages. Plain text only — no markdown, no emojis in body."""

FALLBACK_TEMPLATES = {  
    'hi': "🩸 URGENT: {blood_type} blood needed at {hospital}. Kya aap donate kar sakte hain? Reply YES",  
    'te': "🩸 URGENT: {hospital} lo {blood_type} blood avasaram. Donate chestagara? Reply YES",  
    'ta': "🩸 URGENT: {hospital} ல {blood_type} blood தேவை. Donate செய்வீர்களா? Reply YES",  
    'en': "🩸 URGENT: {blood_type} blood needed at {hospital}. Can you donate? Reply YES",  
    'kn': "🩸 URGENT: {hospital} ನಲ್ಲಿ {blood_type} ರಕ್ತ ಬೇಕು. Donate ಮಾಡುತ್ತೀರಾ? Reply YES",  
    'ml': "🩸 URGENT: {hospital} ൽ {blood_type} രക്തം ആവശ്യം. Donate ചെയ്യുമോ? Reply YES",  
    'mr': "🩸 URGENT: {hospital} मध्ये {blood_type} रक्त हवे. Donate कराल? Reply YES",  
    'bn': "🩸 URGENT: {hospital}এ {blood_type} রক্ত চাই। Donate করবেন? Reply YES",  
    'gu': "🩸 URGENT: {hospital}માં {blood_type} blood જોઈએ. Donate? Reply YES",  
    'pa': "🩸 URGENT: {hospital}ਵਿੱਚ {blood_type} ਖੂਨ ਚਾਹੀਦਾ। Donate? Reply YES",  
}

async def generate_outreach_message(plan: dict, state: AgentState) -> str:  
    """  
    Fetch and inject donor memory context, then use Groq to generate a personalized outreach message.
    """  
    if "message" in plan:
        return plan["message"]
        
    donor_id = plan['donor_id']
    preferred_lang = plan.get("preferred_language", "hi")
    
    # 1. Fetch donor memory context
    memory_context = await build_memory_context_for_llm(donor_id)
    
    # 2. Call Groq for personalized generation
    settings = get_settings()
    try:
        llm = get_fast_llm()

        user_prompt = (
            f"Donor Details:\n"
            f"- Name: {plan.get('name', 'Donor')}\n"
            f"- Language: {preferred_lang}\n"
            f"- Distance: {plan.get('distance_km', 0.0):.1f} km\n"
            f"- Target Channel: {plan.get('channel', 'telegram')}\n\n"
            f"Patient Details:\n"
            f"- Hospital: {state.get('hospital_name', 'Hospital')}\n"
            f"- Blood Type: {state.get('blood_type')}\n"
            f"- Request Urgency: {state.get('urgency_result', {}).get('priority', 'HIGH')}\n\n"
            f"Donor Memory context:\n{memory_context}\n\n"
            f"Generate the outreach message now."
        )

        resp = await llm.ainvoke([
            ("system", OUTREACH_SYSTEM_PROMPT),
            ("user", user_prompt)
        ])
        return resp.content.strip()
    except Exception as e:
        logger.warning(f"Groq outreach generation failed for {donor_id}: {e}. Applying fallback template.")
    
    # 3. Fallback to templates if Groq fails or API key is missing
    lang_key = preferred_lang.lower()[:2]
    if lang_key not in FALLBACK_TEMPLATES:
        lang_key = "hi"
        
    template = FALLBACK_TEMPLATES[lang_key]
    return template.format(
        blood_type=state.get("blood_type"),
        hospital=state.get("hospital_name")
    )

async def outreach_agent(state: AgentState) -> dict:  
    """
    Outreach Agent Node.
    Filters outreach plan for active consent, generates messages in parallel, delivers them, 
    updates Supabase and Neo4j coordination statuses, and broadcasts the websocket event.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] OutreachAgent started...")
    
    outreach_plan = state.get("outreach_plan", [])
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    supabase = get_supabase_admin()
    
    if not outreach_plan:
        logger.warning("No outreach plan found. OutreachAgent skipping.")
        return {"non_consented_donors": []}
        
    # 1. CONSENT CHECK — audit before any outreach send
    consented_plans = []
    non_consented_donors = state.get("non_consented_donors", []).copy()
    
    for plan in outreach_plan:
        donor_id = plan["donor_id"]
        channel = plan["channel"]
        
        # Check channel consent (e.g. outreach_telegram, outreach_sms, outreach_voice)
        # Standardize voice_queue -> voice, sms_queue -> sms, telegram -> telegram
        consent_channel = "telegram"
        if "sms" in channel:
            consent_channel = "sms"
        elif "voice" in channel:
            consent_channel = "voice"
            
        has_consent = await consent_service.check_consent(donor_id, f"outreach_{consent_channel}")
        if not has_consent:
            non_consented_donors.append(donor_id)
            logger.info(f"Consent check failed for donor {donor_id} on outreach_{consent_channel}. Skipping.")
            continue
            
        consented_plans.append(plan)
        
    # 2. PARALLEL FAN-OUT — generate outreach messages simultaneously
    messages = await asyncio.gather(*[
        generate_outreach_message(plan, state) for plan in consented_plans
    ], return_exceptions=True)
    
    # 3. Delivery and Status Updates
    alerted_count = 0
    
    for idx, plan in enumerate(consented_plans):
        msg_val = messages[idx]
        if isinstance(msg_val, Exception):
            logger.error(f"Error generating message for donor {plan['donor_id']}: {msg_val}")
            continue
            
        donor_id = plan["donor_id"]
        channel = plan["channel"]
        
        success = False
        status_to_set = "ALERTED"
        
        if channel == "telegram":
            telegram_chat_id = plan.get("telegram_chat_id")
            # If not in plan, query it
            if not telegram_chat_id:
                donor_res = supabase.table("donors").select("telegram_chat_id").eq("donor_id", donor_id).execute()
                if donor_res.data:
                    telegram_chat_id = donor_res.data[0].get("telegram_chat_id")

            if telegram_chat_id:
                success = await send_outreach_message(telegram_chat_id, msg_val)
                status_to_set = "ALERTED"
            else:
                # SMS removed from MVP — log warning, donor will be retried via voice if configured
                logger.warning(
                    f"Donor {donor_id} has no Telegram chat_id and SMS is disabled. "
                    "They will receive a voice call if VAPI_PHONE_NUMBER_ID is configured."
                )
                success = False
                
        if "voice" in channel:
            # Voice calls placed by Vapi — register status as 'VOICE'
            success = True
            status_to_set = "VOICE"
            
        if success:
            alerted_count += 1
            # Update blood_chains table in Supabase
            supabase.table("blood_chains")\
                .update({
                    "status": status_to_set,
                    "alerted_at": datetime.now().isoformat()
                })\
                .eq("request_id", request_id)\
                .eq("donor_id", donor_id)\
                .execute()
                
            # Update Neo4j graph database edges status parameter to 'ALERTED'
            await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "ALERTED")
            
    # 4. Broadcast WebSocket {type:'outreach_sent', request_id, alerted_count}
    await ws_manager.broadcast({
        "type": "outreach_sent",
        "request_id": request_id,
        "alerted_count": alerted_count
    })
    
    duration = (time.perf_counter() - start_time) * 1000.0
    timings = state.get("node_timings", {}).copy()
    timings["outreach_node"] = round(duration, 2)
    
    # Log outreach metrics
    skipped_count = len(outreach_plan) - len(consented_plans)
    logger.info(f"OutreachAgent: {alerted_count}/{len(outreach_plan)} messages sent ({skipped_count} no-consent skipped)")
    
    # Update chain states in AgentState
    updated_chain = state.get("chain", []).copy()
    for node in updated_chain:
        for p in consented_plans:
            if node["donor_id"] == p["donor_id"]:
                if p["channel"] == "telegram":
                    node["status"] = "ALERTED"
                elif "voice" in p["channel"]:
                    node["status"] = "VOICE"
                node["alerted_at"] = datetime.now().isoformat()
                
    return {
        "chain": updated_chain,
        "non_consented_donors": non_consented_donors,
        "node_timings": timings
    }
