import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import db
from database.models import Location, Prediction, RiskAssessment
from ml.predictor import predict_single
from ml.train_model import train_and_evaluate
from services.risk_service import calculate_composite_heat_risk
from services.alert_service import check_and_create_alert
from services.recommendation_engine import get_recommendations_for_level
from routes.auth_routes import login_required
from config import Config

ml_bp = Blueprint('ml', __name__, url_prefix='/predictions')

@ml_bp.route('/')
@login_required
def index():
    locations = Location.query.order_by(Location.name.asc()).all()
    recent_predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(15).all()

    # Load evaluated metrics
    metrics_path = os.path.join(Config.MODEL_DIR, 'model_metrics.json')
    ml_metrics = None
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                ml_metrics = json.load(f)
        except Exception:
            ml_metrics = None

    return render_template(
        'predictions.html',
        locations=locations,
        recent_predictions=recent_predictions,
        ml_metrics=ml_metrics
    )

@ml_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        data = request.get_json() if request.is_json else request.form
        location_id = int(data.get('location_id'))
        temperature = float(data.get('temperature'))
        humidity = float(data.get('humidity'))
        wind_speed = float(data.get('wind_speed', 10.0))
        rainfall = float(data.get('rainfall', 0.0))
        pressure = float(data.get('pressure', 1013.25))

        loc = Location.query.get_or_404(location_id)

        # 1. Run Machine Learning inference
        pred_res = predict_single(
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            rainfall=rainfall,
            pressure=pressure
        )

        # 2. Calculate composite multidimensional heat risk score (0-100)
        vuln = loc.vulnerability
        vuln_score = vuln.vulnerability_score if vuln else 50.0
        pop = vuln.total_population if vuln else 1000000
        beds = vuln.hospital_beds if vuln else 5000
        water = vuln.water_kiosks if vuln else 200

        risk_res = calculate_composite_heat_risk(
            temperature=temperature,
            humidity=humidity,
            baseline_temp=loc.baseline_temp,
            vulnerability_score=vuln_score,
            zone_type=loc.zone_type,
            population=pop,
            hospital_beds=beds,
            water_kiosks=water
        )

        # 3. Persist Prediction record
        pred_obj = Prediction(
            location_id=loc.id,
            prediction_date=datetime.utcnow().date(),
            temperature=temperature,
            humidity=humidity,
            heat_index=pred_res['heat_index'],
            predicted_risk=pred_res['predicted_risk'],
            confidence=pred_res['confidence_ratio'],
            model_name='Random Forest Classifier'
        )
        db.session.add(pred_obj)

        # 4. Persist Risk Assessment record
        risk_obj = RiskAssessment(
            location_id=loc.id,
            assessment_date=datetime.utcnow().date(),
            hazard_score=risk_res['hazard_score'],
            vulnerability_score=risk_res['vulnerability_score'],
            exposure_score=risk_res['exposure_score'],
            total_risk_score=risk_res['total_risk_score'],
            risk_level=risk_res['risk_level'],
            score_breakdown_json=risk_res['breakdown_json']
        )
        db.session.add(risk_obj)

        # 5. Trigger early warning alert if HIGH or EXTREME
        alert_created = None
        if pred_res['predicted_risk'] in ['HIGH', 'EXTREME'] or risk_res['risk_level'] in ['HIGH', 'EXTREME']:
            alert_created = check_and_create_alert(
                location_id=loc.id,
                risk_level=pred_res['predicted_risk'],
                temperature=temperature,
                heat_index=pred_res['heat_index'],
                risk_score=risk_res['total_risk_score']
            )

        db.session.commit()

        # Fetch actionable recommendations
        recommendations = get_recommendations_for_level(pred_res['predicted_risk'])

        response_payload = {
            'success': True,
            'location_name': loc.name,
            'prediction': pred_res,
            'risk_assessment': risk_res,
            'alert_triggered': alert_created is not None,
            'recommendations': recommendations
        }

        if request.is_json:
            return jsonify(response_payload)
        else:
            flash(f"Prediction for {loc.name}: {pred_res['predicted_risk']} Risk (Confidence: {pred_res['confidence']}%, Score: {risk_res['total_risk_score']}/100)", 'info')
            return redirect(url_for('ml.index'))

    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f"Inference error: {str(e)}", 'danger')
        return redirect(url_for('ml.index'))

@ml_bp.route('/retrain', methods=['POST'])
@login_required
def retrain():
    try:
        metrics = train_and_evaluate()
        flash(f"ML Pipeline retrained successfully! Primary Random Forest Accuracy: {metrics['primary_model']['accuracy']}%, Comparative Decision Tree Accuracy: {metrics['comparative_model']['accuracy']}%", 'success')
    except Exception as e:
        flash(f"Retraining failed: {str(e)}", 'danger')
    return redirect(url_for('ml.index'))
