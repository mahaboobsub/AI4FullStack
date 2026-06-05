"""
Webhook API routes for BloodBridge AI (Telegram, Vapi, etc.).
"""
import asyncio
import logging
import random
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException

from core.config import get_settings
from core.database import get_supabase_admin
from api.websocket import ws_manager
from services.telegram_bot import (
    get_telegram_agent,
    get_user_context,
    handle_deterministic_chain_response,
    handle_command,
    handle_photo_onboarding,
    handle_registration_step
)
from langchain_core.messages import HumanMessage  # type: ignore[import]

logger = logging.getLogger(__name__)
router = APIRouter()

KNOWN_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    POST /webhook/telegram
    Hybrid routing controller webhook for Telegram Bot updates.
    """
    settings = get_settings()
    
    # 1. Webhook security signature check
    from core.security import verify_telegram_webhook
    if not verify_telegram_webhook(request, settings.TELEGRAM_WEBHOOK_SECRET):
        logger.warning("Telegram webhook signature verification failed.")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        return {"ok": False, "error": "Invalid JSON"}
        
    message = payload.get("message")
    if not message:
        return {"ok": True}
        
    chat = message.get("chat")
    if not chat:
        return {"ok": True}
        
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    
    # Send typing status
    from telegram import Bot  # type: ignore[import]
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
    if bot:
        try:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception as e:
            logger.warning(f"Failed to send typing chat action: {e}")
            
    # Fetch user role context
    user_context = await get_user_context(chat_id)
    
    # Route 1: Photo OCR handler (Onboarding)
    photo = message.get("photo")
    if photo:
        largest_photo = photo[-1]
        file_id = largest_photo.get("file_id")
        asyncio.create_task(handle_photo_onboarding(chat_id, file_id))
        return {"ok": True}

    # Route 1.5: Contact message handler (phone number capture)
    contact = message.get("contact")
    if contact:
        phone = contact.get("phone_number")
        if phone:
            supabase = get_supabase_admin()
            donor_res = supabase.table("donors").select("donor_id").eq("telegram_chat_id", str(chat_id)).execute()
            if donor_res.data:
                supabase.table("donors").update({"phone": phone}).eq("donor_id", donor_res.data[0]["donor_id"]).execute()
                if bot:
                    await bot.send_message(chat_id=chat_id, text=f"📱 Phone number *{phone}* saved to your profile. Thank you!", parse_mode="Markdown")
            else:
                if bot:
                    await bot.send_message(chat_id=chat_id, text="Please register first using /register to save your phone number.")
        return {"ok": True}

    # Route 1.6: Multi-turn registration flow interceptor
    reg_response = await handle_registration_step(chat_id, text)
    if reg_response:
        if bot:
            await bot.send_message(chat_id=chat_id, text=reg_response, parse_mode="Markdown")
        return {"ok": True}
        
    # Route 2: Deterministic route for active chain alerted replies (YES/NO/HAAN)
    if user_context.get("active_chain_status") == "ALERTED" and text.lower() in ['yes', 'haan', 'ha', 'ok', 'no', 'nahi']:
        await handle_deterministic_chain_response(chat_id, text, user_context)
        return {"ok": True}
        
    # Route 3: Consent onboarding flow for guests (new users replying YES/NO to starts)
    if user_context.get("role") == "Guest":
        if text.lower() in ['yes', 'haan', 'ha', 'ok']:
            # Create guest donor, grant consent
            supabase = get_supabase_admin()
            donor_id = f"D-{random.randint(10000, 99999)}"
            supabase.table("donors").insert({
                "donor_id": donor_id,
                "telegram_chat_id": str(chat_id),
                "name": f"Telegram Donor {str(chat_id)[-4:]}",
                "blood_type": "O+",  # Default placeholder
                "city": "Hyderabad",  # Default city
                "consent_outreach": True,
                "is_active": True
            }).execute()
            
            from services.consent_service import ConsentService
            await ConsentService.grant_consent(donor_id, ['data_storage', 'outreach_telegram'], channel='telegram', language='en')
            
            msg = "🎉 *Consent Granted & Onboarding Started!*\n\nThank you! We have registered your consent. To complete your registration and set your blood group, type: `/register [blood_type]` (e.g. `/register B+`)."
            if bot:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            return {"ok": True}
        elif text.lower() in ['no', 'nahi']:
            msg = "Understood. We will not store your data or contact you. Feel free to reach out to us if you change your mind."
            if bot:
                await bot.send_message(chat_id=chat_id, text=msg)
            return {"ok": True}
            
    # Route 4: Command routing deterministically
    if text.startswith("/"):
        parts = text.split()
        cmd: str = parts[0]
        args: list[str] = list(parts[1:])
        cmd_response = await handle_command(chat_id, cmd, args, user_context)
        if cmd_response:
            if bot:
                await bot.send_message(chat_id=chat_id, text=cmd_response, parse_mode="Markdown")
            else:
                logger.info(f"Mock command response to {chat_id}: {cmd_response}")
            return {"ok": True}
            
    # Route 5: Agentic NLP Route (Groq Llama tool-calling agent)
    agent = get_telegram_agent()
    if agent:
        try:
            # Format system-injected state context payload
            input_payload = f"[User Role: {user_context['role']}] [Language: {user_context['lang']}] [Name: {user_context['name']}] [Chat ID: {chat_id}] {text}"
            agent_state = {
                "messages": [HumanMessage(content=input_payload)]
            }
            
            result = await asyncio.wait_for(agent.ainvoke(agent_state), timeout=8.0)
            final_response = result["messages"][-1].content
        except asyncio.TimeoutError:
            final_response = "🩸 Namaste! I am currently assisting many donors. Please type /help for commands."
        except Exception as e:
            logger.error(f"Telegram React Agent execution failed: {e}", exc_info=True)
            final_response = "🩸 Namaste! I am currently assisting many donors. Please type /help for commands."
    else:
        # Fallback command menu in case LLM is unconfigured
        final_response = (
            f"🩸 Namaste *{user_context['name']}*!\n\n"
            f"I am the BloodBridge AI Assistant. Chat capabilities are currently running in command mode.\n\n"
            f"Available commands:\n"
            f"- /status [patient_id] - Check status\n"
            f"- /register [blood_type] - Register as donor\n"
            f"- /impact - View your impact\n"
            f"- /leaderboard - View city leaderboard"
        )
        
    if bot:
        await bot.send_message(chat_id=chat_id, text=final_response, parse_mode="Markdown")
    else:
        logger.info(f"Mock bot text response to {chat_id}: {final_response}")
        
    return {"ok": True}


@router.post("/webhook/bolna/call-result")
async def bolna_webhook(request: Request):
    """
    POST /webhook/bolna/call-result
    Handles Bolna.ai call completion webhook.

    Bolna sends a JSON payload on call completion with:
      - call_id: unique call identifier
      - status: 'completed' | 'failed' | 'no-answer' | 'busy'
      - transcript: full call transcript text
      - metadata: dict passed in user_data at call creation (contains request_id, donor_id)

    Webhook secret verification is done via X-Bolna-Secret header.
    """
    settings = get_settings()

    # 1. Webhook security check
    if settings.APP_ENV == "production" and settings.BOLNA_WEBHOOK_SECRET:
        incoming_secret = request.headers.get("X-Bolna-Secret", "")
        if incoming_secret != settings.BOLNA_WEBHOOK_SECRET:
            logger.warning("Bolna webhook secret mismatch — request rejected.")
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Bolna webhook JSON: {e}")
        return {"ok": False, "error": "Invalid JSON"}

    status = body.get("status", "")
    call_id = body.get("call_id", "")
    transcript = body.get("transcript", "") or ""
    metadata = body.get("metadata") or body.get("user_data", {}) or {}

    request_id = metadata.get("request_id")
    donor_id = metadata.get("donor_id")

    logger.info(
        f"Bolna webhook received: call_id={call_id} status={status} "
        f"request={request_id} donor={donor_id}"
    )

    # Only process completed calls
    if status not in ("completed", "ended"):
        logger.info(f"Bolna call {call_id} status={status} — no action needed.")
        return {"ok": True}

    if not request_id or not donor_id:
        logger.warning(f"Bolna webhook missing metadata: {metadata}")
        return {"ok": True}

    # NLU keyword matching on transcript (same logic as before)
    YES_KEYWORDS = ["yes", "haan", "ha", "ji haan", "okay", "ok", "thik", "aane", "aamaa", "1", "haa",
                    "avunu", "aamam", "haudo", "aanu", "aamaa"]
    NO_KEYWORDS  = ["no", "nahi", "na", "nahi aata", "illay", "illai", "2", "nako", "kadu", "illa", "aar"]

    transcript_lower = transcript.lower()
    is_yes = any(kw in transcript_lower for kw in YES_KEYWORDS)
    is_no  = any(kw in transcript_lower for kw in NO_KEYWORDS)

    supabase = get_supabase_admin()

    chain_res = supabase.table("blood_chains")\
        .select("*")\
        .eq("request_id", request_id)\
        .eq("donor_id", donor_id)\
        .execute()

    if not chain_res.data:
        logger.warning(f"Bolna webhook: No chain node for request={request_id} donor={donor_id}")
        return {"ok": True}

    active_node = chain_res.data[0]
    pos = active_node["chain_position"]

    req_res = supabase.table("emergency_requests").select("patient_id").eq("request_id", request_id).execute()
    patient_id: str = str(req_res.data[0]["patient_id"]) if req_res.data else ""

    from services.telegram_bot import run_repair_in_background
    result_str = "unclear"

    if is_yes:
        result_str = "confirmed"
        # Re-check eligibility before confirming
        p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
        patient = p_res.data[0] if p_res.data else {}
        donor_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
        donor = donor_res.data[0] if donor_res.data else {}

        from ml.eligibility_filter import check_donor_eligibility
        elig = check_donor_eligibility(donor, patient)

        if not elig["eligible"]:
            logger.info(f"Bolna: Donor {donor_id} said YES but failed eligibility: {elig['reason']}")
            supabase.table("blood_chains")\
                .update({"status": "DECLINED", "notes": f"eligibility_failed: {elig['reason']}",
                         "declined_at": datetime.now(timezone.utc).isoformat() + "Z"})\
                .eq("request_id", request_id).eq("donor_id", donor_id).execute()
            from agents.neo4j_match import Neo4jMatcher
            await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "DECLINED")
            asyncio.create_task(run_repair_in_background(request_id, patient_id, pos))
        else:
            supabase.table("blood_chains")\
                .update({"status": "CONFIRMED",
                         "confirmed_at": datetime.now(timezone.utc).isoformat() + "Z"})\
                .eq("request_id", request_id).eq("donor_id", donor_id).execute()
            from agents.neo4j_match import Neo4jMatcher
            await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "CONFIRMED")
            from services.donor_memory import update_memory_after_interaction
            await update_memory_after_interaction(donor_id, "confirmed", {})
            await ws_manager.broadcast({
                "type": "donor_confirmed",
                "request_id": request_id,
                "donor_name": donor.get("name", "Donor"),
                "position": pos
            })

    elif is_no:
        result_str = "declined"
        supabase.table("blood_chains")\
            .update({"status": "DECLINED",
                     "declined_at": datetime.now(timezone.utc).isoformat() + "Z"})\
            .eq("request_id", request_id).eq("donor_id", donor_id).execute()
        from agents.neo4j_match import Neo4jMatcher
        await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "DECLINED")
        from services.donor_memory import update_memory_after_interaction
        await update_memory_after_interaction(donor_id, "declined", {})
        await ws_manager.broadcast({
            "type": "donor_declined",
            "request_id": request_id,
            "donor_name": active_node.get("donor_name", "Donor"),
            "position": pos
        })
        asyncio.create_task(run_repair_in_background(request_id, patient_id, pos))

    else:
        # No clear yes/no — treat as declined and trigger repair
        result_str = "unclear"
        supabase.table("blood_chains")\
            .update({"status": "DECLINED", "notes": "Bolna call: response unclear/no-answer",
                     "declined_at": datetime.now(timezone.utc).isoformat() + "Z"})\
            .eq("request_id", request_id).eq("donor_id", donor_id).execute()
        from agents.neo4j_match import Neo4jMatcher
        await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "DECLINED")
        asyncio.create_task(run_repair_in_background(request_id, patient_id, pos))

    await ws_manager.broadcast({
        "type": "voice_call_result",
        "donor_id": donor_id,
        "call_id": call_id,
        "result": result_str,
        "provider": "bolna"
    })

    return {"ok": True}
