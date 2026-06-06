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

    # Initialize bot early — needed for both callback queries and messages
    from telegram import Bot  # type: ignore[import]
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None

    # Handle callback queries (Inline Buttons) BEFORE checking for message,
    # because callback_query updates do NOT have a top-level "message" key.
    callback_query = payload.get("callback_query")
    if callback_query:
        cq_data = callback_query.get("data")
        cq_chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        
        if cq_data in ["consent_yes", "consent_no"]:
            from services.consent_service import ConsentService
            user_ctx = await get_user_context(cq_chat_id)
            if cq_data == "consent_yes":
                if user_ctx.get("role") == "Guest":
                    supabase = get_supabase_admin()
                    donor_id = f"D-{random.randint(10000, 99999)}"
                    supabase.table("donors").insert({
                        "donor_id": donor_id,
                        "telegram_chat_id": str(cq_chat_id),
                        "name": f"Telegram Donor {str(cq_chat_id)[-4:]}",
                        "blood_type": "O+",
                        "city": "Hyderabad",
                        "consent_outreach": True,
                        "is_active": True
                    }).execute()
                    await ConsentService.grant_consent(donor_id, ['data_storage', 'outreach_telegram'], channel='telegram', language='en')
                else:
                    d_id = user_ctx.get("donor_id")
                    if d_id:
                        await ConsentService.grant_consent(d_id, ['data_storage', 'outreach_telegram'], channel='telegram', language='en')
                
                msg = "🎉 *Consent Granted!*\n\nTo complete your registration, type: `/register [blood_type]` (e.g. `/register B+`)."
                if bot:
                    await bot.send_message(chat_id=cq_chat_id, text=msg, parse_mode="Markdown")
            else:
                msg = "Understood. We will not store your data or contact you."
                if bot:
                    await bot.send_message(chat_id=cq_chat_id, text=msg)
            # Answer the callback query to remove the "loading" spinner on the button
            if bot:
                try:
                    await bot.answer_callback_query(callback_query_id=callback_query["id"])
                except Exception as e:
                    logger.warning(f"Failed to answer callback query: {e}")
            return {"ok": True}

        # TC-036/037: Handle outreach chain YES/NO inline button responses
        if cq_data in ["chain_yes", "chain_no"]:
            from datetime import datetime, timezone
            user_ctx = await get_user_context(str(cq_chat_id))
            donor_id = user_ctx.get("donor_id")
            
            if not donor_id:
                if bot:
                    await bot.send_message(chat_id=cq_chat_id, text="You are not registered as a donor.")
                    try:
                        await bot.answer_callback_query(callback_query_id=callback_query["id"])
                    except Exception:
                        pass
                return {"ok": True}
            
            # Find the active ALERTED chain node for this donor
            supabase = get_supabase_admin()
            chain_res = supabase.table("blood_chains")\
                .select("*")\
                .eq("donor_id", donor_id)\
                .eq("status", "ALERTED")\
                .execute()
            
            if not chain_res.data:
                if bot:
                    await bot.send_message(chat_id=cq_chat_id, text="No active donation request found for you right now.")
                    try:
                        await bot.answer_callback_query(callback_query_id=callback_query["id"])
                    except Exception:
                        pass
                return {"ok": True}
            
            active_node = chain_res.data[0]
            request_id = active_node["request_id"]
            pos = active_node["chain_position"]
            
            # Resolve patient_id
            req_res = supabase.table("emergency_requests").select("patient_id").eq("request_id", request_id).execute()
            patient_id: str = str(req_res.data[0]["patient_id"]) if req_res.data else ""
            
            if not patient_id:
                logger.warning(f"Could not resolve patient_id for chain request {request_id}")
                if bot:
                    await bot.send_message(chat_id=cq_chat_id, text="Unable to process — request data not found.")
                    try:
                        await bot.answer_callback_query(callback_query_id=callback_query["id"])
                    except Exception:
                        pass
                return {"ok": True}
            
            if cq_data == "chain_yes":
                # Re-validate eligibility
                p_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
                patient = p_res.data[0] if p_res.data else {}
                donor_full = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
                donor_profile = donor_full.data[0] if donor_full.data else {}
                
                from ml.eligibility_filter import check_donor_eligibility
                elig = check_donor_eligibility(donor_profile, patient)
                
                if not elig["eligible"]:
                    supabase.table("blood_chains")\
                        .update({"status": "DECLINED", "notes": f"eligibility_failed: {elig['reason']}",
                                 "declined_at": datetime.now(timezone.utc).isoformat() + "Z"})\
                        .eq("request_id", request_id).eq("donor_id", donor_id).execute()
                    from agents.neo4j_match import Neo4jMatcher
                    await Neo4jMatcher.update_chain_status(request_id, donor_id, patient_id, "DECLINED")
                    if bot:
                        await bot.send_message(chat_id=cq_chat_id, text=f"Thank you for willing to help! Unfortunately, you are not eligible right now: {elig['reason']}")
                    from services.telegram_bot import run_repair_in_background
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
                        "donor_name": donor_profile.get("name", "Donor"),
                        "position": pos
                    })
                    if bot:
                        await bot.send_message(chat_id=cq_chat_id, text="🩸 *Thank you!* Your donation is confirmed. The hospital staff has been notified. We will contact you with scheduling details.", parse_mode="Markdown")
            else:
                # chain_no — Decline
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
                    "donor_name": user_ctx.get("name", "Donor"),
                    "position": pos
                })
                if bot:
                    await bot.send_message(chat_id=cq_chat_id, text="Understood. We have noted your response. Thank you for considering!")
                from services.telegram_bot import run_repair_in_background
                asyncio.create_task(run_repair_in_background(request_id, patient_id, pos))
            
            # Answer callback to remove spinner
            if bot:
                try:
                    await bot.answer_callback_query(callback_query_id=callback_query["id"])
                except Exception as e:
                    logger.warning(f"Failed to answer callback query: {e}")
            return {"ok": True}

        return {"ok": True}

    message = payload.get("message")
    if not message:
        return {"ok": True}
        
    chat = message.get("chat")
    if not chat:
        return {"ok": True}
        
    chat_id = str(chat.get("id"))
    text = (message.get("text") or "").strip()
    
    # Send typing status
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
        
        # TC-004: /start for already-consented registered donor → personalized welcome, no consent prompt
        if cmd == "/start":
            from services.consent_service import ConsentService
            d_id = user_context.get("donor_id")
            if d_id and user_context.get("role") == "Donor":
                has_st = await ConsentService.check_consent(d_id, "data_storage")
                has_out = await ConsentService.check_consent(d_id, "outreach_telegram")
                if has_st and has_out:
                    # Already consented — show personalized dashboard instead of consent prompt
                    donor_profile = user_context.get("donor_profile", {})
                    name = donor_profile.get("name", user_context.get("name", "Donor"))
                    blood_type = donor_profile.get("blood_type", "N/A")
                    donation_count = donor_profile.get("donation_count", 0)
                    lives_saved = donor_profile.get("lives_saved", 0)
                    
                    # Fetch streak from donor_memory
                    from services.donor_memory import get_memory
                    mem = await get_memory(d_id)
                    streak = mem.get("streak_days", 0)
                    last_donation = donor_profile.get("last_donation_date", "Never")
                    
                    welcome = (
                        f"🩸 *Welcome back, {name}!*\n\n"
                        f"📊 *Your Dashboard:*\n"
                        f"- Blood Type: *{blood_type}*\n"
                        f"- Donations: *{donation_count}*\n"
                        f"- Lives Saved: *{lives_saved}* 🏆\n"
                        f"- Streak: *{streak} days* 🔥\n"
                        f"- Last Donation: *{last_donation}*\n\n"
                        f"Type /help to see all available commands."
                    )
                    if bot:
                        await bot.send_message(chat_id=chat_id, text=welcome, parse_mode="Markdown")
                    return {"ok": True}

        # TC-005: Consent Gateway — block ALL commands (except /start, /help) for users without consent
        if cmd not in ["/start", "/help"]:
            from services.consent_service import ConsentService
            d_id = user_context.get("donor_id")
            has_consent = False
            if d_id:
                has_st = await ConsentService.check_consent(d_id, "data_storage")
                has_out = await ConsentService.check_consent(d_id, "outreach_telegram")
                has_consent = has_st and has_out
            
            if not has_consent:
                # Block: either Guest (no donor_id) or donor without consent
                if bot:
                    from telegram import InlineKeyboardMarkup, InlineKeyboardButton # type: ignore
                    markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Yes, I agree", callback_data="consent_yes")],
                        [InlineKeyboardButton("❌ No, I decline", callback_data="consent_no")]
                    ])
                    await bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ *Please complete consent setup first.*\n\nUnder the DPDP Act 2023, we need your consent before you can use any commands.",
                        parse_mode="Markdown",
                        reply_markup=markup
                    )
                return {"ok": True}

        cmd_response = await handle_command(chat_id, cmd, args, user_context)
        if cmd_response:
            if bot:
                if cmd == "/start":
                    # Only guests/new users reach here — show consent buttons
                    from telegram import InlineKeyboardMarkup, InlineKeyboardButton # type: ignore
                    markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Yes, I agree", callback_data="consent_yes")],
                        [InlineKeyboardButton("❌ No, I decline", callback_data="consent_no")]
                    ])
                    await bot.send_message(chat_id=chat_id, text=cmd_response, parse_mode="Markdown", reply_markup=markup)
                else:
                    await bot.send_message(chat_id=chat_id, text=cmd_response, parse_mode="Markdown")
            else:
                logger.info(f"Mock command response to {chat_id}: {cmd_response}")
            return {"ok": True}
            
    # Route 5: Agentic NLP Route (Bedrock Nova Lite custom loop)
    # TC-006: Consent Gateway — block ALL natural language before consent (guests + unconsented donors)
    from services.consent_service import ConsentService
    donor_id = user_context.get("donor_id")
    has_consent = False
    if donor_id:
        has_storage = await ConsentService.check_consent(donor_id, "data_storage")
        has_outreach = await ConsentService.check_consent(donor_id, "outreach_telegram")
        has_consent = has_storage and has_outreach

    if not has_consent:
        if bot:
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton # type: ignore
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, I agree", callback_data="consent_yes")],
                [InlineKeyboardButton("❌ No, I decline", callback_data="consent_no")]
            ])
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ *Please complete consent setup first.*\n\nUnder the DPDP Act 2023, we need your consent before you can use BloodBridge AI.\n\nSend /start to begin.",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return {"ok": True}

    from services.telegram_bot import handle_message
    try:
        final_response = await asyncio.wait_for(handle_message(str(chat_id), text, user_context), timeout=25.0)
    except asyncio.TimeoutError:
        final_response = "🩸 Namaste! I am currently assisting many donors. Please type /help for commands."
    except Exception as e:
        logger.error(f"Telegram Bedrock loop failed: {e}", exc_info=True)
        final_response = "🩸 Namaste! I am currently assisting many donors. Please type /help for commands."
        
    if bot:
        # Strip ANY hallucinated tool-call XML/markup the LLM might leak into prose
        import re as _re
        cleaned = final_response
        # Multi-line tag pairs
        for pattern in [
            r"<functioncalls>.*?</functioncalls>",
            r"<function_calls>.*?</function_calls>",
            r"<invoke>.*?</invoke>",
            r"<tool_use>.*?</tool_use>",
            r"<tool_call>.*?</tool_call>",
            r"<parameters>.*?</parameters>",
            r"<parameter>.*?</parameter>",
        ]:
            cleaned = _re.sub(pattern, "", cleaned, flags=_re.DOTALL | _re.IGNORECASE)
        # Standalone tags (no closing) — catch leftover stragglers
        cleaned = _re.sub(r"</?(?:functioncalls?|function_calls?|invoke|tool_use|tool_call|parameters?|toolname)\b[^>]*>", "", cleaned, flags=_re.IGNORECASE)
        # Collapse repeated whitespace + newlines from stripped content
        cleaned = _re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = _re.sub(r" {2,}", " ", cleaned)
        cleaned = cleaned.strip() or "I'm here to help. Try /help for available commands."

        # Use plain text by default — avoid Telegram Markdown parse failures
        try:
            await bot.send_message(chat_id=chat_id, text=cleaned)
        except Exception as send_err:
            logger.error(f"Telegram send failed: {send_err}")
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
