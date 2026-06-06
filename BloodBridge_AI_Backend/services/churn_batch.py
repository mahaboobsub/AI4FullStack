"""
Nightly Churn Scoring and Intervention Batch Service for BloodBridge AI.
"""
import logging
from datetime import datetime, date
from core.database import get_supabase_admin
from core.config import get_settings
import os
import joblib
import numpy as np
from ml.churn_predictor import ChurnPredictor
from services.telegram_bot import send_telegram_message
from services.voice_service import make_bolna_call

logger = logging.getLogger(__name__)

SVD_RECOMMENDER_PATH = os.path.join("ml", "models", "svd_challenges.joblib")

def get_challenge_recommendation(donor_idx: int) -> str:
    """Recommend a gamified challenge type using TruncatedSVD collaborative filtering."""
    if os.path.exists(SVD_RECOMMENDER_PATH):
        try:
            data = joblib.load(SVD_RECOMMENDER_PATH)
            svd = data["svd"]
            matrix = data["matrix"]
            latent = data["latent"]
            challenge_types = data["challenge_types"]
            
            # Predict scores for this donor
            donor_features = latent[donor_idx % len(latent)]
            predicted_ratings = np.dot(donor_features, svd.components_)
            
            completed = matrix[donor_idx % len(matrix)]
            best_idx = -1
            best_rating = -999.0
            
            for idx, rating in enumerate(predicted_ratings):
                if completed[idx] == 0 and rating > best_rating:
                    best_rating = rating
                    best_idx = idx
                    
            if best_idx != -1:
                return challenge_types[best_idx]
            return challenge_types[0]
        except Exception as e:
            logger.warning(f"SVD recommendation failed: {e}")
    return "Weekend Warrior"

async def run_nightly_churn_batch():
    """
    Daily 8 PM IST.
    Scores all active donors in batches using the XGBoost ChurnPredictor.
    Dispatches:
    - CRITICAL (>0.75): Trigger automated voice calls via Vapi.ai.
    - HIGH (>0.50): Generate personalized Gemini engagement reminders and send via Telegram.
    - MEDIUM (>0.25): Recommend gamified challenges via SVD models.
    - LOW: No action.
    """
    logger.info("Starting nightly churn scoring batch...")
    supabase = get_supabase_admin()
    
    try:
        # 1. Fetch active donors
        res = supabase.table("donors").select("*").eq("is_active", True).execute()
        donors = res.data or []
        
        if not donors:
            logger.info("No active donors found to score.")
            return
            
        # Prepare feature variables for ChurnPredictor
        rich_donors = []
        for d in donors:
            donor_id = d["donor_id"]
            
            # Fetch missed alerts (DECLINED nodes in chain)
            bc_res = supabase.table("blood_chains")\
                .select("status")\
                .eq("donor_id", donor_id)\
                .eq("status", "DECLINED")\
                .execute()
            missed_alerts = len(bc_res.data or [])
            
            # Fetch memory
            mem_res = supabase.table("donor_memory").select("*").eq("donor_id", donor_id).execute()
            mem = mem_res.data[0] if mem_res.data else {}
            badge_count = len(mem.get("badges", []))
            avg_response_lag = mem.get("last_response_time_secs", 3600.0)
            
            # Copy and add features for extractor
            d_copy = d.copy()
            d_copy["missed_alerts"] = missed_alerts
            d_copy["badge_count"] = badge_count
            d_copy["avg_response_lag"] = avg_response_lag
            d_copy["city_scarcity_score"] = 0.5
            d_copy["chain_position_avg"] = 4.5
            
            rich_donors.append(d_copy)
            
        # 2. Predict batch
        predictor = ChurnPredictor()
        predictions = predictor.predict_batch(rich_donors)
        
        # Count statistics
        stats = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        settings = get_settings()
        
        # 3. Update Supabase and Dispatch
        for idx, pred in enumerate(predictions):
            donor_id = pred["donor_id"]
            score = pred["churn_score"]
            risk = pred["churn_risk"]
            factor = pred["top_risk_factor"]
            
            donor = rich_donors[idx]
            
            stats[risk] += 1
            
            # Update donors table
            supabase.table("donors")\
                .update({
                    "churn_score": score,
                    "churn_risk": risk
                })\
                .eq("donor_id", donor_id)\
                .execute()
                
            # 4. Dispatch tiered interventions
            chat_id = donor.get("telegram_chat_id")
            
            if risk == "CRITICAL":
                logger.info(f"Churn Batch: [CRITICAL] Dispatching Voice call to {donor['phone']}")
                if donor.get("phone"):
                    # Call Bolna voice service with mock emergency config
                    # or special churn reduction message
                    await make_bolna_call(
                        phone=donor["phone"],
                        donor=donor,
                        emergency={"blood_type": donor["blood_type"], "hospital_name": "Blood Warriors Center"},
                        request_id=f"CHURN-{donor_id[:4]}"
                    )
            elif risk == "HIGH":
                logger.info(f"Churn Batch: [HIGH] Sending personalized engagement reminder to {donor_id}")
                if chat_id:
                    # Invoke Gemini to generate personalized engagement outreach
                    msg = None
                    try:
                        from core.llm_provider import get_reasoning_llm
                        llm = get_reasoning_llm()
                        prompt = (
                            f"Write a personalized, extremely warm and polite message to a blood donor named {donor['name']}. "
                            f"They haven't donated in a while, and we want to encourage them to stay engaged. "
                            f"Highlight their past impact (they saved lives) and invite them to check the leaderboard or badges on the bot. "
                            f"Do not sound demanding or urgent. Use language: {donor.get('preferred_language', 'Hindi')}. "
                            f"Length: Under 100 words. Plain text only."
                        )
                        resp = await llm.ainvoke(prompt)
                        msg = resp.content.strip()
                    except Exception as ex:
                        logger.warning(f"Failed to generate churn outreach via Gemini: {ex}")
                            
                    if not msg:
                        msg = f"Namaste {donor['name']}. We miss you at Blood Warriors! Your presence saves lives. Check out your badges and achievements by typing /badges."
                        
                    await send_telegram_message(chat_id, msg)
                    
            elif risk == "MEDIUM":
                logger.info(f"Churn Batch: [MEDIUM] Dispatching gamified challenge recommendation to {donor_id}")
                challenge = get_challenge_recommendation(idx)
                if chat_id:
                    msg = (
                        f"🏆 *New Challenge Unlocked!*\n\n"
                        f"Namaste {donor['name']}. We have recommended a new challenge for you: *{challenge}*.\n"
                        f"Complete this challenge to earn special points and reach the top of the leaderboard!"
                    )
                    await send_telegram_message(chat_id, msg)
                    
        log_msg = f"Churn: {len(donors)} scored | CRITICAL:{stats['CRITICAL']} | HIGH:{stats['HIGH']} | MEDIUM:{stats['MEDIUM']} | LOW:{stats['LOW']}"
        logger.info(log_msg)
        
        # Save batch log in notes of administrative request log or general system log
        logger.info("Nightly churn scoring batch completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in run_nightly_churn_batch: {e}", exc_info=True)
