"""
Donor memory module for BloodBridge AI.
"""
import logging
from datetime import datetime, date
from core.database import get_supabase_admin
from services.language_service import detect_dominant_language

logger = logging.getLogger(__name__)

async def get_memory(donor_id: str) -> dict:
    """Fetch from Supabase donor_memory. Return defaults if new donor."""
    supabase = get_supabase_admin()
    try:
        res = supabase.table("donor_memory").select("*").eq("donor_id", donor_id).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        logger.error(f"Error fetching memory for {donor_id}: {e}")
        
    return {
        "donor_id": donor_id,
        "preferred_language": "Hindi",
        "tone_profile": "warm",
        "emotional_anchors": [],
        "last_interaction": None,
        "total_interactions": 0,
        "badges": [],
        "streak_days": 0,
        "last_response_time_secs": None,
        "impact_story": None,
        "last_story_date": None
    }

async def update_memory_after_interaction(donor_id: str, interaction_type: str, metadata: dict):
    """
    interaction_type: outreach_sent|confirmed|declined|badge_earned|voice_call  
    Updates: total_interactions, last_interaction, streak_days(if confirmed),  
    tone_profile(shift to formal after 3 declines), badges, last_response_time_secs
    """
    supabase = get_supabase_admin()
    now_str = datetime.utcnow().isoformat() + "Z"
    
    try:
        mem = await get_memory(donor_id)
        total_int = mem.get("total_interactions", 0) + 1
        streak = mem.get("streak_days", 0)
        tone = mem.get("tone_profile", "warm")
        badges = mem.get("badges", [])
        
        # Track declines in metadata or count from history to shift tone profile
        if interaction_type == "confirmed":
            streak += 30
            tone = "warm" # reset to warm on confirm
        elif interaction_type == "declined":
            # If donor declined, let's increment decline count in metadata
            # and if consecutive declines >= 3, shift tone to formal
            consecutive_declines = metadata.get("consecutive_declines", 0)
            if consecutive_declines >= 3:
                tone = "formal"
                
        if interaction_type == "badge_earned":
            badge_name = metadata.get("badge_name")
            if badge_name and badge_name not in badges:
                badges.append(badge_name)
                
        last_resp = metadata.get("response_time_secs", mem.get("last_response_time_secs"))
        
        supabase.table("donor_memory").upsert({
            "donor_id": donor_id,
            "preferred_language": mem.get("preferred_language", "Hindi"),
            "tone_profile": tone,
            "emotional_anchors": mem.get("emotional_anchors", []),
            "last_interaction": now_str,
            "total_interactions": total_int,
            "badges": badges,
            "streak_days": streak,
            "last_response_time_secs": last_resp
        }).execute()
        
        logger.info(f"Updated donor memory for {donor_id} after {interaction_type}")
    except Exception as e:
        logger.error(f"Failed to update donor memory for {donor_id}: {e}", exc_info=True)

async def build_memory_context_for_llm(donor_id: str) -> str:
    """Compact context string for injection into Groq/Gemini prompts."""
    supabase = get_supabase_admin()
    name = "Unknown Donor"
    lang = "Hindi"
    donations = 0
    response_rate = 50
    days_ago_str = "no previous donations"
    streak_str = "0 days"
    
    try:
        donor_res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
        if donor_res.data:
            donor = donor_res.data[0]
            name = donor.get("name", "Unknown Donor")
            lang = donor.get("preferred_language", "Hindi")
            donations = donor.get("donation_count", 0)
            rate_val = donor.get("response_rate", 0.5)
            response_rate = int(rate_val * 100) if rate_val <= 1.0 else int(rate_val)
            
            last_date = donor.get("last_donation_date")
            if last_date:
                try:
                    delta = (date.today() - date.fromisoformat(str(last_date))).days
                    days_ago_str = f"{delta} days ago"
                except Exception:
                    days_ago_str = "unknown days ago"
    except Exception as e:
        logger.error(f"Error fetching donor info for build_memory_context: {e}")
        
    mem = await get_memory(donor_id)
    tone = mem.get("tone_profile", "warm")
    anchors = mem.get("emotional_anchors", []) or []
    anchors_str = ", ".join(anchors) if anchors else "None"
    
    streak_days = mem.get("streak_days", 0)
    if streak_days >= 30:
        streak_str = f"{streak_days // 30} months"
    else:
        streak_str = f"{streak_days} days"
        
    context = (
        f"Donor: {name} | Language: {lang} | Tone: {tone} | Anchors: [{anchors_str}]\n"
        f"{donations} donations, {response_rate}% response rate, {days_ago_str} | Streak: {streak_str}"
    )
    return context

async def detect_and_update_language(donor_id: str, message_text: str):
    """
    langdetect on incoming message. Update preferred_language if confidence > 0.8.  
    Only languages: hi,te,ta,en,kn,ml,mr,bn,gu,pa
    """
    supported_langs = {'hi', 'te', 'ta', 'en', 'kn', 'ml', 'mr', 'bn', 'gu', 'pa'}
    if not message_text or len(message_text.strip()) < 5:
        return
        
    try:
        detected = detect_dominant_language(message_text)
        if detected in supported_langs:
            supabase = get_supabase_admin()
            supabase.table("donors").update({"preferred_language": detected}).eq("donor_id", donor_id).execute()
            supabase.table("donor_memory").upsert({"donor_id": donor_id, "preferred_language": detected}).execute()
            logger.info(f"Updated preferred language for {donor_id} to {detected}")
    except Exception as e:
        logger.warning(f"Language detection failed for donor {donor_id}: {e}")

async def add_emotional_anchor(donor_id: str, anchor: str):
    """Append anchor. Max 5 kept (oldest removed). Used in future outreach personalization."""
    supabase = get_supabase_admin()
    try:
        mem = await get_memory(donor_id)
        anchors = mem.get("emotional_anchors", []) or []
        if anchor not in anchors:
            anchors.append(anchor)
            if len(anchors) > 5:
                anchors.pop(0)
            supabase.table("donor_memory").upsert({
                "donor_id": donor_id,
                "emotional_anchors": anchors
            }).execute()
            logger.info(f"Added emotional anchor for donor {donor_id}: {anchor}")
    except Exception as e:
        logger.error(f"Failed to add emotional anchor for donor {donor_id}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# B4 — FAILURE-LEARNING & SELF-IMPROVING OUTREACH
# ═══════════════════════════════════════════════════════════════════════════════

FAILURE_REASONS = [
    "wrong_channel", "wrong_time", "message_too_long",
    "fatigue_from_calls", "donor_busy", "no_response", "unknown"
]

async def analyze_response_and_update(
    donor_id: str,
    outcome: str,
    channel: str,
    response_time_seconds: int = None,
    message_text: str = None
):
    """
    B4: Classify failure, update tone_profile, emotional_anchors,
    optimal_contact_window, best_channel via Bedrock Claude Haiku.
    """
    supabase = get_supabase_admin()
    mem = await get_memory(donor_id)

    # Get IST time bucket
    from datetime import timezone, timedelta as td
    import datetime as dt_module
    ist = timezone(td(hours=5, minutes=30))
    now_ist = dt_module.datetime.now(ist)
    hour = now_ist.hour
    if 6 <= hour < 12:
        time_bucket = "morning"
    elif 12 <= hour < 17:
        time_bucket = "afternoon"
    elif 17 <= hour < 21:
        time_bucket = "evening"
    else:
        time_bucket = "night"

    # Try Bedrock for classification
    failure_reason = "unknown"
    updated_tone = mem.get("tone_profile", "warm")
    new_anchor = None
    best_channel = channel
    contact_window = time_bucket

    if outcome != "CONFIRMED":
        try:
            from core.llm_provider import get_reasoning_llm
            llm = get_reasoning_llm()

            prompt = (
                f"A blood donor {outcome.lower()} a donation request.\n"
                f"Channel: {channel}, Time: {time_bucket}, Response time: {response_time_seconds}s\n"
                f"Current tone: {mem.get('tone_profile')}, Message: {message_text or 'N/A'}\n\n"
                f"Return JSON with: tone_profile (warm/urgent/factual/inspirational), "
                f"failure_reason (one of: {FAILURE_REASONS}), "
                f"optimal_contact_window (morning/afternoon/evening), "
                f"best_channel (telegram/voice/sms), "
                f"emotional_anchor (string or null)"
            )

            response = llm.invoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)

            # Try to parse JSON from response
            import json
            import re
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                parsed = json.loads(json_match.group())
                failure_reason = parsed.get("failure_reason", "unknown")
                updated_tone = parsed.get("tone_profile", updated_tone)
                new_anchor = parsed.get("emotional_anchor")
                best_channel = parsed.get("best_channel", channel)
                contact_window = parsed.get("optimal_contact_window", time_bucket)
        except Exception as e:
            logger.warning(f"B4 Bedrock classification failed for {donor_id}: {e}")
            # Heuristic fallback
            if outcome == "NO_RESPONSE" and channel == "voice":
                failure_reason = "wrong_channel"
            elif outcome == "DECLINED":
                failure_reason = "donor_busy"

    # Update donor_memory
    update_data = {
        "donor_id": donor_id,
        "tone_profile": updated_tone,
        "optimal_contact_window": contact_window,
        "best_channel": best_channel,
        "last_interaction": datetime.utcnow().isoformat() + "Z"
    }

    if new_anchor:
        anchors = mem.get("emotional_anchors", []) or []
        if new_anchor not in anchors:
            anchors.append(new_anchor)
            if len(anchors) > 5:
                anchors.pop(0)
            update_data["emotional_anchors"] = anchors

    try:
        supabase.table("donor_memory").upsert(update_data).execute()
    except Exception as e:
        logger.error(f"B4 memory update failed for {donor_id}: {e}")

    # Update outreach_protocol_stats
    try:
        supabase.table("outreach_protocol_stats").insert({
            "channel": channel,
            "time_of_day": time_bucket,
            "blood_type": None,  # Could be enriched
            "outcome": outcome,
            "failure_reason": failure_reason if outcome != "CONFIRMED" else None,
            "donor_id": donor_id,
            "recorded_at": datetime.utcnow().isoformat() + "Z"
        }).execute()
    except Exception:
        logger.warning(f"outreach_protocol_stats table may not exist for {donor_id}")

    # Recompute response_rate for this donor
    try:
        chains_res = supabase.table("blood_chains")\
            .select("status")\
            .eq("donor_id", donor_id)\
            .execute()
        total = len(chains_res.data or [])
        confirmed = sum(1 for c in (chains_res.data or []) if c["status"] in ["CONFIRMED", "COMPLETED"])
        if total > 0:
            new_rate = round(confirmed / total, 4)
            supabase.table("donors").update({"response_rate": new_rate}).eq("donor_id", donor_id).execute()
    except Exception:
        pass

    logger.info(f"B4: Analyzed {outcome} for donor {donor_id}: reason={failure_reason}, tone={updated_tone}")
    return {"failure_reason": failure_reason, "tone_profile": updated_tone}

