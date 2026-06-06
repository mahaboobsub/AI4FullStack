"""
Churn Prediction Model Training on Real BWF Data (A4).
Features: calls_to_donations_ratio, donation_count, response_rate,
days_since_donation, is_one_time_donor, serves_active_bridge, total_calls.
Label: is_active (from user_donation_active_status).
"""

import logging
import joblib
import os
from datetime import date, datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

RISK_TIERS = {
    "LOW": {"range": (0.0, 0.3), "action": "none"},
    "MEDIUM": {"range": (0.3, 0.6), "action": "send_impact_story"},
    "HIGH": {"range": (0.6, 0.8), "action": "re_engagement_badge_challenge"},
    "CRITICAL": {"range": (0.8, 1.0), "action": "ai_voice_call"}
}


def get_risk_tier(score: float) -> str:
    """Map a churn score to a risk tier."""
    for tier, config in RISK_TIERS.items():
        low, high = config["range"]
        if low <= score < high:
            return tier
    return "CRITICAL" if score >= 0.8 else "LOW"


async def train_churn_model() -> Dict[str, Any]:
    """Retrain the churn prediction model on real Supabase donor data."""
    from core.database import get_supabase_admin
    import numpy as np

    supabase = get_supabase_admin()
    logger.info("A4: Starting churn model retrain on real data...")

    res = supabase.table("donors").select(
        "donor_id, is_active, calls_to_donations_ratio, donation_count, "
        "response_rate, last_donation_date, donor_type, total_calls"
    ).execute()
    donors = res.data or []

    if len(donors) < 20:
        return {"status": "skipped", "reason": "insufficient_data", "count": len(donors)}

    bm_res = supabase.table("bridge_memberships").select("donor_id").execute()
    bridge_donor_ids = {row["donor_id"] for row in (bm_res.data or [])}

    features, labels, donor_ids = [], [], []
    today = date.today()

    for d in donors:
        ratio = float(d.get("calls_to_donations_ratio") or 1.0)
        don_count = int(d.get("donation_count") or 0)
        resp_rate = float(d.get("response_rate") or 0.5)
        total_calls = int(d.get("total_calls") or 0)
        last_dt = d.get("last_donation_date")
        days_since = 365
        if last_dt:
            try:
                days_since = (today - date.fromisoformat(str(last_dt)[:10])).days
            except Exception:
                pass
        is_one_time = 1 if d.get("donor_type") == "One-Time" else 0
        serves_bridge = 1 if d["donor_id"] in bridge_donor_ids else 0

        features.append([ratio, don_count, resp_rate, days_since, is_one_time, serves_bridge, total_calls])
        labels.append(1 if d.get("is_active") else 0)
        donor_ids.append(d["donor_id"])

    X = __import__("numpy").array(features)
    y = __import__("numpy").array(labels)

    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier
    from sklearn.metrics import roc_auc_score, precision_score, recall_score

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pos_count = sum(y_train)
    neg_count = len(y_train) - pos_count
    scale = neg_count / max(pos_count, 1)

    model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                          scale_pos_weight=scale, use_label_encoder=False,
                          eval_metric="logloss", random_state=42)
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)

    logger.info(f"A4: AUC={auc:.4f}, Precision={precision:.4f}, Recall={recall:.4f}")

    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)
    new_path = os.path.join(model_dir, "churn_model_new.joblib")
    final_path = os.path.join(model_dir, "churn_model.joblib")

    if auc >= 0.70:
        joblib.dump(model, new_path)
        os.replace(new_path, final_path)

    # Batch-score all donors
    all_proba = model.predict_proba(__import__("numpy").array(features))
    for i, did in enumerate(donor_ids):
        score = round(1.0 - float(all_proba[i][1]), 4)
        tier = get_risk_tier(score)
        try:
            supabase.table("donors").update({"churn_score": score, "churn_risk": tier}).eq("donor_id", did).execute()
        except Exception:
            pass

    try:
        supabase.table("ml_model_logs").insert({
            "model_name": "churn_predictor", "auc": round(auc, 4),
            "precision_val": round(precision, 4), "recall_val": round(recall, 4),
            "training_samples": len(X_train), "test_samples": len(X_test),
            "trained_at": datetime.utcnow().isoformat() + "Z"
        }).execute()
    except Exception as e:
        logger.warning(f"ml_model_logs insert failed: {e}")

    return {"status": "success" if auc >= 0.70 else "below_threshold",
            "auc": round(auc, 4), "precision": round(precision, 4),
            "recall": round(recall, 4), "donors_scored": len(donor_ids)}
