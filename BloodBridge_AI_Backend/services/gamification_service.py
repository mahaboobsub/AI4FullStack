"""
Gamification Service for BloodBridge AI.
Manages donor badges, milestones, city leaderboards, and localized notifications.
"""
import logging
from datetime import datetime
from core.database import get_supabase_admin
from core.config import get_settings
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)

BADGES = {
    'blood_starter': {
        'name': 'Blood Starter',
        'emoji': '🌱',
        'threshold_type': 'donation_count',
        'threshold': 1,
        'message_hi': 'Shukriya! Pehli baar donate kiya! 🌱',
        'message_te': 'ధన్యవాదాలు! మొదటిసారి donate చేసారు! 🌱',
        'message_en': 'Thank you! Your first donation starts an incredible journey! 🌱'
    },
    'life_saver': {
        'name': 'Life Saver',
        'emoji': '❤️',
        'threshold_type': 'donation_count',
        'threshold': 5,
        'message_hi': '5 zindagiyan bachayi! ❤️',
        'message_te': '5 ప్రాణాలు కాపాడారు! ❤️',
        'message_en': 'Amazing! You have saved 5 lives with your donations! ❤️'
    },
    'blood_hero': {
        'name': 'Blood Hero',
        'emoji': '🦸',
        'threshold_type': 'donation_count',
        'threshold': 10,
        'message_hi': 'Blood Hero! 10 donate karke itihash! 🦸',
        'message_te': 'బ్లడ్ హీరో! 10 సార్లు దానం చేసి చరిత్ర సృష్టించారు! 🦸',
        'message_en': 'Blood Hero! You have made history by donating 10 times! 🦸'
    },
    'rare_guardian': {
        'name': 'Rare Guardian',
        'emoji': '💎',
        'message_hi': 'Rare Guardian! Rare Kell negative blood group donate kiya! 💎',
        'message_te': 'రేర్ గార్డియన్! అరుదైన బ్లడ్ గ్రూప్ దానం చేసారు! 💎',
        'message_en': 'Rare Guardian! Thank you for protecting lives with your rare Kell-negative blood group! 💎'
    },
    'city_champion': {
        'name': 'City Champion',
        'emoji': '🏆',
        'message_hi': 'City Champion! Aap apne sheher mein number 1 rank par hain! 🏆',
        'message_te': 'సిటీ ఛాంపియన్! మీరు మీ నగరంలో నంబర్ 1 స్థానంలో ఉన్నారు! 🏆',
        'message_en': 'City Champion! You are ranked #1 in your city! 🏆'
    },
    'crisis_hero': {
        'name': 'Crisis Hero',
        'emoji': '⚡',
        'message_hi': 'Crisis Hero! Critical alert ke 2 ghante ke andar confirm kiya! ⚡',
        'message_te': 'క్రైసిస్ హీరో! అత్యవసర సమయంలో 2 గంటల్లో స్పందించారు! ⚡',
        'message_en': 'Crisis Hero! Thank you for responding within 2 hours of a critical alert! ⚡'
    }
}

async def check_and_award_badges(donor_id: str, donor: dict = None) -> list[str]:
    """
    Check all gamification rules, award new badges, insert into gamification,
    and update donor_memory.
    """
    supabase = get_supabase_admin()
    now_str = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Fetch donor if not provided
        if not donor:
            res_donor = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
            if not res_donor.data:
                return []
            donor = res_donor.data[0]
            
        donation_count = donor.get("donation_count", 0)
        
        # Fetch existing badges for this donor
        res_gam = supabase.table("gamification").select("badge_name").eq("donor_id", donor_id).execute()
        existing_badges = {b["badge_name"].lower().replace(" ", "_") for b in res_gam.data} if res_gam.data else set()
        
        awarded_keys = []
        
        # 1. Blood Starter
        if 'blood_starter' not in existing_badges and donation_count >= 1:
            awarded_keys.append('blood_starter')
            
        # 2. Life Saver
        if 'life_saver' not in existing_badges and donation_count >= 5:
            awarded_keys.append('life_saver')
            
        # 3. Blood Hero
        if 'blood_hero' not in existing_badges and donation_count >= 10:
            awarded_keys.append('blood_hero')
            
        # 4. Rare Guardian
        if 'rare_guardian' not in existing_badges:
            kell_neg = donor.get("kell_negative", False)
            if kell_neg and donation_count >= 3:
                awarded_keys.append('rare_guardian')
                
        # 5. City Champion
        if 'city_champion' not in existing_badges:
            # Query rank of donor in city
            month_year = datetime.utcnow().strftime("%Y-%m")
            res_rank = supabase.table("leaderboard_cache")\
                .select("rank")\
                .eq("donor_id", donor_id)\
                .eq("city", donor.get("city", ""))\
                .eq("month_year", month_year)\
                .execute()
            if res_rank.data and res_rank.data[0].get("rank") == 1:
                awarded_keys.append('city_champion')
                
        # 6. Crisis Hero
        if 'crisis_hero' not in existing_badges:
            res_chains = supabase.table("blood_chains")\
                .select("alerted_at, confirmed_at, request_id")\
                .eq("donor_id", donor_id)\
                .eq("status", "CONFIRMED")\
                .execute()
                
            is_crisis_hero = False
            for chain in (res_chains.data or []):
                alerted = chain.get("alerted_at")
                confirmed = chain.get("confirmed_at")
                req_id = chain.get("request_id")
                
                if alerted and confirmed and req_id:
                    try:
                        # Check priority of request
                        res_req = supabase.table("emergency_requests")\
                            .select("priority")\
                            .eq("request_id", req_id)\
                            .execute()
                        priority = res_req.data[0].get("priority") if res_req.data else "ROUTINE"
                        
                        if priority == "CRITICAL":
                            # Parse dates and check <= 2 hours (7200 seconds)
                            t_alert = datetime.fromisoformat(alerted.replace("Z", "+00:00"))
                            t_confirm = datetime.fromisoformat(confirmed.replace("Z", "+00:00"))
                            diff = (t_confirm - t_alert).total_seconds()
                            if diff <= 7200:
                                is_crisis_hero = True
                                break
                    except Exception as ex:
                        logger.warning(f"Error parsing chain timing: {ex}")
                        
            if is_crisis_hero:
                awarded_keys.append('crisis_hero')
                
        # Award badges in database
        lang = donor.get("preferred_language", "en")
        for key in awarded_keys:
            badge_info = BADGES[key]
            # Insert into gamification
            supabase.table("gamification").insert({
                "donor_id": donor_id,
                "badge_name": badge_info["name"],
                "badge_emoji": badge_info["emoji"],
                "threshold": badge_info.get("threshold", 0),
                "awarded_at": now_str,
                "notified": True
            }).execute()
            
            # Fetch existing badges in donor_memory to update the array
            mem_res = supabase.table("donor_memory").select("badges").eq("donor_id", donor_id).execute()
            mem_badges = mem_res.data[0].get("badges", []) if mem_res.data else []
            if badge_info["name"] not in mem_badges:
                mem_badges.append(badge_info["name"])
                supabase.table("donor_memory").upsert({
                    "donor_id": donor_id,
                    "badges": mem_badges
                }).execute()
                
            # Send notification
            await send_badge_notification(donor_id, key, lang)
            
        return [BADGES[k]["name"] for k in awarded_keys]
    except Exception as e:
        logger.error(f"Error checking and awarding badges for donor {donor_id}: {e}", exc_info=True)
        return []

async def send_badge_notification(donor_id: str, badge_name: str, language: str):
    """
    Sends Telegram notification of earned badge in donor's preferred language.
    """
    supabase = get_supabase_admin()
    try:
        # Fetch Telegram chat ID
        res = supabase.table("donors").select("telegram_chat_id").eq("donor_id", donor_id).execute()
        if not res.data or not res.data[0].get("telegram_chat_id"):
            return
            
        chat_id = res.data[0]["telegram_chat_id"]
        badge_info = BADGES.get(badge_name)
        if not badge_info:
            return
            
        lang_key = (language or "en").lower()[:2]
        msg_key = f"message_{lang_key}"
        # Fallback to English, then Hindi
        notification_text = badge_info.get(msg_key, badge_info.get("message_en", badge_info.get("message_hi", "")))
        
        full_msg = f"🏆 *New Badge Awarded!*\n\n{notification_text}"
        await send_telegram_message(chat_id, full_msg)
        logger.info(f"Sent badge notification '{badge_name}' to donor {donor_id}")
    except Exception as e:
        logger.error(f"Failed to send badge notification for donor {donor_id}: {e}")

async def update_leaderboard(city: str, donor_id: str, lives_saved: int):
    """
    Supabase RANK() OVER (PARTITION BY city ORDER BY lives_saved DESC)
    Recalculates ranks for the city and upserts into leaderboard_cache.
    """
    supabase = get_supabase_admin()
    month_year = datetime.utcnow().strftime("%Y-%m")
    
    try:
        # Fetch all active donors in this city
        res = supabase.table("donors")\
            .select("donor_id, lives_saved")\
            .eq("city", city)\
            .eq("is_active", True)\
            .execute()
            
        if not res.data:
            return
            
        donors_list = res.data
        
        # Sort by lives_saved descending
        donors_sorted = sorted(donors_list, key=lambda x: x.get("lives_saved", 0), reverse=True)
        
        # Compute dense rank
        current_rank = 1
        records_to_upsert = []
        
        for idx, d in enumerate(donors_sorted):
            if idx > 0 and d.get("lives_saved", 0) < donors_sorted[idx-1].get("lives_saved", 0):
                current_rank = idx + 1
                
            records_to_upsert.append({
                "donor_id": d["donor_id"],
                "city": city,
                "lives_saved": d.get("lives_saved", 0),
                "rank": current_rank,
                "month_year": month_year,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            })
            
        # Upsert records in batches
        for i in range(0, len(records_to_upsert), 50):
            supabase.table("leaderboard_cache").upsert(records_to_upsert[i:i+50]).execute()
            
        logger.info(f"Updated leaderboard cache for city {city} ({len(records_to_upsert)} donors ranked).")
    except Exception as e:
        logger.error(f"Failed to update leaderboard rank for city {city}: {e}", exc_info=True)

async def get_city_leaderboard(city: str) -> list[dict]:
    """
    Top-10 from leaderboard_cache (fast, pre-computed).
    """
    supabase = get_supabase_admin()
    month_year = datetime.utcnow().strftime("%Y-%m")
    
    try:
        # Query pre-computed leaderboard_cache
        res = supabase.table("leaderboard_cache")\
            .select("donor_id, lives_saved, rank")\
            .eq("city", city)\
            .eq("month_year", month_year)\
            .order("rank", desc=False)\
            .limit(10)\
            .execute()
            
        if not res.data:
            return []
            
        records = res.data
        
        # Fetch donor names
        donor_ids = [r["donor_id"] for r in records]
        res_names = supabase.table("donors").select("donor_id, name").in_("donor_id", donor_ids).execute()
        name_map = {d["donor_id"]: d["name"] for d in res_names.data} if res_names.data else {}
        
        leaderboard = []
        for r in records:
            leaderboard.append({
                "rank": r["rank"],
                "donor_id": r["donor_id"],
                "name": name_map.get(r["donor_id"], "Kind Donor"),
                "lives_saved": r["lives_saved"]
            })
        return leaderboard
    except Exception as e:
        logger.error(f"Failed to fetch city leaderboard for {city}: {e}")
        return []

async def get_next_badge_progress(donor: dict) -> dict:
    """
    Returns progress to the next badge milestone.
    Returns: {current_badge, next_badge, current, target, remaining}
    """
    donation_count = donor.get("donation_count", 0)
    
    if donation_count == 0:
        return {
            "current_badge": "None",
            "next_badge": "Blood Starter",
            "current": 0,
            "target": 1,
            "remaining": 1
        }
    elif donation_count < 5:
        return {
            "current_badge": "Blood Starter",
            "next_badge": "Life Saver",
            "current": donation_count,
            "target": 5,
            "remaining": 5 - donation_count
        }
    elif donation_count < 10:
        return {
            "current_badge": "Life Saver",
            "next_badge": "Blood Hero",
            "current": donation_count,
            "target": 10,
            "remaining": 10 - donation_count
        }
    else:
        return {
            "current_badge": "Blood Hero",
            "next_badge": "None",
            "current": donation_count,
            "target": donation_count,
            "remaining": 0
        }
