"""
Urgency Scorer for BloodBridge AI.
Calculates patient transfusion urgency using an XGBoost regression model or rule-based fallback.
"""
import os
import logging
import joblib
import numpy as np
from datetime import date, datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UrgencyScorer:
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "urgency_model.joblib")
    FEATURES = ['hemoglobin', 'days_overdue', 'has_cardiac_flag', 'age', 'transfusion_count', 'antibody_count']

    def __init__(self):
        self.model = self._load_model()

    def _load_model(self) -> Optional[Any]:
        """Attempt to load the pre-trained XGBoost urgency model from disk."""
        if os.path.exists(self.MODEL_PATH):
            try:
                model = joblib.load(self.MODEL_PATH)
                logger.info(f"Successfully loaded XGBoost urgency model from {self.MODEL_PATH}")
                return model
            except Exception as e:
                logger.warning(f"Failed to load XGBoost model from {self.MODEL_PATH}: {e}. Fallback enabled.")
        else:
            logger.info("XGBoost urgency model not found. Using rule-based fallback.")
        return None

    def _parse_date(self, date_val) -> Optional[date]:
        """Safely parse next_transfusion_due into a date object."""
        if not date_val:
            return None
        if isinstance(date_val, date):
            return date_val
        if isinstance(date_val, str):
            try:
                return datetime.strptime(date_val.split("T")[0], "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def _extract_features(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a structured feature dictionary from the raw patient details."""
        hgb = patient.get("hemoglobin", 7.0)
        
        # Calculate days overdue based on next_transfusion_due
        due_date = self._parse_date(patient.get("next_transfusion_due"))
        if due_date:
            days_overdue = (date.today() - due_date).days
            days_overdue = max(0, days_overdue)
        else:
            days_overdue = 0
            
        has_cardiac_flag = 1 if patient.get("cardiac_flag", False) else 0
        age = patient.get("age", 10)
        tx_count = patient.get("transfusion_count", 0)
        
        # Calculate antibody count (sum of all minor antibody flags)
        antibody_count = 0
        antibody_fields = [
            "antibody_kell", "antibody_duffy", "antibody_kidd",
            "antibody_rh_e", "antibody_rh_c", "antibody_mns"
        ]
        for field in antibody_fields:
            if patient.get(field, False):
                antibody_count += 1
                
        # Parse from list if antibody_flags is stored as a list
        flags = patient.get("antibody_flags")
        if isinstance(flags, list):
            antibody_count = max(antibody_count, len(flags))

        return {
            "hemoglobin": float(hgb),
            "days_overdue": float(days_overdue),
            "has_cardiac_flag": int(has_cardiac_flag),
            "age": float(age),
            "transfusion_count": int(tx_count),
            "antibody_count": int(antibody_count)
        }

    def score(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate urgency score (0.0 to 10.0) and priority category.
        Priority:
            - CRITICAL: score >= 7.5
            - HIGH: score >= 5.0
            - ROUTINE: score < 5.0
        """
        features_dict = self._extract_features(patient)
        
        if self.model is not None:
            try:
                # Prepare feature vector for XGBoost inference
                feature_vector = np.array([[
                    features_dict["hemoglobin"],
                    features_dict["days_overdue"],
                    features_dict["has_cardiac_flag"],
                    features_dict["age"],
                    features_dict["transfusion_count"],
                    features_dict["antibody_count"]
                ]])
                raw_score = float(self.model.predict(feature_vector)[0])
                urgency_score = round(max(0.0, min(10.0, raw_score)), 2)
            except Exception as e:
                logger.error(f"XGBoost scoring failed: {e}. Falling back to rules.")
                urgency_score = self._rule_score(features_dict)
        else:
            urgency_score = self._rule_score(features_dict)

        # Classify priority
        if urgency_score >= 7.5:
            priority = "CRITICAL"
        elif urgency_score >= 5.0:
            priority = "HIGH"
        else:
            priority = "ROUTINE"

        return {
            "urgency_score": urgency_score,
            "priority": priority,
            "features": features_dict
        }

    def _rule_score(self, features: Dict[str, Any]) -> float:
        """Deterministic rule-based clinical scoring model."""
        hgb = features["hemoglobin"]
        overdue = features["days_overdue"]
        cardiac = features["has_cardiac_flag"]
        
        base = 10.0 - (hgb / 16.5) * 4.0
        overdue_points = min(overdue / 30.0, 3.0)
        cardiac_points = 2.0 if cardiac == 1 else 0.0
        
        raw = base + overdue_points + cardiac_points
        return round(max(0.0, min(10.0, raw)), 2)

# Helper function for quick access
_scorer_instance: Optional[UrgencyScorer] = None

def get_urgency_scorer() -> UrgencyScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = UrgencyScorer()
    return _scorer_instance
