"""
Urgency Model Training Script.
Generates training data, fits XGBoost regressor, and prints evaluation metrics (MAE, RMSE, Confusion Matrix).
"""
import os
import sys
import random
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

# Add backend root to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_data(num_samples=1500):
    """Generate synthetic patient profiles and clinical urgency labels."""
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
        # Base clinical scoring rule with minor noise
        base = 10.0 - (hemoglobin[i] / 16.5) * 4.0
        overdue = min(days_overdue[i] / 30.0, 3.0)
        cardiac = 2.0 if has_cardiac_flag[i] == 1 else 0.0
        noise = random.gauss(0, 0.25)
        
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

def get_priority_class(score: float) -> str:
    """Map continuous score into clinical priority categories."""
    if score >= 7.5:
        return "CRITICAL"
    elif score >= 5.0:
        return "HIGH"
    else:
        return "ROUTINE"

def train_urgency_model():
    print("Generating synthetic clinical datasets...")
    df = generate_data()
    
    X = df[["hemoglobin", "days_overdue", "has_cardiac_flag", "age", "transfusion_count", "antibody_count"]]
    y = df["urgency_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Fitting XGBoost regressor model...")
    model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Regression evaluation
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    
    print("\n=== REGRESSION PERFORMANCE ===")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    
    # Classification evaluation (by binning into clinical priorities)
    y_test_classes = [get_priority_class(val) for val in y_test]
    pred_classes = [get_priority_class(val) for val in predictions]
    
    labels = ["ROUTINE", "HIGH", "CRITICAL"]
    cm = confusion_matrix(y_test_classes, pred_classes, labels=labels)
    
    print("\n=== CLINICAL PRIORITY CONFUSION MATRIX ===")
    print(f"{'':<12} | {'Pred: ROUTINE':<13} | {'Pred: HIGH':<13} | {'Pred: CRITICAL':<13}")
    print("-" * 65)
    for idx, label in enumerate(labels):
        print(f"True: {label:<8} | {cm[idx][0]:<13} | {cm[idx][1]:<13} | {cm[idx][2]:<13}")
        
    print("\n=== CLASSIFICATION REPORT ===")
    print(classification_report(y_test_classes, pred_classes, target_names=labels))
    
    # Save model
    models_dir = os.path.join("ml", "models")
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "urgency_model.joblib")
    joblib.dump(model, model_path)
    print(f"Model saved successfully to {model_path}")

if __name__ == "__main__":
    train_urgency_model()
