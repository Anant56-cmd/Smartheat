"""
Explainable AI (XAI) Engine for SMARTHEAT
Provides local feature attribution, contrastive risk explanations, and
counterfactual reasoning for tree-based heatwave prediction models.
"""

import numpy as np
import pandas as pd
from ml.preprocessing import engineer_features
from ml.train_model import MODEL_FEATURES

NEUTRAL_BASELINE = {
    'Temperature': 28.0,
    'Humidity': 45.0,
    'Wind_Speed': 12.0,
    'Rainfall': 0.0,
    'Pressure': 1013.25
}

HUMAN_FRIENDLY_NAMES = {
    'Temperature': 'Ambient Air Temperature',
    'Humidity': 'Relative Humidity',
    'Wind_Speed': 'Surface Wind Velocity',
    'Rainfall': 'Precipitation',
    'Pressure': 'Barometric Pressure',
    'Heat_Index': 'Rothfusz Heat Index ("Feels Like")',
    'Temp_Humid_Product': 'Thermal Humidity Synergy',
    'Dew_Point_Approx': 'Moisture Saturation (Dew Point)',
    'Wind_Cooling_Factor': 'Evaporative Wind Cooling',
    'Vapor_Pressure_Est': 'Atmospheric Vapor Pressure'
}

def explain_prediction(model, scaler, input_dict, target_class=None):
    """
    Computes local feature attribution (XAI) for a single prediction.
    Measures how each meteorological and engineered feature drives the model's
    predicted risk tier relative to a comfortable baseline state.
    """
    input_df = pd.DataFrame([input_dict])
    featured_df = engineer_features(input_df)
    X_input = featured_df[MODEL_FEATURES]
    X_input_scaled = scaler.transform(X_input)

    classes = list(model.classes_)
    pred_class = model.predict(X_input_scaled)[0]
    if not target_class or target_class not in classes:
        target_class = pred_class

    target_idx = classes.index(target_class)
    current_prob = float(model.predict_proba(X_input_scaled)[0][target_idx])

    base_df = pd.DataFrame([NEUTRAL_BASELINE])
    featured_base = engineer_features(base_df)
    X_base = featured_base[MODEL_FEATURES]
    X_base_scaled = scaler.transform(X_base)
    base_prob = float(model.predict_proba(X_base_scaled)[0][target_idx])

    attributions = []
    total_abs_impact = 0.0

    for col in MODEL_FEATURES:
        X_perturbed = X_input.copy()
        X_perturbed[col] = X_base[col].values[0]
        X_perturbed_scaled = scaler.transform(X_perturbed)

        perturbed_prob = float(model.predict_proba(X_perturbed_scaled)[0][target_idx])
        marginal_impact = current_prob - perturbed_prob
        total_abs_impact += abs(marginal_impact)

        val = float(featured_df[col].iloc[0])
        base_val = float(featured_base[col].iloc[0])

        attributions.append({
            'feature': col,
            'display_name': HUMAN_FRIENDLY_NAMES.get(col, col),
            'value': round(val, 2),
            'baseline_value': round(base_val, 2),
            'raw_impact': round(marginal_impact, 4),
            'direction': 'INCREASES_RISK' if marginal_impact >= 0 else 'REDUCES_RISK'
        })

    for item in attributions:
        if total_abs_impact > 1e-6:
            item['percentage'] = round((abs(item['raw_impact']) / total_abs_impact) * 100, 1)
        else:
            item['percentage'] = round(100.0 / len(MODEL_FEATURES), 1)

    attributions.sort(key=lambda x: abs(x['raw_impact']), reverse=True)

    risk_drivers = [a for a in attributions if a['direction'] == 'INCREASES_RISK']
    protective_factors = [a for a in attributions if a['direction'] == 'REDUCES_RISK']

    counterfactuals = generate_counterfactuals(
        model=model,
        scaler=scaler,
        input_dict=input_dict,
        current_pred=pred_class
    )

    return {
        'target_class': target_class,
        'predicted_class': pred_class,
        'current_probability': round(current_prob * 100, 1),
        'base_probability': round(base_prob * 100, 1),
        'probability_delta': round((current_prob - base_prob) * 100, 1),
        'feature_attributions': attributions,
        'top_risk_drivers': risk_drivers[:3],
        'protective_factors': protective_factors[:3],
        'counterfactuals': counterfactuals
    }

def generate_counterfactuals(model, scaler, input_dict, current_pred):
    suggestions = []
    temp = float(input_dict.get('Temperature', 35.0))
    humidity = float(input_dict.get('Humidity', 60.0))

    if current_pred in ['HIGH', 'EXTREME']:
        for delta_t in [2.0, 4.0, 6.0]:
            test_dict = input_dict.copy()
            test_dict['Temperature'] = max(20.0, temp - delta_t)
            test_df = engineer_features(pd.DataFrame([test_dict]))[MODEL_FEATURES]
            p = model.predict(scaler.transform(test_df))[0]
            if p != current_pred:
                suggestions.append({
                    'action': f"Lower ambient temperature by {delta_t}°C (to {test_dict['Temperature']:.1f}°C)",
                    'resulting_tier': p,
                    'feasibility': 'Urban canopy shading, public cooling shelters, roof misting'
                })
                break

        for delta_h in [15.0, 25.0]:
            test_dict = input_dict.copy()
            test_dict['Humidity'] = max(20.0, humidity - delta_h)
            test_df = engineer_features(pd.DataFrame([test_dict]))[MODEL_FEATURES]
            p = model.predict(scaler.transform(test_df))[0]
            if p != current_pred:
                suggestions.append({
                    'action': f"Reduce relative humidity by {delta_h}% (to {test_dict['Humidity']:.1f}%)",
                    'resulting_tier': p,
                    'feasibility': 'Dehumidified indoor transit hubs & cross-ventilation corridors'
                })
                break

        current_wind = float(input_dict.get('Wind_Speed', 8.0))
        if current_wind < 20.0:
            test_dict = input_dict.copy()
            test_dict['Wind_Speed'] = current_wind + 15.0
            test_df = engineer_features(pd.DataFrame([test_dict]))[MODEL_FEATURES]
            p = model.predict(scaler.transform(test_df))[0]
            if p != current_pred:
                suggestions.append({
                    'action': "Increase surface ventilation / airflow by 15 km/h",
                    'resulting_tier': p,
                    'feasibility': 'High-velocity industrial cooling fans in crowded markets'
                })

    return suggestions
