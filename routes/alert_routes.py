from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import db
from database.models import Alert
from services.alert_service import resolve_alert, generate_simulated_dispatch_log
from routes.auth_routes import login_required

alert_bp = Blueprint('alerts', __name__, url_prefix='/alerts')

@alert_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    level_filter = request.args.get('level', 'all')

    query = Alert.query

    if status_filter != 'all':
        query = query.filter(Alert.status == status_filter.capitalize())
    if level_filter != 'all':
        query = query.filter(Alert.alert_level == level_filter.upper())

    alerts = query.order_by(Alert.created_at.desc()).all()

    active_count = Alert.query.filter_by(status='Active').count()
    resolved_count = Alert.query.filter_by(status='Resolved').count()
    extreme_count = Alert.query.filter_by(alert_level='EXTREME').count()

    return render_template(
        'alerts.html',
        alerts=alerts,
        active_count=active_count,
        resolved_count=resolved_count,
        extreme_count=extreme_count,
        status_filter=status_filter,
        level_filter=level_filter
    )

@alert_bp.route('/resolve/<int:id>', methods=['POST'])
@login_required
def resolve(id):
    if resolve_alert(id):
        flash(f'Alert #{id} marked as resolved.', 'success')
    else:
        flash(f'Alert #{id} could not be resolved or was already resolved.', 'warning')
    return redirect(url_for('alerts.index'))

@alert_bp.route('/dispatch-log/<int:id>')
@login_required
def dispatch_log(id):
    alert = Alert.query.get_or_404(id)
    logs = generate_simulated_dispatch_log(alert)
    return jsonify({
        'alert_id': alert.id,
        'location': alert.location.name if alert.location else 'Zone',
        'alert_level': alert.alert_level,
        'temperature': alert.temperature,
        'logs': logs
    })
