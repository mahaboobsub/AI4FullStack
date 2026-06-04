"""
XGBoost Churn Predictor for BloodBridge AI.
"""
import os
import joblib
import numpy as np
import logging
from datetime import date
from typing import Literal, List, Dict, Any

logger = logging.getLogger(__name__)

CHURN_MODEL_PATH = os.path.join("ml", "models", "churn_model.joblib")

class ChurnPredictor:
    def __init__(self):
        self.model = None
        if os.path.exists(CHURN_MODEL_PATH):
            try:
                self.model = joblib.load(CHURN_MODEL_PATH)
                logger.info("Successfully loaded churn model.")
            except Exception as e:
                logger.error(f"Failed to load churn model: {e}")

    def predict_churn(self, donor: dict) -> dict:
        """
        Predict churn score and risk category for a single donor.
        Returns: {churn_score, churn_risk, top_risk_factor}
        """
        features = self._extract_features(donor)
        
        # Predict using loaded model or simple fallback
        if self.model:
            try:
                score = float(self.model.predict(features.reshape(1, -1))[0])
            except Exception as e:
                logger.warning(f"Churn prediction failed: {e}. Using fallback.")
                score = self._fallback_score(features)
        else:
            score = self._fallback_score(features)
            
        score = max(0.0, min(1.0, score))
        risk_tier = self.get_risk_tier(score)
        top_risk_factor = self.explain_top_risk_factor(donor, features)
        
        return {
            "churn_score": round(score, 2),
            "churn_risk": risk_tier,
            "top_risk_factor": top_risk_factor
        }

    def predict_batch(self, donors: List[dict]) -> List[dict]:
        """
        Predict churn scores in a vectorized batch for maximum performance.
        500 donors in <50ms.
        """
        if not donors:
            return []
            
        feature_matrix = np.vstack([self._extract_features(d) for d in donors])
        
        scores = []
        if self.model:
            try:
                scores = self.model.predict(feature_matrix)
            except Exception as e:
                logger.warning(f"Batch churn prediction failed: {e}. Using fallback.")
                scores = [self._fallback_score(f) for f in feature_matrix]
        else:
            scores = [self._fallback_score(f) for f in feature_matrix]
            
        results = []
        for idx, donor in enumerate(donors):
            score = max(0.0, min(1.0, float(scores[idx])))
            risk_tier = self.get_risk_tier(score)
            top_risk_factor = self.explain_top_risk_factor(donor, feature_matrix[idx])
            
            results.append({
                "donor_id": donor["donor_id"],
                "churn_score": round(score, 2),
                "churn_risk": risk_tier,
                "top_risk_factor": top_risk_factor
            })
        return results

    def _extract_features(self, donor: dict) -> np.ndarray:
        """Extract a numpy array of features for model input."""
        # 1. days_since_donation
        last_date = donor.get("last_donation_date")
        if last_date:
            try:
                days_since = (date.today() - date.fromisoformat(str(last_date))).days
            except Exception:
                days_since = 365.0
        else:
            days_since = 365.0
            
        # 2. response_time_decay (maps to response_rate)
        response_rate = donor.get("response_rate", 0.5)
        
        # 3. missed_alerts
        missed_alerts = donor.get("missed_alerts", 0)
        
        # 4. avg_response_lag
        avg_response_lag = donor.get("avg_response_lag", 3600.0)
        
        # 5. kell_negative_flag
        kell_negative_flag = 1 if donor.get("kell_negative") else 0
        
        # 6. city_blood_scarcity_score
        city_blood_scarcity_score = donor.get("city_scarcity_score", 0.5)
        
        # 7. badge_count
        badge_count = donor.get("badge_count", 0)
        
        # 8. chain_position_avg
        chain_position_avg = donor.get("chain_position_avg", 4.5)
        
        return np.array([
            float(days_since),
            float(response_rate),
            float(missed_alerts),
            float(avg_response_lag),
            float(kell_negative_flag),
            float(city_blood_scarcity_score),
            float(badge_count),
            float(chain_position_avg)
        ])

    def _fallback_score(self, features: np.ndarray) -> float:
        """Linear combination fallback calculation if model is missing."""
        days_since = features[0]
        missed = features[2]
        return min(1.0, max(0.0, (days_since / 180.0) * 0.5 + missed * 0.1))

    def get_risk_tier(self, churn_score: float) -> Literal['CRITICAL','HIGH','MEDIUM','LOW']:
        """Get the risk tier corresponding to the churn score."""
        if churn_score >= 0.75:
            return "CRITICAL"
        elif churn_score >= 0.50:
            return "HIGH"
        elif churn_score >= 0.25:
            return "MEDIUM"
        return "LOW"

    def explain_top_risk_factor(self, donor: dict, features: np.ndarray) -> str:
        """Explain top reason for churn risk based on feature values."""
        days_since = features[0]
        missed = features[2]
        
        if missed >= 3:
            return "Multiple missed alert opportunities"
        if days_since >= 180:
            return f"Over {int(days_since)} days inactive since last donation"
        if features[1] < 0.3:
            return "Low response rate to coordination requests"
        return "Lack of gamified challenge engagement"
