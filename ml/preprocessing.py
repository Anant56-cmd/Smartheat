import math
import numpy as np
import pandas as pd

def calculate_heat_index(temp_c, humidity):
    """
    Calculate the NOAA Heat Index in degrees Celsius.
    Converts Celsius to Fahrenheit, applies the NWS Rothfusz regression
    with official NOAA boundary adjustments, then converts back to Celsius.
    """
    # Guard against invalid humidity
    rh = max(0.0, min(100.0, float(humidity)))
    t_c = float(temp_c)
    t_f = (t_c * 9.0 / 5.0) + 32.0

    # If temperature is below 80°F (26.7°C), simplified formula
    if t_f < 80.0:
        hi_f = 0.5 * (t_f + 61.0 + ((t_f - 68.0) * 1.2) + (rh * 0.094))
    else:
        # Full Rothfusz regression equation
        hi_f = (
            -42.379
            + 2.04901523 * t_f
            + 10.14333127 * rh
            - 0.22475541 * t_f * rh
            - 0.00683783 * (t_f ** 2)
            - 0.05481717 * (rh ** 2)
            + 0.00122874 * (t_f ** 2) * rh
            + 0.00085282 * t_f * (rh ** 2)
            - 0.00000199 * (t_f ** 2) * (rh ** 2)
        )
        # NOAA Adjustment for low humidity
        if rh < 13.0 and 80.0 <= t_f <= 112.0:
            adj = ((13.0 - rh) / 4.0) * math.sqrt(max(0.0, (17.0 - abs(t_f - 95.0)) / 17.0))
            hi_f -= adj
        # NOAA Adjustment for high humidity
        elif rh > 85.0 and 80.0 <= t_f <= 87.0:
            adj = ((rh - 85.0) / 10.0) * ((87.0 - t_f) / 5.0)
            hi_f += adj

    # Convert back to Celsius
    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return round(hi_c, 2)

def determine_risk_label(temp_c, heat_index_c):
    """
    Determine categorical heat wave risk level:
    LOW, MODERATE, HIGH, EXTREME based on meteorological criteria.
    """
    t = float(temp_c)
    hi = float(heat_index_c)

    # Extreme condition: Heat index >= 54°C or absolute temp >= 45°C
    if hi >= 54.0 or t >= 45.0:
        return 'EXTREME'
    elif hi >= 41.0 or t >= 40.0:
        return 'HIGH'
    elif hi >= 32.0 or t >= 35.0:
        return 'MODERATE'
    else:
        return 'LOW'

def engineer_features(df):
    """
    Generate domain-specific meteorological features for machine learning.
    """
    data = df.copy()

    # Ensure required columns exist
    if 'Temperature' not in data.columns or 'Humidity' not in data.columns:
        raise ValueError("Dataset must contain 'Temperature' and 'Humidity' columns.")

    # Fill optional missing columns with domain defaults
    if 'Wind_Speed' not in data.columns:
        data['Wind_Speed'] = 10.0
    else:
        data['Wind_Speed'] = data['Wind_Speed'].fillna(10.0)

    if 'Rainfall' not in data.columns:
        data['Rainfall'] = 0.0
    else:
        data['Rainfall'] = data['Rainfall'].fillna(0.0)

    if 'Pressure' not in data.columns:
        data['Pressure'] = 1013.25
    else:
        data['Pressure'] = data['Pressure'].fillna(1013.25)

    # Clean numeric types
    data['Temperature'] = pd.to_numeric(data['Temperature'], errors='coerce')
    data['Humidity'] = pd.to_numeric(data['Humidity'], errors='coerce')
    data['Wind_Speed'] = pd.to_numeric(data['Wind_Speed'], errors='coerce').fillna(10.0)
    data['Rainfall'] = pd.to_numeric(data['Rainfall'], errors='coerce').fillna(0.0)
    data['Pressure'] = pd.to_numeric(data['Pressure'], errors='coerce').fillna(1013.25)

    # Impute missing Temperature and Humidity with column median if any
    data['Temperature'] = data['Temperature'].fillna(data['Temperature'].median() if not data['Temperature'].empty else 30.0)
    data['Humidity'] = data['Humidity'].fillna(data['Humidity'].median() if not data['Humidity'].empty else 50.0)

    # Calculate Heat Index
    data['Heat_Index'] = [
        calculate_heat_index(t, h) for t, h in zip(data['Temperature'], data['Humidity'])
    ]

    # Additional engineered features
    # 1. Temp-Humidity Interaction Index
    data['Temp_Humid_Product'] = (data['Temperature'] * data['Humidity']) / 100.0
    
    # 2. Dew Point Approximation (Magnus formula approximation)
    data['Dew_Point_Approx'] = data['Temperature'] - ((100.0 - data['Humidity']) / 5.0)

    # 3. Wind Chill / Ventilation Offset
    data['Wind_Cooling_Factor'] = data['Temperature'] - (0.05 * data['Wind_Speed'])

    # 4. Vapor Pressure Indicator
    data['Vapor_Pressure_Est'] = (data['Humidity'] / 100.0) * (6.112 * np.exp((17.67 * data['Temperature']) / (data['Temperature'] + 243.5)))

    # Ground-truth target label
    data['Risk_Level'] = [
        determine_risk_label(t, hi) for t, hi in zip(data['Temperature'], data['Heat_Index'])
    ]

    return data

def clean_and_validate_dataset(df):
    """
    Validate and clean uploaded weather CSV data.
    Removes duplicates, trims whitespace, handles case variations in column names.
    """
    data = df.copy()

    # Normalize column names: strip whitespace, capitalize first letter
    col_map = {}
    for col in data.columns:
        c_clean = col.strip().replace(' ', '_').lower()
        if 'temp' in c_clean:
            col_map[col] = 'Temperature'
        elif 'humid' in c_clean:
            col_map[col] = 'Humidity'
        elif 'wind' in c_clean:
            col_map[col] = 'Wind_Speed'
        elif 'rain' in c_clean or 'precip' in c_clean:
            col_map[col] = 'Rainfall'
        elif 'press' in c_clean:
            col_map[col] = 'Pressure'
        elif 'loc' in c_clean or 'city' in c_clean:
            col_map[col] = 'Location'
        elif 'date' in c_clean:
            col_map[col] = 'Date'
            
    data = data.rename(columns=col_map)

    # Drop exact duplicates
    initial_count = len(data)
    data = data.drop_duplicates()
    duplicates_removed = initial_count - len(data)

    # Filter out physical impossibilities
    if 'Temperature' in data.columns:
        data = data[(data['Temperature'] >= -10.0) & (data['Temperature'] <= 60.0)]
    if 'Humidity' in data.columns:
        data = data[(data['Humidity'] >= 0.0) & (data['Humidity'] <= 100.0)]

    return data, duplicates_removed
