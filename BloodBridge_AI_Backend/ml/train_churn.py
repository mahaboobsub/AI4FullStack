"""
Train XGBoost Churn Model for BloodBridge AI.
Generates synthetic training data matching the 8-feature vector used by ChurnPredictor,
trains an XGBRegressor, evaluates with MAE/RMSE/Confusion Matrix, and saves to disk.
"""
import os
import sys
import random
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error,
    confusion_matrix, classification_report
)
from sklearn.model_selection import train_test_split

# Add backend root to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_churn_data(num_samples=2000):
    """
    Generate synthetic donor churn training data.
    Feature vector matches ChurnPredictor._extract_features():
      [days_since_donation, response_rate, missed_alerts, avg_response_lag,
       kell_negative_flag, city_blood_scarcity_score, badge_count, chain_position_avg]
    Target: churn_score (0.0 to 1.0)
    """
    np.random.seed(42)
    random.seed(42)

    # Feature distributions
    days_since_donation = np.random.uniform(0, 400, num_samples)
    response_rate = np.random.uniform(0.0, 1.0, num_samples)
    missed_alerts = np.random.randint(0, 10, num_samples)
    avg_response_lag = np.random.uniform(30, 7200, num_samples)  # 30s to 2hrs
    kell_negative_flag = np.random.binomial(1, 0.15, num_samples)
    city_blood_scarcity = np.random.uniform(0.0, 1.0, num_samples)
    badge_count = np.random.randint(0, 15, num_samples)
    chain_position_avg = np.random.uniform(1.0, 8.0, num_samples)

    records = []
    for i in range(num_samples):
        # Churn scoring rules:
        # - High days_since -> higher churn
        # - Low response_rate -> higher churn
        # - More missed_alerts -> higher churn
        # - Higher avg_response_lag -> slightly higher churn
        # - More badges -> lower churn (engaged)
        # - Lower chain_position_avg -> lower churn (trusted donors)

        base = 0.0
        # Days since donation: primary driver (0-400 days maps to 0-0.5)
        base += (days_since_donation[i] / 400.0) * 0.35

        # Response rate: inverse (low rate = high churn)
        base += (1.0 - response_rate[i]) * 0.25

        # Missed alerts: each adds 0.04
        base += min(missed_alerts[i] * 0.04, 0.20)

        # Avg response lag: slow responders churn more
        base += (avg_response_lag[i] / 7200.0) * 0.08

        # Badge count: negative correlation (engaged donors stay)
        base -= min(badge_count[i] * 0.015, 0.15)

        # Chain position: being called first (pos 1-2) means trusted, lower churn
        if chain_position_avg[i] <= 2.0:
            base -= 0.05
        elif chain_position_avg[i] >= 6.0:
            base += 0.05

        # Add noise
        noise = random.gauss(0, 0.05)
        churn_score = max(0.0, min(1.0, base + noise))

        records.append({
            "days_since_donation": days_since_donation[i],
            "response_rate": response_rate[i],
            "missed_alerts": missed_alerts[i],
            "avg_response_lag": avg_response_lag[i],
            "kell_negative_flag": kell_negative_flag[i],
            "city_blood_scarcity": city_blood_scarcity[i],
            "badge_count": badge_count[i],
            "chain_position_avg": chain_position_avg[i],
            "churn_score": churn_score
        })

    return pd.DataFrame(records)


def get_churn_tier(score: float) -> str:
    """Map continuous churn score to risk tier."""
    if score >= 0.75:
        return "CRITICAL"
    elif score >= 0.50:
        return "HIGH"
    elif score >= 0.25:
        return "MEDIUM"
    return "LOW"


def train_churn_model():
    print("=" * 60)
    print("BLOODBRIDGE AI - CHURN MODEL TRAINING")
    print("=" * 60)

    print("\n1. Generating synthetic churn training data...")
    df = generate_churn_data(2000)
    print(f"   Generated {len(df)} training samples")
    print(f"   Churn score distribution: mean={df['churn_score'].mean():.3f}, "
          f"std={df['churn_score'].std():.3f}")

    # Features and target
    feature_cols = [
        "days_since_donation", "response_rate", "missed_alerts",
        "avg_response_lag", "kell_negative_flag", "city_blood_scarcity",
        "badge_count", "chain_position_avg"
    ]
    X = df[feature_cols]
    y = df["churn_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"   Train: {len(X_train)} | Test: {len(X_test)}")

    print("\n2. Training XGBoost regressor...")
    model = XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Regression evaluation
    predictions = model.predict(X_test)
    predictions = np.clip(predictions, 0.0, 1.0)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print("\n" + "=" * 60)
    print("REGRESSION PERFORMANCE")
    print("=" * 60)
    print(f"   Mean Absolute Error (MAE):        {mae:.4f}")
    print(f"   Root Mean Squared Error (RMSE):    {rmse:.4f}")

    # Classification evaluation (by binning into churn tiers)
    y_test_classes = [get_churn_tier(val) for val in y_test]
    pred_classes = [get_churn_tier(val) for val in predictions]

    labels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    cm = confusion_matrix(y_test_classes, pred_classes, labels=labels)

    print("\n" + "=" * 60)
    print("CHURN TIER CONFUSION MATRIX")
    print("=" * 60)
    header = f"{'':>14} | {'Pred:LOW':>10} | {'Pred:MED':>10} | {'Pred:HIGH':>10} | {'Pred:CRIT':>10}"
    print(header)
    print("-" * len(header))
    for idx, label in enumerate(labels):
        row = f"True: {label:>8} | {cm[idx][0]:>10} | {cm[idx][1]:>10} | {cm[idx][2]:>10} | {cm[idx][3]:>10}"
        print(row)

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(y_test_classes, pred_classes, target_names=labels))

    # Feature importance
    print("=" * 60)
    print("FEATURE IMPORTANCE")
    print("=" * 60)
    importances = model.feature_importances_
    for fname, imp in sorted(zip(feature_cols, importances), key=lambda x: -x[1]):
        bar = "#" * int(imp * 50)
        print(f"   {fname:>25}: {imp:.4f} {bar}")

    # Save model
    models_dir = os.path.join("ml", "models")
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "churn_model.joblib")
    joblib.dump(model, model_path)
    print(f"\n   Model saved to {model_path}")
    print(f"   Model size: {os.path.getsize(model_path) / 1024:.1f} KB")

    print("\n" + "=" * 60)
    print("[SUCCESS] CHURN MODEL TRAINING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    train_churn_model()
