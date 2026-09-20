"""
Versioned Enterprise RESTful API (v1) for SMARTHEAT
Includes endpoints for:
  - Real-time Heat Wave Inference with XAI Feature Attribution
  - Algorithmic Municipal Resource Dispatch Optimization
  - SRE Observability: Liveness/Readiness Health Probe
  - Prometheus Telemetry Metrics
"""

import time
import os
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
from database.db import db
from database.models import Location, Alert, WeatherData
from ml.predictor import predict_single, get_model_and_scaler
from ml.explainability import explain_prediction
from services.resource_optimizer import MunicipalResourceOptimizer

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# In-memory telemetry counters for SRE observability
TELEMETRY = {
    'start_time': time.time(),
    'requests_total': 0,
    'predictions_total': 0,
    'optimizations_total': 0,
    'latencies': []
}

@api_v1_bp.before_request
def record_start_time():
    request.start_time = time.time()
    TELEMETRY['requests_total'] += 1

@api_v1_bp.after_request
def record_latency(response):
    if hasattr(request, 'start_time'):
        latency = time.time() - request.start_time
        TELEMETRY['latencies'].append(latency)
        if len(TELEMETRY['latencies']) > 1000:
            TELEMETRY['latencies'].pop(0)
    return response

@api_v1_bp.route('/health', methods=['GET'])
def health_check():
    """
    SRE Liveness & Readiness Probe.
    Checks database connection, ML model caching status, and system memory.
    """
    db_ok = False
    try:
        db.session.execute(db.select(1)).scalar()
        db_ok = True
    except Exception:
        db_ok = False

    model_loaded = False
    try:
        m, s = get_model_and_scaler()
        model_loaded = (m is not None and s is not None)
    except Exception:
        model_loaded = False

    process = psutil.Process(os.getpid()) if hasattr(psutil, 'Process') else None
    mem_mb = round(process.memory_info().rss / (1024 * 1024), 2) if process else 0.0

    status = "healthy" if (db_ok and model_loaded) else "degraded"
    status_code = 200 if status == "healthy" else 503

    uptime_sec = round(time.time() - TELEMETRY['start_time'], 1)

    return jsonify({
        'status': status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime_sec,
        'checks': {
            'database': 'up' if db_ok else 'down',
            'ml_model_cache': 'ready' if model_loaded else 'unloaded',
            'memory_rss_mb': mem_mb
        },
        'version': '2.1.0'
    }), status_code

@api_v1_bp.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """
    Prometheus-compatible plain text metrics exposition format.
    """
    uptime_sec = time.time() - TELEMETRY['start_time']
    active_alerts = Alert.query.filter_by(status='Active').count()
    total_locations = Location.query.count()

    latencies = TELEMETRY['latencies']
    p50 = sorted(latencies)[int(len(latencies) * 0.50)] if latencies else 0.0
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0

    metrics_text = f"""# HELP smartheat_uptime_seconds Total application uptime in seconds
# TYPE smartheat_uptime_seconds gauge
smartheat_uptime_seconds {uptime_sec:.2f}

# HELP smartheat_http_requests_total Total number of HTTP requests handled
# TYPE smartheat_http_requests_total counter
smartheat_http_requests_total {TELEMETRY['requests_total']}

# HELP smartheat_predictions_total Total ML inference operations served
# TYPE smartheat_predictions_total counter
smartheat_predictions_total {TELEMETRY['predictions_total']}

# HELP smartheat_optimizations_total Total resource optimization runs computed
# TYPE smartheat_optimizations_total counter
smartheat_optimizations_total {TELEMETRY['optimizations_total']}

# HELP smartheat_active_alerts Current number of active heatwave alerts
# TYPE smartheat_active_alerts gauge
smartheat_active_alerts {active_alerts}

# HELP smartheat_monitored_locations Total registered municipal monitoring locations
# TYPE smartheat_monitored_locations gauge
smartheat_monitored_locations {total_locations}

# HELP smartheat_latency_p50 Median API latency in seconds
# TYPE smartheat_latency_p50 gauge
smartheat_latency_p50 {p50:.4f}

# HELP smartheat_latency_p95 95th percentile API latency in seconds
# TYPE smartheat_latency_p95 gauge
smartheat_latency_p95 {p95:.4f}
"""
    return Response(metrics_text, mimetype='text/plain; version=0.0.4; charset=utf-8')

@api_v1_bp.route('/predict', methods=['POST'])
def api_predict():
    """
    Enterprise ML prediction endpoint with Explainable AI (XAI) feature attribution.
    Request JSON:
        {
            "temperature": 42.5,
            "humidity": 55.0,
            "wind_speed": 10.0,
            "rainfall": 0.0,
            "pressure": 1012.0
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    temp = data.get('temperature')
    hum = data.get('humidity')

    if temp is None or hum is None:
        return jsonify({'error': 'Missing required fields: temperature, humidity'}), 400

    try:
        temp = float(temp)
        hum = float(hum)
        wind = float(data.get('wind_speed', 10.0))
        rainfall = float(data.get('rainfall', 0.0))
        pressure = float(data.get('pressure', 1013.25))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid numeric parameters provided.'}), 400

    t0 = time.time()
    res = predict_single(
        temperature=temp,
        humidity=hum,
        wind_speed=wind,
        rainfall=rainfall,
        pressure=pressure
    )

    # Compute XAI feature attribution
    m, s = get_model_and_scaler()
    input_dict = {
        'Temperature': temp,
        'Humidity': hum,
        'Wind_Speed': wind,
        'Rainfall': rainfall,
        'Pressure': pressure
    }
    xai = explain_prediction(m, s, input_dict)
    res['explainability'] = xai
    res['inference_latency_ms'] = round((time.time() - t0) * 1000, 2)

    TELEMETRY['predictions_total'] += 1
    return jsonify(res), 200

@api_v1_bp.route('/optimize/dispatch', methods=['POST'])
def api_optimize_dispatch():
    """
    Algorithmic resource allocation endpoint.
    Accepts fleet parameters and returns optimal distribution matrix across wards.
    """
    data = request.get_json(force=True, silent=True) or {}
    fleet_tankers = int(data.get('fleet_water_tankers', 30))
    total_ors = int(data.get('total_ors_kits', 5000))
    emergency_beds = int(data.get('emergency_beds', 120))

    # Fetch live or registered wards from DB
    locations = Location.query.all()
    wards_payload = []
    for loc in locations:
        vuln = loc.vulnerability
        weather = WeatherData.query.filter_by(location_id=loc.id).order_by(WeatherData.date.desc()).first()
        temp = weather.temperature if weather else 38.0
        hi = weather.heat_index if weather else 42.0

        # Approximate risk score
        risk_score = min(100.0, max(20.0, (hi * 1.5) + (vuln.vulnerability_score * 0.3 if vuln else 20.0)))
        risk_level = 'EXTREME' if risk_score >= 75 else ('HIGH' if risk_score >= 60 else 'MODERATE')

        wards_payload.append({
            'id': loc.id,
            'name': loc.name,
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'total_population': vuln.total_population if vuln else 100000,
            'vulnerability_score': vuln.vulnerability_score if vuln else 50.0,
            'slum_residents_count': vuln.slum_residents_count if vuln else 20000,
            'elderly_count': vuln.elderly_count if vuln else 12000,
            'children_count': vuln.children_count if vuln else 10000,
            'depot_distance_km': round(abs(loc.latitude - 22.25) * 40.0 + abs(loc.longitude - 84.85) * 40.0 + 2.0, 1)
        })

    optimizer = MunicipalResourceOptimizer(
        fleet_water_tankers=fleet_tankers,
        total_ors_kits=total_ors,
        emergency_beds=emergency_beds
    )
    result = optimizer.optimize_dispatch(wards_payload)
    TELEMETRY['optimizations_total'] += 1

    return jsonify(result), 200


@api_v1_bp.route('/alerts/cap.xml', methods=['GET'])
def api_cap_alerts():
    """
    OASIS Common Alerting Protocol (CAP v1.2) XML Emergency Broadcast Feed.
    Compliant with ITU-T X.1303 specification used by NDMA and national cell telecoms.
    """
    from services.cap_service import generate_cap_xml
    active_alerts = Alert.query.filter_by(status='Active').all()
    alerts_payload = []
    for a in active_alerts:
        loc = a.location
        vuln = loc.vulnerability if loc else None
        alerts_payload.append({
            'location_name': loc.name if loc else 'National Hub',
            'risk_level': a.alert_level,
            'temperature': a.temperature,
            'heat_index': getattr(a, 'heat_index', round(a.temperature + 4.5, 1)),
            'vulnerability_score': vuln.vulnerability_score if vuln else 60.0,
            'latitude': loc.latitude if loc else 22.26,
            'longitude': loc.longitude if loc else 84.85
        })
    xml_output = generate_cap_xml(alerts_payload)
    return Response(xml_output, mimetype='application/xml; charset=utf-8')

@api_v1_bp.route('/simulate/climate', methods=['POST'])
def api_simulate_climate():
    """
    IPCC Climate Crisis & Infrastructure Failure Stress-Testing Solver.
    Simulates global warming departures (+1.0C to +4.0C) with grid blackouts and pipeline failures.
    """
    from services.climate_simulator import run_climate_stress_simulation
    data = request.get_json(force=True, silent=True) or {}
    anomaly = float(data.get('temp_anomaly', 2.0))
    blackout = bool(data.get('grid_blackout', False))
    pipeline = bool(data.get('water_pipeline_rupture', False))

    sim_res = run_climate_stress_simulation(
        temp_anomaly=anomaly,
        grid_blackout=blackout,
        water_pipeline_rupture=pipeline
    )
    return jsonify(sim_res), 200

@api_v1_bp.route('/optimize/vrp-routes', methods=['POST'])
def api_vrp_routes():
    """
    Capacitated Vehicle Routing Problem (CVRP) Turn-by-Turn Fleet Dispatch Scheduler.
    Computes optimal transit paths, ETAs, and fuel savings for emergency water tankers.
    """
    from services.vrp_scheduler import FleetVRPScheduler
    data = request.get_json(force=True, silent=True) or {}
    fleet_tankers = int(data.get('fleet_water_tankers', 20))
    tanker_cap = int(data.get('tanker_capacity_liters', 10000))

    # First optimize allocation
    locations = Location.query.all()
    wards_payload = []
    for loc in locations:
        vuln = loc.vulnerability
        weather = WeatherData.query.filter_by(location_id=loc.id).order_by(WeatherData.date.desc()).first()
        temp = weather.temperature if weather else 38.0
        hi = weather.heat_index if weather else 42.0

        risk_score = min(100.0, max(20.0, (hi * 1.5) + (vuln.vulnerability_score * 0.3 if vuln else 20.0)))
        risk_level = 'EXTREME' if risk_score >= 75 else ('HIGH' if risk_score >= 60 else 'MODERATE')

        wards_payload.append({
            'id': loc.id,
            'name': loc.name,
            'ward_name': loc.name,
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'total_population': vuln.total_population if vuln else 100000,
            'vulnerability_score': vuln.vulnerability_score if vuln else 50.0,
            'slum_residents_count': vuln.slum_residents_count if vuln else 20000,
            'elderly_count': vuln.elderly_count if vuln else 12000,
            'children_count': vuln.children_count if vuln else 10000,
            'depot_distance_km': round(abs(loc.latitude - 22.25) * 40.0 + abs(loc.longitude - 84.85) * 40.0 + 2.0, 1)
        })

    optimizer = MunicipalResourceOptimizer(fleet_water_tankers=fleet_tankers)
    alloc_res = optimizer.optimize_dispatch(wards_payload)

    # Now solve CVRP
    scheduler = FleetVRPScheduler()
    vrp_res = scheduler.generate_fleet_routes(
        allocated_wards=alloc_res['wards_allocation'],
        num_tankers=fleet_tankers,
        tanker_capacity_liters=tanker_cap
    )
    vrp_res['allocation_summary'] = {
        'total_tankers_dispatched': alloc_res['total_tankers_dispatched'],
        'remaining_tankers': alloc_res['remaining_tankers'],
        'system_risk_mitigation_pct': alloc_res['system_risk_mitigation_pct']
    }
    return jsonify(vrp_res), 200

@api_v1_bp.route('/openapi.json', methods=['GET'])
def api_openapi_spec():
    """Serves OpenAPI 3.0 specification."""
    from routes.docs_routes import OPENAPI_SPEC
    return jsonify(OPENAPI_SPEC), 200
