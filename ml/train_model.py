import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from datetime import datetime
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)

from ml.preprocessing import engineer_features, clean_and_validate_dataset

MODEL_FEATURES = [
    'Temperature',
    'Humidity',
    'Wind_Speed',
    'Rainfall',
    'Pressure',
    'Heat_Index',
    'Temp_Humid_Product',
    'Dew_Point_Approx',
    'Wind_Cooling_Factor',
    'Vapor_Pressure_Est'
]

CLASS_LABELS = ['LOW', 'MODERATE', 'HIGH', 'EXTREME']

def train_and_evaluate(csv_path=None, model_dir=None):
    """
    Train Random Forest and Decision Tree models on weather dataset,
    compute legitimate validation metrics, and persist serialized artifacts.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if not csv_path:
        real_csv = os.path.join(base_dir, 'data', 'real_weather_history.csv')
        sample_csv = os.path.join(base_dir, 'data', 'sample_weather.csv')
        csv_path = real_csv if os.path.exists(real_csv) else sample_csv
    if not model_dir:
        model_dir = os.path.join(base_dir, 'saved_models')

    os.makedirs(model_dir, exist_ok=True)

    print(f"[*] Loading training dataset from: {csv_path}")
    raw_df = pd.read_csv(csv_path)

    # 1. Clean & validate
    cleaned_df, dupes = clean_and_validate_dataset(raw_df)
    print(f"[*] Cleaned data: {len(cleaned_df)} records remaining ({dupes} duplicates removed)")

    # 2. Feature engineering
    featured_df = engineer_features(cleaned_df)

    X = featured_df[MODEL_FEATURES]
    y = featured_df['Risk_Level']

    # Class distribution check
    print(f"[*] Class distribution:\n{y.value_counts()}")

    # 3. Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"[*] Train set: {len(X_train)} samples, Test set: {len(X_test)} samples")

    # 4. Feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Train Primary Model: Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=4,
        random_state=42,
        class_weight='balanced'
    )
    rf_model.fit(X_train_scaled, y_train)
    y_pred_rf = rf_model.predict(X_test_scaled)

    # 6. Train Comparative Model: Decision Tree
    dt_model = DecisionTreeClassifier(
        max_depth=6,
        random_state=42,
        class_weight='balanced'
    )
    dt_model.fit(X_train_scaled, y_train)
    y_pred_dt = dt_model.predict(X_test_scaled)

    # 7. Evaluate Random Forest
    acc_rf = float(accuracy_score(y_test, y_pred_rf))
    p_rf, r_rf, f1_rf, _ = precision_recall_fscore_support(y_test, y_pred_rf, average='weighted', zero_division=0)
    cm_rf = confusion_matrix(y_test, y_pred_rf, labels=CLASS_LABELS).tolist()
    
    # Per-class metrics
    p_class, r_class, f1_class, supp_class = precision_recall_fscore_support(
        y_test, y_pred_rf, labels=CLASS_LABELS, zero_division=0
    )
    per_class_metrics = {}
    for idx, lbl in enumerate(CLASS_LABELS):
        per_class_metrics[lbl] = {
            'precision': round(float(p_class[idx]) * 100, 2),
            'recall': round(float(r_class[idx]) * 100, 2),
            'f1_score': round(float(f1_class[idx]) * 100, 2),
            'support': int(supp_class[idx])
        }

    # Feature Importance
    importances = rf_model.feature_importances_
    feature_imp_list = [
        {'feature': feat, 'importance': round(float(imp) * 100, 2)}
        for feat, imp in sorted(zip(MODEL_FEATURES, importances), key=lambda x: x[1], reverse=True)
    ]

    # 8. Evaluate Decision Tree
    acc_dt = float(accuracy_score(y_test, y_pred_dt))
    p_dt, r_dt, f1_dt, _ = precision_recall_fscore_support(y_test, y_pred_dt, average='weighted', zero_division=0)

    # 9. Store metrics dictionary
    metrics_payload = {
        'training_timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'dataset_total_samples': len(cleaned_df),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'classes': CLASS_LABELS,
        'features': MODEL_FEATURES,
        'primary_model': {
            'name': 'Random Forest Classifier',
            'accuracy': round(acc_rf * 100, 2),
            'precision_weighted': round(float(p_rf) * 100, 2),
            'recall_weighted': round(float(r_rf) * 100, 2),
            'f1_weighted': round(float(f1_rf) * 100, 2),
            'confusion_matrix': cm_rf,
            'per_class': per_class_metrics,
            'feature_importance': feature_imp_list
        },
        'comparative_model': {
            'name': 'Decision Tree Classifier',
            'accuracy': round(acc_dt * 100, 2),
            'precision_weighted': round(float(p_dt) * 100, 2),
            'recall_weighted': round(float(r_dt) * 100, 2),
            'f1_weighted': round(float(f1_dt) * 100, 2)
        }
    }

    # 10. Persist artifacts
    rf_model_path = os.path.join(model_dir, 'heatwave_rf_model.pkl')
    dt_model_path = os.path.join(model_dir, 'heatwave_dt_model.pkl')
    scaler_path = os.path.join(model_dir, 'scaler.pkl')
    metrics_path = os.path.join(model_dir, 'model_metrics.json')

    joblib.dump(rf_model, rf_model_path)
    joblib.dump(dt_model, dt_model_path)
    joblib.dump(scaler, scaler_path)

    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"[+] Successfully trained & evaluated models!")
    print(f"    - Random Forest Accuracy: {metrics_payload['primary_model']['accuracy']}%")
    print(f"    - Decision Tree Accuracy: {metrics_payload['comparative_model']['accuracy']}%")
    print(f"    - Artifacts saved to: {model_dir}")

    return metrics_payload

if __name__ == '__main__':
    train_and_evaluate()
