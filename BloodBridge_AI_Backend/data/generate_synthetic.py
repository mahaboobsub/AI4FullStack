"""
Synthetic Data Generation and Machine Learning Model Training.
Trains XGBoost urgency/churn models and TruncatedSVD challenge recommender.
Saves serialized model artifacts in ml/models/.
"""
import os
import sys
import random
import numpy as np
import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import mean_absolute_error, r2_score

# Add backend root to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_urgency_training_data(num_samples=1000):
    """Generate synthetic patient clinical parameters and calculate urgency scores."""
    np.random.seed(42)
    random.seed(42)
    
    hemoglobin = np.random.uniform(4.0, 16.5, num_samples)
    days_overdue = np.random.uniform(0, 60, num_samples)
    has_cardiac_flag = np.random.binomial(1, 0.15, num_samples)
    age = np.random.uniform(3, 18, num_samples)
    transfusion_count = np.random.randint(10, 250, num_samples)
    antibody_count = np.random.randint(0, 6, num_samples)
    
    records = []
    for i in range(num_samples):
        # Clinical urgency calculation rule (P1-D / P2-C specifications)
        base = 10.0 - (hemoglobin[i] / 16.5) * 4.0
        overdue = min(days_overdue[i] / 30.0, 3.0)
        cardiac = 2.0 if has_cardiac_flag[i] == 1 else 0.0
        noise = random.gauss(0, 0.3)
        
        urgency_score = min(10.0, max(0.0, base + overdue + cardiac + noise))
        
        records.append({
            "hemoglobin": hemoglobin[i],
            "days_overdue": days_overdue[i],
            "has_cardiac_flag": has_cardiac_flag[i],
            "age": age[i],
            "transfusion_count": transfusion_count[i],
            "antibody_count": antibody_count[i],
            "urgency_score": urgency_score
        })
        
    return pd.DataFrame(records)

def generate_churn_training_data(num_samples=1000):
    """Generate synthetic donor engagement statistics and calculate churn probabilities."""
    np.random.seed(42)
    random.seed(42)
    
    days_since_donation = np.random.uniform(0, 365, num_samples)
    response_rate = np.random.uniform(0.1, 1.0, num_samples)
    missed_alerts = np.random.randint(0, 10, num_samples)
    avg_response_lag = np.random.uniform(300, 86400, num_samples) # in seconds
    kell_negative_flag = np.random.binomial(1, 0.92, num_samples)
    city_blood_scarcity_score = np.random.uniform(0.1, 1.0, num_samples)
    badge_count = np.random.randint(0, 8, num_samples)
    chain_position_avg = np.random.uniform(1.0, 8.0, num_samples)
    
    records = []
    for i in range(num_samples):
        # Churn probability rule (P1-D specifies base formulas)
        base = (days_since_donation[i] / 180.0) * 0.35
        resp = (1.0 - response_rate[i]) * 0.20
        missed = (missed_alerts[i] / 10.0) * 0.15
        lag = min(avg_response_lag[i] / 3600.0, 1.0) * 0.12
        kell = -0.08 if kell_negative_flag[i] == 1 else 0.0
        badge = -(badge_count[i] * 0.03)
        noise = random.gauss(0, 0.05)
        
        churn_prob = min(1.0, max(0.0, base + resp + missed + lag + kell + badge + noise))
        
        records.append({
            "days_since_donation": days_since_donation[i],
            "response_time_decay": response_rate[i],
            "missed_alerts": missed_alerts[i],
            "avg_response_lag": avg_response_lag[i],
            "kell_negative_flag": kell_negative_flag[i],
            "city_blood_scarcity_score": city_blood_scarcity_score[i],
            "badge_count": badge_count[i],
            "chain_position_avg": chain_position_avg[i],
            "churn_probability": churn_prob
        })
        
    return pd.DataFrame(records)

def train_and_save_models():
    """Train XGBoost regressors and SVD matrix, saving to ml/models/ directory."""
    print("Generating training datasets...")
    df_urgency = generate_urgency_training_data()
    df_churn = generate_churn_training_data()
    
    # Ensure ml/models directory exists
    models_dir = os.path.join("ml", "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Train Urgency Model
    print("Training Urgency Model...")
    X_u = df_urgency[["hemoglobin", "days_overdue", "has_cardiac_flag", "age", "transfusion_count", "antibody_count"]]
    y_u = df_urgency["urgency_score"]
    
    urgency_model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    urgency_model.fit(X_u, y_u)
    
    pred_u = urgency_model.predict(X_u)
    mae_u = mean_absolute_error(y_u, pred_u)
    r2_u = r2_score(y_u, pred_u)
    
    urgency_path = os.path.join(models_dir, "urgency_model.joblib")
    joblib.dump(urgency_model, urgency_path)
    print(f"Urgency model trained. Saved to {urgency_path}. MAE: {mae_u:.3f}, R2: {r2_u:.3f}")
    
    # 2. Train Churn Model
    print("Training Churn Model...")
    X_c = df_churn[[
        "days_since_donation", "response_time_decay", "missed_alerts", "avg_response_lag",
        "kell_negative_flag", "city_blood_scarcity_score", "badge_count", "chain_position_avg"
    ]]
    y_c = df_churn["churn_probability"]
    
    churn_model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    churn_model.fit(X_c, y_c)
    
    pred_c = churn_model.predict(X_c)
    mae_c = mean_absolute_error(y_c, pred_c)
    r2_c = r2_score(y_c, pred_c)
    
    churn_path = os.path.join(models_dir, "churn_model.joblib")
    joblib.dump(churn_model, churn_path)
    print(f"Churn model trained. Saved to {churn_path}. MAE: {mae_c:.3f}, R2: {r2_c:.3f}")
    
    # 3. Fit Challenge Recommender (SVD)
    print("Fitting SVD Challenge Recommender...")
    # 500 donors x 15 challenge types interaction matrix
    np.random.seed(42)
    num_donors = 500
    num_challenges = 15
    
    # Generate sparse random user-item interactions (ratings or binary completions 0 or 1)
    matrix = np.random.choice([0, 1], size=(num_donors, num_challenges), p=[0.75, 0.25])
    
    # TruncatedSVD
    svd = TruncatedSVD(n_components=10, random_state=42)
    latent = svd.fit_transform(matrix)
    
    svd_path = os.path.join(models_dir, "svd_challenges.joblib")
    joblib.dump({
        "svd": svd,
        "matrix": matrix,
        "latent": latent,
        "challenge_types": [
            "Weekend Warrior", "Rare Guardian", "First Responder", "Milestone Master",
            "City Champion", "Holiday Hero", "Summer Saver", "Emergency Anchor",
            "Youth Ambassador", "Platelet Pioneer", "Double Red Donor", "Community Leader",
            "Awareness Advocate", "Winter Warmth", "Rapid Rescue"
        ]
    }, svd_path)
    
    print(f"SVD challenge recommender trained. Saved to {svd_path}.")
    print("\n--- MODEL TRAINING SUMMARY ---")
    print(f"{'Model Name':<25} | {'Metric 1':<15} | {'Metric 2':<15}")
    print("-" * 63)
    print(f"{'Urgency Scorer (XGB)':<25} | {f'MAE: {mae_u:.4f}':<15} | {f'R2: {r2_u:.4f}':<15}")
    print(f"{'Churn Predictor (XGB)':<25} | {f'MAE: {mae_c:.4f}':<15} | {f'R2: {r2_c:.4f}':<15}")
    print(f"{'SVD Recommender (SVD)':<25} | {f'Components: {svd.n_components}':<15} | {f'Variance: {svd.explained_variance_ratio_.sum():.4f}':<15}")

if __name__ == "__main__":
    train_and_save_models()
