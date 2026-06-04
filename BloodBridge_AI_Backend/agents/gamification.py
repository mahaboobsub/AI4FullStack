"""
Gamification Agent for BloodBridge AI.
Calculates and awards badges and updates leaderboard positions.
"""
import logging
import time
from datetime import datetime
from models.state import AgentState
from core.database import get_supabase_admin
from api.websocket import ws_manager
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)

BADGE_RULES = {
    'blood_starter': {'name': 'Blood Starter', 'threshold': 1,  'emoji': '🌱', 'msg': 'Awarded for your first blood donation! Welcome to the life-saving club.'},
    'life_saver':    {'name': 'Life Saver', 'threshold': 5,  'emoji': '❤️', 'msg': 'Awarded for completing 5 life-saving blood donations.'},
    'blood_hero':    {'name': 'Blood Hero', 'threshold': 10, 'emoji': '🦸', 'msg': 'Awarded for completing 10 life-saving blood donations. You are a true hero!'},
    'rare_guardian': {'name': 'Rare Guardian', 'emoji': '💎', 'msg': 'Awarded for donating rare Kell-negative blood at least 3 times.'},
    'city_champion': {'name': 'City Champion', 'emoji': '🏆', 'msg': 'Awarded for reaching Rank #1 in your city leaderboard this month.'},
    'crisis_hero':   {'name': 'Crisis Hero', 'emoji': '⚡', 'msg': 'Awarded for confirming a critical blood request within 2 hours.'},
}

async def gamification_agent(state: AgentState) -> dict:
    """
    Gamification Agent Node.
    Checks badge rules for confirmed donors, awards new badges, updates leaderboards,
    and calls impact story generation.
    """
    start_time = time.perf_counter()
    logger.info(f"[{state['trace_id']}] GamificationAgent started...")
    
    request_id = state["request_id"]
    patient_id = state["patient_id"]
    city = state["city"]
    priority = state.get("urgency_result", {}).get("priority", "ROUTINE")
    supabase = get_supabase_admin()
    
    badges_awarded = []
    
    try:
        # 1. Fetch confirmed donors for this request
        chain_res = supabase.table("blood_chains")\
            .select("donor_id, donor_name, alerted_at, confirmed_at")\
            .eq("request_id", request_id)\
            .eq("status", "COMPLETED")\
            .execute()
            
        confirmed_nodes = chain_res.data or []
        
        for node in confirmed_nodes:
            donor_id = node.get("donor_id")
            donor_name = node.get("donor_name", "Hero")
            if not donor_id:
                continue            # 3. Update leaderboard for this city
            from services.gamification_service import update_leaderboard, check_and_award_badges
            await update_leaderboard(city, donor_id, donor.get("lives_saved", 0))
            
            # 4. Check and award badges via the new gamification service
            new_awarded = await check_and_award_badges(donor_id, donor)
            badges_awarded.extend(new_awarded)
            
            # 5. Broadcast WebSocket event for each awarded badge
            for b_name in new_awarded:
                await ws_manager.broadcast({
                    "type": "badge_awarded",
                    "donor_id": donor_id,
                    "donor_name": donor_name,
                    "badge_name": b_name
                })
                
            # 7. Generate Gemini impact story and send 2-hour delayed Telegram message
            from services.impact_story import generate_impact_story, send_impact_story_via_telegram
            
            # Fetch patient details
            patient_res = supabase.table("patients").select("*").eq("patient_id", patient_id).execute()
            patient = patient_res.data[0] if patient_res.data else {}
            
            lang = donor.get("preferred_language", "en")
            story = await generate_impact_story(donor, patient, lang)
            if story:
                await send_impact_story_via_telegram(donor_id, story)
                
        duration = (time.perf_counter() - start_time) * 1000.0
        timings = state.get("node_timings", {}).copy()
        timings["gamification_node"] = round(duration, 2)
        
        return {
            "badges_awarded": badges_awarded,
            "node_timings": timings
        }
    except Exception as e:
        logger.error(f"GamificationAgent error: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Gamification agent error: {e}"],
            "badges_awarded": []
        }
