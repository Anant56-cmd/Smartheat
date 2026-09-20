import os
import json
from flask import Blueprint, render_template, redirect, url_for, session, jsonify
from sqlalchemy import func
from database.models import Location, WeatherData, Alert, VulnerabilityData, Prediction, RiskAssessment
from routes.auth_routes import login_required
from config import Config

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # 1. Monitored locations count
    total_locations = Location.query.count()

    # 2. Active alerts count
    active_alerts_count = Alert.query.filter_by(status='Active').count()
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()

    # 3. Ingested weather observations count
    total_weather_records = WeatherData.query.count()

    # 4. Average temperature across latest records
    latest_date_sub = db_latest_weather_date()
    if latest_date_sub:
        latest_weather = WeatherData.query.filter_by(date=latest_date_sub).all()
        avg_temp = round(sum(w.temperature for w in latest_weather) / max(len(latest_weather), 1), 1) if latest_weather else 33.5
        max_temp_record = max(latest_weather, key=lambda w: w.temperature) if latest_weather else None
        hottest_city = max_temp_record.location.name if max_temp_record and max_temp_record.location else "N/A"
        hottest_temp = max_temp_record.temperature if max_temp_record else 0.0
    else:
        avg_temp = 34.2
        hottest_city = "Delhi"
        hottest_temp = 43.5

    # 5. Vulnerability summary
    high_vuln_count = VulnerabilityData.query.filter(VulnerabilityData.vulnerability_level.in_(['HIGH', 'EXTREME'])).count()

    # 6. Load ML metrics for model performance widget
    metrics_path = os.path.join(Config.MODEL_DIR, 'model_metrics.json')
    ml_metrics = None
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                ml_metrics = json.load(f)
        except Exception:
            ml_metrics = None

    # 7. Summary of monitored locations with their latest conditions
    locations = Location.query.all()
    location_cards = []
    for loc in locations:
        latest_w = WeatherData.query.filter_by(location_id=loc.id).order_by(WeatherData.date.desc()).first()
        vuln = loc.vulnerability
        temp = latest_w.temperature if latest_w else loc.baseline_temp
        hi = latest_w.heat_index if latest_w else temp + 3.0
        v_score = vuln.vulnerability_score if vuln else 50.0
        
        # Determine quick status
        if hi >= 54.0 or temp >= 45.0:
            status = 'EXTREME'
            badge_class = 'danger'
        elif hi >= 41.0 or temp >= 40.0:
            status = 'HIGH'
            badge_class = 'warning'
        elif hi >= 32.0:
            status = 'MODERATE'
            badge_class = 'info'
        else:
            status = 'LOW'
            badge_class = 'success'

        location_cards.append({
            'id': loc.id,
            'name': loc.name,
            'state': loc.state,
            'temperature': temp,
            'heat_index': hi,
            'vulnerability_score': round(v_score, 1),
            'status': status,
            'badge_class': badge_class
        })

    return render_template(
        'dashboard.html',
        total_locations=total_locations,
        active_alerts_count=active_alerts_count,
        total_weather_records=total_weather_records,
        avg_temp=avg_temp,
        hottest_city=hottest_city,
        hottest_temp=hottest_temp,
        high_vuln_count=high_vuln_count,
        recent_alerts=recent_alerts,
        ml_metrics=ml_metrics,
        locations=location_cards
    )

@dashboard_bp.route('/dashboard/api/chart-data')
@login_required
def chart_data():
    """API providing data for Chart.js charts on the dashboard."""
    # 1. Temperature trends over time (average per date)
    date_trends = (
        WeatherData.query.with_entities(
            WeatherData.date,
            func.avg(WeatherData.temperature).label('avg_temp'),
            func.avg(WeatherData.heat_index).label('avg_hi'),
            func.max(WeatherData.temperature).label('max_temp')
        )
        .group_by(WeatherData.date)
        .order_by(WeatherData.date.asc())
        .limit(30)
        .all()
    )

    trend_labels = [row.date.strftime('%d %b') for row in date_trends]
    trend_temps = [round(row.avg_temp, 1) for row in date_trends]
    trend_his = [round(row.avg_hi if row.avg_hi is not None else row.avg_temp + 2, 1) for row in date_trends]
    trend_max = [round(row.max_temp, 1) for row in date_trends]

    # 2. Heat wave risk level distribution across all recorded data
    all_weather = WeatherData.query.all()
    risk_counts = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'EXTREME': 0}
    for w in all_weather:
        t = w.temperature
        hi = w.heat_index if w.heat_index is not None else t
        if hi >= 54.0 or t >= 45.0:
            risk_counts['EXTREME'] += 1
        elif hi >= 41.0 or t >= 40.0:
            risk_counts['HIGH'] += 1
        elif hi >= 32.0 or t >= 35.0:
            risk_counts['MODERATE'] += 1
        else:
            risk_counts['LOW'] += 1

    # 3. Vulnerability distribution across locations
    vuln_data = VulnerabilityData.query.all()
    vuln_labels = [v.location.name for v in vuln_data]
    vuln_scores = [round(v.vulnerability_score, 1) for v in vuln_data]

    # 4. Feature importance from model
    metrics_path = os.path.join(Config.MODEL_DIR, 'model_metrics.json')
    feature_labels = []
    feature_values = []
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('primary_model', {}).get('feature_importance', [])[:6]:
                    feature_labels.append(item['feature'].replace('_', ' '))
                    feature_values.append(item['importance'])
        except Exception:
            pass

    return jsonify({
        'trends': {
            'labels': trend_labels,
            'avg_temp': trend_temps,
            'avg_hi': trend_his,
            'max_temp': trend_max
        },
        'risk_distribution': {
            'labels': ['Low Risk', 'Moderate Risk', 'High Risk', 'Extreme Risk'],
            'data': [
                risk_counts['LOW'],
                risk_counts['MODERATE'],
                risk_counts['HIGH'],
                risk_counts['EXTREME']
            ]
        },
        'vulnerability': {
            'labels': vuln_labels,
            'scores': vuln_scores
        },
        'feature_importance': {
            'labels': feature_labels,
            'data': feature_values
        }
    })

def db_latest_weather_date():
    latest = WeatherData.query.order_by(WeatherData.date.desc()).first()
    return latest.date if latest else None
