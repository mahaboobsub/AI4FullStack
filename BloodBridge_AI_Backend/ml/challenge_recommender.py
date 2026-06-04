"""
SVD Collaborative Filtering Challenge Recommender for BloodBridge AI.
Recommends personalized gamified challenges to donors using latent vectors.
"""
import os
import joblib
import numpy as np
import hashlib
import logging
from core.database import get_supabase_admin
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)

MODEL_PATH = 'ml/models/svd_challenges.joblib'

CHALLENGES_METADATA = {
    'double_donor': {
        'name': 'Double Donor',
        'emoji': '🎒',
        'description': 'Donate twice in a row without missing a schedule.'
    },
    'referral_hero': {
        'name': 'Referral Hero',
        'emoji': '👥',
        'description': 'Refer a friend to sign up as a blood donor.'
    },
    'city_drive': {
        'name': 'City Drive',
        'emoji': '🏢',
        'description': 'Donate at any city blood drive location.'
    },
    'streak_keeper': {
        'name': 'Streak Keeper',
        'emoji': '🔥',
        'description': 'Maintain your monthly donation streak for 3 months.'
    },
    'midnight_hero': {
        'name': 'Midnight Hero',
        'emoji': '🌙',
        'description': 'Respond to a critical request raised late at night.'
    },
    'rare_blood_run': {
        'name': 'Rare Blood Run',
        'emoji': '🏃‍♂️',
        'description': 'Help secure compatible blood for a rare antigen patient.'
    },
    'young_saver': {
        'name': 'Young Saver',
        'emoji': '👶',
        'description': 'Donate to save a pediatric Thalassemia patient.'
    },
    'multilingual': {
        'name': 'Multilingual',
        'emoji': '🗣️',
        'description': 'Complete onboarding or update language settings.'
    },
    'comeback_kid': {
        'name': 'Comeback Kid',
        'emoji': '🔄',
        'description': 'Donate after being inactive for more than 6 months.'
    },
    'speed_response': {
        'name': 'Speed Response',
        'emoji': '⚡',
        'description': 'Confirm an outreach request within 1 hour.'
    }
}

SVD_TO_CHALLENGE_MAP = {
    "Weekend Warrior": "double_donor",
    "Rare Guardian": "rare_blood_run",
    "First Responder": "speed_response",
    "Milestone Master": "streak_keeper",
    "City Champion": "city_drive",
    "Holiday Hero": "midnight_hero",
    "Summer Saver": "young_saver",
    "Emergency Anchor": "comeback_kid",
    "Youth Ambassador": "referral_hero",
    "Platelet Pioneer": "double_donor",
    "Double Red Donor": "double_donor",
    "Community Leader": "referral_hero",
    "Awareness Advocate": "multilingual",
    "Winter Warmth": "city_drive",
    "Rapid Rescue": "speed_response"
}

class ChallengeRecommender:
    def __init__(self):
        self.model_data = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model_data = joblib.load(MODEL_PATH)
                logger.info("Successfully loaded SVD challenge model.")
            except Exception as e:
                logger.error(f"Failed to load SVD challenge model: {e}")

    def _get_donor_idx(self, donor_id: str) -> int:
        """Stable deterministic mapping of donor_id to index 0-499."""
        try:
            digits = "".join(c for c in donor_id if c.isdigit())
            if digits:
                return int(digits) % 500
        except Exception:
            pass
        return int(hashlib.md5(donor_id.encode()).hexdigest(), 16) % 500

    def _get_profile_vector(self, donor: dict, challenge_types: list) -> np.ndarray:
        """Construct profile-based dense interaction vector for cold start."""
        v = np.zeros(len(challenge_types))
        for idx, col in enumerate(challenge_types):
            if col == "Rare Guardian" and donor.get("kell_negative"):
                v[idx] = 1.0
            if col == "Milestone Master" and donor.get("donation_count", 0) >= 5:
                v[idx] = 1.0
            if col == "City Champion" and donor.get("donation_count", 0) >= 10:
                v[idx] = 1.0
            if col == "First Responder" and donor.get("response_rate", 0.5) > 0.8:
                v[idx] = 1.0
        return v

    def recommend_challenges(self, donor_id: str, top_k=3) -> list[dict]:
        """
        Collaborative filtering recommendation.
        Algorithm: latent vector -> cosine similarity -> similar donors -> their completed challenges
        """
        if not self.model_data:
            logger.warning("SVD model not loaded. Returning fallback recommendations.")
            return self._fallback_recommendations(top_k)
            
        svd = self.model_data["svd"]
        matrix = self.model_data["matrix"]
        latent = self.model_data["latent"]
        challenge_types = self.model_data["challenge_types"]
        
        donor_idx = self._get_donor_idx(donor_id)
        
        # 1. Retrieve or calculate user latent vector
        # Cold start: if donor is not in database or we want to use profile-based features
        is_cold_start = True
        donor_profile = {}
        
        supabase = get_supabase_admin()
        try:
            res = supabase.table("donors").select("*").eq("donor_id", donor_id).execute()
            if res.data:
                donor_profile = res.data[0]
                # If they have completed active donations, they are not completely cold
                if donor_profile.get("donation_count", 0) > 0:
                    is_cold_start = False
        except Exception as e:
            logger.warning(f"Failed to fetch donor profile for cold start check: {e}")
            
        if is_cold_start and donor_profile:
            # Cold start: project profile vector into SVD latent space
            v = self._get_profile_vector(donor_profile, challenge_types)
            u_latent = svd.transform(v.reshape(1, -1))[0]
        else:
            # Retrieve pre-computed latent factor
            u_latent = latent[donor_idx % len(latent)]
            
        # 2. Compute Cosine Similarity with all other users
        norms = np.linalg.norm(latent, axis=1)
        norms[norms == 0] = 1.0
        u_norm = np.linalg.norm(u_latent)
        if u_norm == 0:
            u_norm = 1.0
            
        similarities = np.dot(latent, u_latent) / (norms * u_norm)
        
        # Sort indices by similarity descending
        similar_indices = np.argsort(similarities)[::-1]
        
        # 3. Aggregate completed items from top-10 similar donors (weighted by similarity)
        challenge_scores = np.zeros(matrix.shape[1])
        count = 0
        for idx in similar_indices:
            if idx == (donor_idx % len(latent)):
                continue
            sim = similarities[idx]
            if sim <= 0.0:
                break
            challenge_scores += matrix[idx] * sim
            count += 1
            if count >= 10:
                break
                
        # 4. Exclude already completed challenges
        user_history = matrix[donor_idx % len(matrix)]
        challenge_scores[user_history == 1] = -999.0
        
        # Sort SVD challenges by aggregated score
        recommended_svd_indices = np.argsort(challenge_scores)[::-1]
        
        # 5. Map to CHALLENGES_METADATA, keeping unique categories
        recommendations = []
        seen_challenge_ids = set()
        
        for svd_idx in recommended_svd_indices:
            if len(recommendations) >= top_k:
                break
                
            score = challenge_scores[svd_idx]
            if score == -999.0:
                break # All others are already completed
                
            svd_name = challenge_types[svd_idx]
            challenge_id = SVD_TO_CHALLENGE_MAP.get(svd_name, 'double_donor')
            
            if challenge_id not in seen_challenge_ids:
                seen_challenge_ids.add(challenge_id)
                meta = CHALLENGES_METADATA[challenge_id]
                recommendations.append({
                    "challenge_id": challenge_id,
                    "name": meta["name"],
                    "emoji": meta["emoji"],
                    "description": meta["description"],
                    "relevance_score": round(float(score), 2)
                })
                
        # Fallback if SVD scores are completely depleted
        if len(recommendations) < top_k:
            fb = self._fallback_recommendations(top_k)
            for item in fb:
                if item["challenge_id"] not in seen_challenge_ids and len(recommendations) < top_k:
                    recommendations.append(item)
                    
        return recommendations

    def _fallback_recommendations(self, top_k: int) -> list[dict]:
        """Return default recommendations based on static challenges metadata."""
        fb = []
        for challenge_id, meta in list(CHALLENGES_METADATA.items())[:top_k]:
            fb.append({
                "challenge_id": challenge_id,
                "name": meta["name"],
                "emoji": meta["emoji"],
                "description": meta["description"],
                "relevance_score": 0.5
            })
        return fb

async def unlock_challenge_for_donor(donor_id: str):
    """
    Get recommended challenge and notify donor via Telegram.
    """
    recommender = ChallengeRecommender()
    recs = recommender.recommend_challenges(donor_id, top_k=1)
    if not recs:
        return
        
    rec = recs[0]
    
    supabase = get_supabase_admin()
    try:
        res = supabase.table("donors").select("name, telegram_chat_id").eq("donor_id", donor_id).execute()
        if res.data and res.data[0].get("telegram_chat_id"):
            name = res.data[0]["name"]
            chat_id = res.data[0]["telegram_chat_id"]
            
            msg = (
                f"🏆 *New Challenge Unlocked!*\n\n"
                f"Namaste {name}! Based on your profile, we have unlocked a personalized challenge for you:\n\n"
                f"{rec['emoji']} *{rec['name']}*\n"
                f"_{rec['description']}_\n\n"
                f"Complete this challenge to earn points and scale the leaderboards!"
            )
            await send_telegram_message(chat_id, msg)
            logger.info(f"Challenge unlock alert dispatched to donor {donor_id}: {rec['name']}")
    except Exception as e:
        logger.error(f"Failed to dispatch challenge unlock alert for donor {donor_id}: {e}")
