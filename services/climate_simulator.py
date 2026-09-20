"""
IPCC Climate Crisis & Compound Infrastructure Failure Stress Simulator
Models non-linear compound climate shocks across all 24 Pan-India national hubs:
  - IPCC SSP Warming Pathways (+1.0C to +4.0C anomaly departure)
  - Power Grid Failure (Cooling blackout multiplying demographic vulnerability)
  - Municipal Water Pipeline Rupture (Halving potable water kiosk coverage)
"""

from typing import Dict, Any, List
import math
from database.models import Location, WeatherData
from services.risk_service import calculate_composite_heat_risk
from ml.preprocessing import calculate_heat_index

def run_climate_stress_simulation(
    temp_anomaly: float = 2.0,
    grid_blackout: bool = False,
    water_pipeline_rupture: bool = False
) -> Dict[str, Any]:
    """
    Executes a dynamic compound stress test across all registered national locations.
    """
    temp_anomaly = max(0.0, min(5.0, float(temp_anomaly)))
    locations = Location.query.all()
    
    simulated_stations = []
    initial_extreme_count = 0
    simulated_extreme_count = 0
    total_projected_bed_deficit = 0
    total_vulnerable_impacted = 0

    for loc in locations:
        vuln = loc.vulnerability
        weather = WeatherData.query.filter_by(location_id=loc.id).order_by(WeatherData.date.desc()).first()

        base_t = weather.temperature if weather else loc.baseline_temp
        base_h = weather.humidity if weather else 50.0

        # Baseline risk
        v_score_base = vuln.vulnerability_score if vuln else 50.0
        pop = vuln.total_population if vuln else 1000000
        beds = vuln.hospital_beds if vuln else 5000
        kiosks = vuln.water_kiosks if vuln else 200

        res_base = calculate_composite_heat_risk(
            temperature=base_t,
            humidity=base_h,
            baseline_temp=loc.baseline_temp,
            vulnerability_score=v_score_base,
            zone_type=loc.zone_type,
            population=pop,
            hospital_beds=beds,
            water_kiosks=kiosks
        )
        if res_base['risk_level'] == 'EXTREME':
            initial_extreme_count += 1

        # Apply Climate & Infrastructure Stress Shocks
        sim_t = round(base_t + temp_anomaly, 1)
        sim_h = base_h  # Humidity assumed constant or elevated
        sim_hi = calculate_heat_index(sim_t, sim_h)

        # Compound Shock 1: Grid Blackout removes air-conditioning/fan relief
        v_multiplier = 1.35 if grid_blackout else 1.0
        sim_v_score = min(100.0, v_score_base * v_multiplier)

        # Compound Shock 2: Water Pipeline Rupture halves effective water kiosk capacity
        effective_kiosks = max(10, int(kiosks * 0.4)) if water_pipeline_rupture else kiosks
        
        # Bed surge pressure under compound heat stress
        effective_beds = beds

        res_sim = calculate_composite_heat_risk(
            temperature=sim_t,
            humidity=sim_h,
            baseline_temp=loc.baseline_temp,
            vulnerability_score=sim_v_score,
            zone_type=loc.zone_type,
            population=pop,
            hospital_beds=effective_beds,
            water_kiosks=effective_kiosks
        )

        if res_sim['risk_level'] == 'EXTREME':
            simulated_extreme_count += 1

        # Calculate projected ICU / heat-stroke hospital bed deficit
        estimated_daily_patients = int((pop * 0.0004) * (res_sim['total_risk_score'] / 40.0))
        available_beds = max(50, int(beds * 0.05)) # ~5% emergency surge allocation
        bed_deficit = max(0, estimated_daily_patients - available_beds)
        total_projected_bed_deficit += bed_deficit

        if res_sim['risk_level'] in ['HIGH', 'EXTREME']:
            total_vulnerable_impacted += int(pop * 0.35)

        simulated_stations.append({
            'location_id': loc.id,
            'name': loc.name,
            'state': loc.state,
            'zone_type': loc.zone_type,
            'baseline_temperature': base_t,
            'simulated_temperature': sim_t,
            'baseline_heat_index': res_base['heat_index'],
            'simulated_heat_index': round(sim_hi, 1),
            'baseline_risk_score': res_base['total_risk_score'],
            'simulated_risk_score': res_sim['total_risk_score'],
            'risk_delta': round(res_sim['total_risk_score'] - res_base['total_risk_score'], 1),
            'baseline_tier': res_base['risk_level'],
            'simulated_tier': res_sim['risk_level'],
            'projected_daily_patients': estimated_daily_patients,
            'hospital_bed_deficit': bed_deficit,
            'status': 'CRITICAL_SURGE' if bed_deficit > 0 else 'MANAGEABLE'
        })

    simulated_stations.sort(key=lambda x: x['simulated_risk_score'], reverse=True)

    return {
        'scenario': {
            'temperature_anomaly_deg_c': temp_anomaly,
            'grid_blackout_active': grid_blackout,
            'water_pipeline_rupture_active': water_pipeline_rupture,
            'ipcc_pathway_reference': 'SSP5-8.5 (High Emissions)' if temp_anomaly >= 3.0 else ('SSP2-4.5 (Intermediate)' if temp_anomaly >= 1.5 else 'SSP1-2.6 (Paris Goal)')
        },
        'systemic_impact': {
            'total_stations': len(locations),
            'initial_extreme_stations': initial_extreme_count,
            'simulated_extreme_stations': simulated_extreme_count,
            'newly_critical_stations': max(0, simulated_extreme_count - initial_extreme_count),
            'total_projected_bed_deficit': total_projected_bed_deficit,
            'total_vulnerable_population_impacted': total_vulnerable_impacted
        },
        'stations': simulated_stations
    }
