from flask import Blueprint, render_template, jsonify
from database.models import Location, WeatherData, CriticalFacility, Alert, VulnerabilityData
from services.risk_service import calculate_composite_heat_risk
from services.recommendation_engine import get_recommendations_for_level
from routes.auth_routes import login_required

map_bp = Blueprint('map', __name__, url_prefix='/map')

@map_bp.route('/')
@login_required
def index():
    return render_template('map.html')

@map_bp.route('/api/data')
@login_required
def get_map_data():
    """
    Provide GIS geospatial coordinates, risk levels, and facility markers for Leaflet.js.
    """
    locations = Location.query.all()
    location_markers = []

    for loc in locations:
        latest_w = WeatherData.query.filter_by(location_id=loc.id).order_by(WeatherData.date.desc()).first()
        vuln = loc.vulnerability

        temp = latest_w.temperature if latest_w else loc.baseline_temp
        hum = latest_w.humidity if latest_w else 50.0
        v_score = vuln.vulnerability_score if vuln else 50.0
        pop = vuln.total_population if vuln else 1000000
        beds = vuln.hospital_beds if vuln else 5000
        water = vuln.water_kiosks if vuln else 200

        risk_res = calculate_composite_heat_risk(
            temperature=temp,
            humidity=hum,
            baseline_temp=loc.baseline_temp,
            vulnerability_score=v_score,
            zone_type=loc.zone_type,
            population=pop,
            hospital_beds=beds,
            water_kiosks=water
        )

        # Check if active alert exists
        active_alert = Alert.query.filter_by(location_id=loc.id, status='Active').first()
        recs = get_recommendations_for_level(risk_res['risk_level'])

        location_markers.append({
            'id': loc.id,
            'name': loc.name,
            'state': loc.state,
            'lat': loc.latitude,
            'lng': loc.longitude,
            'zone_type': loc.zone_type,
            'temperature': temp,
            'humidity': hum,
            'heat_index': risk_res['heat_index'],
            'total_risk_score': risk_res['total_risk_score'],
            'risk_level': risk_res['risk_level'],
            'vulnerability_score': round(v_score, 1),
            'vulnerability_level': vuln.vulnerability_level if vuln else 'MODERATE',
            'has_active_alert': active_alert is not None,
            'active_alert_reason': active_alert.reason if active_alert else None,
            'recommendations': [r['title'] for r in recs[:2]]
        })

    facilities = CriticalFacility.query.all()
    facility_markers = []
    for fac in facilities:
        facility_markers.append({
            'id': fac.id,
            'name': fac.name,
            'facility_type': fac.facility_type,
            'lat': fac.latitude,
            'lng': fac.longitude,
            'capacity': fac.capacity,
            'contact_phone': fac.contact_phone,
            'location_name': fac.location.name if fac.location else 'Monitoring Hub'
        })

    return jsonify({
        'locations': location_markers,
        'facilities': facility_markers
    })
