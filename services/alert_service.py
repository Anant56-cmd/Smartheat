from datetime import datetime, date
from database.db import db
from database.models import Alert, Location

def check_and_create_alert(location_id, risk_level, temperature, heat_index, risk_score):
    """
    Evaluate conditions and generate an early warning alert if risk is HIGH or EXTREME.
    """
    if risk_level not in ['HIGH', 'EXTREME']:
        return None

    # Check if there is already an active alert for this location today
    today_start = datetime.combine(date.today(), datetime.min.time())
    existing = Alert.query.filter(
        Alert.location_id == location_id,
        Alert.status == 'Active',
        Alert.created_at >= today_start
    ).first()

    if existing:
        return existing

    loc = Location.query.get(location_id)
    loc_name = loc.name if loc else f"Location #{location_id}"

    if risk_level == 'EXTREME':
        reason = (
            f"EXTREME HEAT EMERGENCY in {loc_name}: Temperature reached {temperature}°C with "
            f"calculated Heat Index of {heat_index}°C (Risk Score: {risk_score}/100). "
            f"Imminent hazard of heat stroke, cardiovascular stress, and dehydration."
        )
        recommendation = (
            "1. Activate Red Alert emergency protocol.\n"
            "2. Open 24/7 civic cooling shelters and hydrate vulnerable populations.\n"
            "3. Enforce complete prohibition of outdoor manual labor between 11 AM - 4 PM.\n"
            "4. Dispatch emergency mobile water tankers to high-density settlements."
        )
    else: # HIGH
        reason = (
            f"HIGH HEAT ADVISORY in {loc_name}: Temperature reached {temperature}°C with "
            f"Heat Index of {heat_index}°C (Risk Score: {risk_score}/100). "
            f"Heightened danger of heat exhaustion and cramps among outdoor workers and elderly."
        )
        recommendation = (
            "1. Issue Orange Heat Warning across local media and public sirens.\n"
            "2. Reschedule outdoor construction shifts to early morning/evening.\n"
            "3. Equip primary health centers with heat-stroke observation beds and ORS supplies.\n"
            "4. Ensure drinking water accessibility at transit hubs."
        )

    alert = Alert(
        location_id=location_id,
        alert_level=risk_level,
        temperature=temperature,
        reason=reason,
        recommended_action=recommendation,
        status='Active',
        simulated_dispatched=True,
        created_at=datetime.utcnow()
    )
    db.session.add(alert)
    db.session.commit()
    return alert

def resolve_alert(alert_id):
    """Mark an active alert as resolved."""
    alert = Alert.query.get(alert_id)
    if alert and alert.status == 'Active':
        alert.status = 'Resolved'
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        return True
    return False

def get_active_alerts_count():
    """Count of active alerts currently pending."""
    return Alert.query.filter_by(status='Active').count()

def get_recent_alerts(limit=10, active_only=False):
    """Get latest alerts with location relations."""
    query = Alert.query
    if active_only:
        query = query.filter_by(status='Active')
    return query.order_by(Alert.created_at.desc()).limit(limit).all()

def generate_simulated_dispatch_log(alert):
    """
    Generate realistic simulated broadcast dispatch telemetry logs
    to show in UI without pretending real telecom SMS was sent.
    """
    loc_name = alert.location.name if alert.location else "Monitoring Zone"
    return [
        {
            'channel': 'Municipal Emergency Broadcast Center (CAP-India)',
            'protocol': 'Common Alerting Protocol v1.2',
            'status': 'DISPATCHED_CONFIRMED',
            'timestamp': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'details': f"Broadcast signal sent to civic public address systems and display boards in {loc_name}."
        },
        {
            'channel': 'District Health Office & Emergency Medical Services',
            'protocol': 'Secure HTTPS Webhook / EDIS',
            'status': 'DELIVERED',
            'timestamp': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'details': f"Notified {alert.location.facilities.__len__() if alert.location else 3} emergency response healthcare centers."
        },
        {
            'channel': 'Simulated Public SMS Gateway',
            'protocol': 'SMPP Simulation Service',
            'status': 'SIMULATED_QUEUE_SENT',
            'timestamp': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'details': f"Simulated dispatch queue: 14,820 registered mobile subscribers in {loc_name} cell towers."
        }
    ]
