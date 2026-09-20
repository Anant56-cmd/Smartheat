import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from ml.preprocessing import calculate_heat_index, engineer_features
from ml.train_model import MODEL_FEATURES, CLASS_LABELS

_cached_model = None
_cached_scaler = None

def get_model_and_scaler(model_dir=None):
    """Lazy load and cache model and scaler."""
    global _cached_model, _cached_scaler
    if _cached_model is None or _cached_scaler is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if not model_dir:
            model_dir = os.path.join(base_dir, 'saved_models')
        
        model_path = os.path.join(model_dir, 'heatwave_rf_model.pkl')
        scaler_path = os.path.join(model_dir, 'scaler.pkl')
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            from ml.train_model import train_and_evaluate
            train_and_evaluate(model_dir=model_dir)

        _cached_model = joblib.load(model_path)
        _cached_scaler = joblib.load(scaler_path)

    return _cached_model, _cached_scaler

def predict_single(temperature, humidity, wind_speed=10.0, rainfall=0.0, pressure=1013.25, model_dir=None, include_xai=True):
    """
    Predict heat-wave risk category, probabilities, and Explainable AI (XAI) feature attribution.
    """
    model, scaler = get_model_and_scaler(model_dir)
    
    input_dict = {
        'Temperature': float(temperature),
        'Humidity': float(humidity),
        'Wind_Speed': float(wind_speed) if wind_speed is not None else 10.0,
        'Rainfall': float(rainfall) if rainfall is not None else 0.0,
        'Pressure': float(pressure) if pressure is not None else 1013.25
    }
    input_df = pd.DataFrame([input_dict])

    featured_df = engineer_features(input_df)
    X = featured_df[MODEL_FEATURES]
    X_scaled = scaler.transform(X)

    # Predict class and probabilities
    predicted_class = model.predict(X_scaled)[0]
    probs = model.predict_proba(X_scaled)[0]
    model_classes = list(model.classes_)
    
    prob_dict = {}
    for cls_name, prob in zip(model_classes, probs):
        prob_dict[cls_name] = round(float(prob) * 100, 1)

    predicted_idx = model_classes.index(predicted_class)
    confidence = float(probs[predicted_idx])

    hi = float(featured_df['Heat_Index'].iloc[0])
    dew_point = float(featured_df['Dew_Point_Approx'].iloc[0])
    cooling_factor = float(featured_df['Wind_Cooling_Factor'].iloc[0])

    response = {
        'predicted_risk': predicted_class,
        'confidence': round(confidence * 100, 1),
        'confidence_ratio': round(confidence, 4),
        'heat_index': round(hi, 2),
        'temperature': float(temperature),
        'humidity': float(humidity),
        'wind_speed': float(wind_speed) if wind_speed is not None else 10.0,
        'dew_point': round(dew_point, 2),
        'cooling_factor': round(cooling_factor, 2),
        'probabilities': prob_dict,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    if include_xai:
        try:
            from ml.explainability import explain_prediction
            response['explainability'] = explain_prediction(model, scaler, input_dict, target_class=predicted_class)
        except Exception as e:
            response['explainability'] = {'error': str(e)}

    return response

def predict_batch(df, model_dir=None):
    """
    Predict heat-wave risk for an entire batch DataFrame.
    """
    model, scaler = get_model_and_scaler(model_dir)
    featured_df = engineer_features(df)
    X = featured_df[MODEL_FEATURES]
    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)
    probs = model.predict_proba(X_scaled)
    max_probs = np.max(probs, axis=1)

    result_df = df.copy()
    result_df['Heat_Index'] = featured_df['Heat_Index']
    result_df['Predicted_Risk'] = preds
    result_df['Confidence'] = np.round(max_probs * 100, 1)
    return result_df
