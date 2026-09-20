import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, Response, request, flash, redirect, url_for
from database.models import WeatherData, Prediction, Alert, VulnerabilityData, ResponseRecommendation, Location
from routes.auth_routes import login_required

report_bp = Blueprint('reports', __name__, url_prefix='/reports')

@report_bp.route('/')
@login_required
def index():
    weather_count = WeatherData.query.count()
    prediction_count = Prediction.query.count()
    alert_count = Alert.query.count()
    vuln_count = VulnerabilityData.query.count()

    return render_template(
        'reports.html',
        weather_count=weather_count,
        prediction_count=prediction_count,
        alert_count=alert_count,
        vuln_count=vuln_count
    )

@report_bp.route('/export/csv/<report_type>')
@login_required
def export_csv(report_type):
    output = io.StringIO()
    writer = csv.writer(output)
    filename = f"smartheat_{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    if report_type == 'weather':
        writer.writerow(['ID', 'Location', 'Date', 'Temperature_C', 'Humidity_Pct', 'Heat_Index_C', 'Wind_Speed_kmh', 'Rainfall_mm', 'Pressure_hPa', 'Simulated'])
        records = WeatherData.query.join(Location).order_by(WeatherData.date.desc()).all()
        for r in records:
            writer.writerow([
                r.id, r.location.name if r.location else '', r.date.strftime('%Y-%m-%d'),
                r.temperature, r.humidity, r.heat_index, r.wind_speed, r.rainfall, r.pressure, r.is_simulated
            ])

    elif report_type == 'predictions':
        writer.writerow(['ID', 'Location', 'Date', 'Temperature_C', 'Humidity_Pct', 'Heat_Index_C', 'Predicted_Risk', 'Confidence_Pct', 'Model_Used', 'Timestamp'])
        records = Prediction.query.join(Location).order_by(Prediction.created_at.desc()).all()
        for p in records:
            writer.writerow([
                p.id, p.location.name if p.location else '', p.prediction_date.strftime('%Y-%m-%d'),
                p.temperature, p.humidity, p.heat_index, p.predicted_risk, round(p.confidence * 100, 1), p.model_name, p.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

    elif report_type == 'alerts':
        writer.writerow(['Alert_ID', 'Location', 'Severity', 'Temperature_C', 'Reason', 'Recommended_Action', 'Status', 'Created_At', 'Resolved_At'])
        records = Alert.query.join(Location).order_by(Alert.created_at.desc()).all()
        for a in records:
            writer.writerow([
                a.id, a.location.name if a.location else '', a.alert_level, a.temperature,
                a.reason.replace('\n', ' '), a.recommended_action.replace('\n', ' '),
                a.status, a.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                a.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if a.resolved_at else 'N/A'
            ])

    elif report_type == 'vulnerability':
        writer.writerow(['Location', 'State', 'Total_Population', 'Elderly_60+', 'Children_<5', 'Outdoor_Workers', 'Slum_Residents', 'Hospital_Beds', 'Water_Kiosks', 'Tree_Canopy_Ratio', 'Vulnerability_Score', 'Vulnerability_Level'])
        records = VulnerabilityData.query.join(Location).all()
        for v in records:
            writer.writerow([
                v.location.name if v.location else '', v.location.state if v.location else '',
                v.total_population, v.elderly_count, v.children_count, v.outdoor_workers_count,
                v.slum_residents_count, v.hospital_beds, v.water_kiosks, v.tree_canopy_ratio,
                round(v.vulnerability_score, 1), v.vulnerability_level
            ])

    elif report_type == 'recommendations':
        writer.writerow(['ID', 'Risk_Level', 'Priority', 'Target_Sector', 'Title', 'Description'])
        records = ResponseRecommendation.query.order_by(ResponseRecommendation.risk_level.asc()).all()
        for rec in records:
            writer.writerow([
                rec.id, rec.risk_level, rec.priority, rec.target_sector, rec.title, rec.description.replace('\n', ' ')
            ])

    else:
        flash('Invalid report type requested.', 'danger')
        return redirect(url_for('reports.index'))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
