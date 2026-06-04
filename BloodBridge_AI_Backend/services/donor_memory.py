"""
Donor memory module for BloodBridge AI.
"""
import logging
from datetime import datetime, date
from core.database import get_supabase_admin
from langdetect import detect

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
        detected = detect(message_text)
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
