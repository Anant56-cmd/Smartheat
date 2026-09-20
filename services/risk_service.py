import json
from config import Config
from ml.preprocessing import calculate_heat_index

def compute_hazard_score(temperature, humidity, baseline_temp=32.0):
    """
    Compute meteorological hazard score (0 to 100) based on
    NOAA Heat Index and temperature anomaly departure from baseline.
    """
    hi = calculate_heat_index(temperature, humidity)
    temp = float(temperature)
    
    # 1. Base score from Heat Index (0 - 100 scale)
    if hi < 27.0:
        hi_score = max(5.0, (hi / 27.0) * 20.0)
    elif hi < 32.0:
        hi_score = 20.0 + ((hi - 27.0) / (32.0 - 27.0)) * 20.0  # 20 - 40
    elif hi < 41.0:
        hi_score = 40.0 + ((hi - 32.0) / (41.0 - 32.0)) * 25.0  # 40 - 65
    elif hi < 54.0:
        hi_score = 65.0 + ((hi - 41.0) / (54.0 - 41.0)) * 25.0  # 65 - 90
    else:
        hi_score = min(100.0, 90.0 + ((hi - 54.0) / 10.0) * 10.0) # 90 - 100

    # 2. Temperature Anomaly factor (IMD criteria: departure >= 4.5°C is heatwave, >= 6.4°C is severe)
    departure = max(0.0, temp - float(baseline_temp))
    anomaly_penalty = 0.0
    if departure >= 6.4:
        anomaly_penalty = 15.0
    elif departure >= 4.5:
        anomaly_penalty = 10.0
    elif departure >= 3.0:
        anomaly_penalty = 5.0

    hazard_score = min(100.0, hi_score + anomaly_penalty)
    return round(hazard_score, 1), round(hi, 1)

def compute_exposure_score(zone_type='Urban', population=1000000):
    """
    Compute population and spatial exposure score (0 to 100).
    """
    zone_weights = {
        'Urban': 75.0,
        'Industrial': 70.0,
        'Coastal Urban': 80.0,
        'Arid Urban': 85.0,
        'Gangetic Plain': 78.0,
        'Suburban': 50.0,
        'Rural': 30.0
    }
    base_zone = zone_weights.get(zone_type, 60.0)
    
    # Population scale factor
    pop = int(population)
    if pop > 10000000:
        pop_bonus = 15.0
    elif pop > 5000000:
        pop_bonus = 10.0
    elif pop > 2000000:
        pop_bonus = 5.0
    else:
        pop_bonus = 0.0

    return min(100.0, base_zone + pop_bonus)

def compute_healthcare_deficit(hospital_beds, water_kiosks, population):
    """
    Compute deficit score (0 to 100). Higher deficit = higher risk.
    """
    pop = max(int(population), 1000)
    beds = int(hospital_beds)
    kiosks = int(water_kiosks)

    beds_per_k = beds / (pop / 1000.0)     # WHO guideline recommends ~3-5 beds per 1000
    kiosks_per_10k = kiosks / (pop / 10000.0) # Target: >= 2 per 10,000

    bed_deficit = max(0.0, min(50.0, (4.0 - beds_per_k) * 12.5))
    water_deficit = max(0.0, min(50.0, (3.0 - kiosks_per_10k) * 16.6))

    return min(100.0, bed_deficit + water_deficit)

def calculate_composite_heat_risk(
    temperature,
    humidity,
    baseline_temp=32.0,
    vulnerability_score=50.0,
    zone_type='Urban',
    population=1000000,
    hospital_beds=5000,
    water_kiosks=200,
    weights=None
):
    """
    Calculate the transparent, composite 0-100 Heat Risk Score.
    Incorporates:
      - Meteorological Hazard (45%)
      - Demographics & Social Vulnerability (30%)
      - Population Exposure (15%)
      - Healthcare & Water Deficit (10%)
    """
    if weights is None:
        w_hazard = Config.RISK_WEIGHT_HAZARD
        w_vuln = Config.RISK_WEIGHT_VULNERABILITY
        w_exposure = Config.RISK_WEIGHT_EXPOSURE
        w_deficit = Config.RISK_WEIGHT_HEALTHCARE_DEFICIT
    else:
        w_hazard = weights.get('hazard', 0.45)
        w_vuln = weights.get('vulnerability', 0.30)
        w_exposure = weights.get('exposure', 0.15)
        w_deficit = weights.get('deficit', 0.10)

    hazard_score, heat_index = compute_hazard_score(temperature, humidity, baseline_temp)
    vuln_score = float(vulnerability_score)
    exposure_score = compute_exposure_score(zone_type, population)
    deficit_score = compute_healthcare_deficit(hospital_beds, water_kiosks, population)

    total_score = (
        (w_hazard * hazard_score) +
        (w_vuln * vuln_score) +
        (w_exposure * exposure_score) +
        (w_deficit * deficit_score)
    )
    total_score = round(min(100.0, max(0.0, total_score)), 1)

    # Risk category classification based on backend configuration
    if total_score <= Config.THRESHOLD_LOW_MAX:
        risk_level = 'LOW'
    elif total_score <= Config.THRESHOLD_MODERATE_MAX:
        risk_level = 'MODERATE'
    elif total_score <= Config.THRESHOLD_HIGH_MAX:
        risk_level = 'HIGH'
    else:
        risk_level = 'EXTREME'

    breakdown = {
        'hazard_score': hazard_score,
        'hazard_weight': w_hazard,
        'hazard_contribution': round(w_hazard * hazard_score, 1),
        
        'vulnerability_score': vuln_score,
        'vulnerability_weight': w_vuln,
        'vulnerability_contribution': round(w_vuln * vuln_score, 1),
        
        'exposure_score': exposure_score,
        'exposure_weight': w_exposure,
        'exposure_contribution': round(w_exposure * exposure_score, 1),
        
        'deficit_score': deficit_score,
        'deficit_weight': w_deficit,
        'deficit_contribution': round(w_deficit * deficit_score, 1),
        
        'heat_index': heat_index,
        'temperature': temperature,
        'humidity': humidity,
        'baseline_temp': baseline_temp,
        'formula_explanation': (
            f"Total ({total_score}) = "
            f"[{w_hazard} * {hazard_score} (Hazard)] + "
            f"[{w_vuln} * {vuln_score} (Vulnerability)] + "
            f"[{w_exposure} * {exposure_score} (Exposure)] + "
            f"[{w_deficit} * {deficit_score} (Deficit)]"
        )
    }

    return {
        'total_risk_score': total_score,
        'risk_level': risk_level,
        'hazard_score': hazard_score,
        'vulnerability_score': vuln_score,
        'exposure_score': exposure_score,
        'deficit_score': deficit_score,
        'heat_index': heat_index,
        'breakdown': breakdown,
        'breakdown_json': json.dumps(breakdown)
    }
