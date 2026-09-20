import os
from datetime import datetime
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename

from database.db import db
from database.models import WeatherData, Location
from ml.preprocessing import clean_and_validate_dataset, calculate_heat_index, determine_risk_label
from services.alert_service import check_and_create_alert
from services.risk_service import calculate_composite_heat_risk
from routes.auth_routes import login_required

weather_bp = Blueprint('weather', __name__, url_prefix='/weather')

@weather_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    location_id = request.args.get('location_id', type=int)
    
    query = WeatherData.query.join(Location)
    if location_id:
        query = query.filter(WeatherData.location_id == location_id)
        
    pagination = query.order_by(WeatherData.date.desc(), WeatherData.id.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    locations = Location.query.order_by(Location.name.asc()).all()
    
    return render_template(
        'weather.html',
        records=pagination.items,
        pagination=pagination,
        locations=locations,
        selected_location_id=location_id
    )

@weather_bp.route('/upload', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('weather.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('weather.index'))

    if not file.filename.lower().endswith('.csv'):
        flash('Invalid file format. Please upload a standard CSV file.', 'danger')
        return redirect(url_for('weather.index'))

    try:
        # Read uploaded CSV
        df = pd.read_csv(file.stream)
        cleaned_df, dupes = clean_and_validate_dataset(df)

        if 'Temperature' not in cleaned_df.columns or 'Humidity' not in cleaned_df.columns:
            flash("Dataset must contain at least 'Temperature' and 'Humidity' columns.", 'danger')
            return redirect(url_for('weather.index'))

        # Cache existing locations
        existing_locs = {loc.name.lower(): loc for loc in Location.query.all()}
        default_loc = Location.query.first()

        inserted_count = 0
        alerts_triggered = 0

        for _, row in cleaned_df.iterrows():
            loc_name = str(row.get('Location', 'Default Zone')).strip()
            loc_obj = existing_locs.get(loc_name.lower())
            
            # Create location on the fly if new
            if not loc_obj:
                loc_obj = Location(
                    name=loc_name,
                    state='Monitored State',
                    latitude=20.5937,
                    longitude=78.9629,
                    zone_type='Urban',
                    baseline_temp=33.0
                )
                db.session.add(loc_obj)
                db.session.flush()
                existing_locs[loc_name.lower()] = loc_obj

            # Parse date
            raw_date = row.get('Date')
            if pd.notna(raw_date):
                try:
                    date_val = pd.to_datetime(raw_date).date()
                except Exception:
                    date_val = datetime.utcnow().date()
            else:
                date_val = datetime.utcnow().date()

            temp = float(row['Temperature'])
            humidity = float(row['Humidity'])
            wind = float(row.get('Wind_Speed', 10.0)) if pd.notna(row.get('Wind_Speed')) else 10.0
            rain = float(row.get('Rainfall', 0.0)) if pd.notna(row.get('Rainfall')) else 0.0
            press = float(row.get('Pressure', 1013.25)) if pd.notna(row.get('Pressure')) else 1013.25
            
            hi = calculate_heat_index(temp, humidity)

            weather_record = WeatherData(
                location_id=loc_obj.id,
                date=date_val,
                temperature=temp,
                humidity=humidity,
                wind_speed=wind,
                rainfall=rain,
                pressure=press,
                heat_index=hi,
                is_simulated=False
            )
            db.session.add(weather_record)
            inserted_count += 1

            # Check if condition triggers early warning
            risk_cat = determine_risk_label(temp, hi)
            if risk_cat in ['HIGH', 'EXTREME']:
                risk_res = calculate_composite_heat_risk(
                    temp, humidity, baseline_temp=loc_obj.baseline_temp
                )
                alert = check_and_create_alert(
                    location_id=loc_obj.id,
                    risk_level=risk_cat,
                    temperature=temp,
                    heat_index=hi,
                    risk_score=risk_res['total_risk_score']
                )
                if alert:
                    alerts_triggered += 1

        db.session.commit()
        msg = f"Successfully uploaded and validated {inserted_count} weather observations ({dupes} duplicates discarded)."
        if alerts_triggered > 0:
            msg += f" {alerts_triggered} high/extreme risk early warnings were automatically generated."
        flash(msg, 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"Error processing CSV file: {str(e)}", 'danger')

    return redirect(url_for('weather.index'))

@weather_bp.route('/manual-entry', methods=['POST'])
@login_required
def manual_entry():
    try:
        location_id = request.form.get('location_id', type=int)
        raw_date = request.form.get('date')
        temp = request.form.get('temperature', type=float)
        humidity = request.form.get('humidity', type=float)
        wind = request.form.get('wind_speed', 10.0, type=float)
        rainfall = request.form.get('rainfall', 0.0, type=float)
        pressure = request.form.get('pressure', 1013.25, type=float)

        loc = Location.query.get_or_404(location_id)
        date_val = datetime.strptime(raw_date, '%Y-%m-%d').date() if raw_date else datetime.utcnow().date()
        hi = calculate_heat_index(temp, humidity)

        record = WeatherData(
            location_id=loc.id,
            date=date_val,
            temperature=temp,
            humidity=humidity,
            wind_speed=wind,
            rainfall=rainfall,
            pressure=pressure,
            heat_index=hi,
            is_simulated=False
        )
        db.session.add(record)

        # Early warning check
        risk_cat = determine_risk_label(temp, hi)
        if risk_cat in ['HIGH', 'EXTREME']:
            risk_res = calculate_composite_heat_risk(temp, humidity, baseline_temp=loc.baseline_temp)
            check_and_create_alert(loc.id, risk_cat, temp, hi, risk_res['total_risk_score'])

        db.session.commit()
        flash(f'New weather record for {loc.name} on {date_val} successfully recorded!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to add record: {str(e)}', 'danger')

    return redirect(url_for('weather.index'))

@weather_bp.route('/sync-realtime')
@login_required
def sync_realtime_action():
    """Trigger live synchronization across all monitoring stations from Open-Meteo."""
    from services.realtime_weather_service import sync_all_stations_realtime
    try:
        res = sync_all_stations_realtime()
        msg = f"Live synchronization complete! Updated {res['total_stations']} stations in real-time from Open-Meteo WMO service."
        if res['alerts_triggered'] > 0:
            msg += f" {res['alerts_triggered']} new live early warnings triggered."
        flash(msg, 'success')
    except Exception as e:
        flash(f"Live synchronization warning: {str(e)}", 'warning')
    
    # Return to referrer or weather index
    referrer = request.referrer
    return redirect(referrer or url_for('weather.index'))

@weather_bp.route('/api/sync-realtime', methods=['POST'])
@login_required
def api_sync_realtime():
    """API endpoint to trigger real-time synchronization via AJAX."""
    from services.realtime_weather_service import sync_all_stations_realtime
    try:
        res = sync_all_stations_realtime()
        return jsonify({'success': True, 'data': res})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@weather_bp.route('/api/live-station/<int:location_id>')
@login_required
def api_live_station(location_id):
    """Fetch live meteorological reading for a single monitoring station."""
    from services.realtime_weather_service import fetch_live_weather
    loc = Location.query.get_or_404(location_id)
    try:
        live = fetch_live_weather(loc.latitude, loc.longitude)
        live['location_name'] = loc.name
        live['location_id'] = loc.id
        return jsonify({'success': True, 'data': live})
    except Exception as e:
        # Fallback to latest database observation
        latest = WeatherData.query.filter_by(location_id=loc.id).order_by(WeatherData.date.desc()).first()
        if latest:
            return jsonify({
                'success': True,
                'data': {
                    'location_name': loc.name,
                    'location_id': loc.id,
                    'temperature': latest.temperature,
                    'humidity': latest.humidity,
                    'wind_speed': latest.wind_speed,
                    'rainfall': latest.rainfall,
                    'pressure': latest.pressure,
                    'heat_index': latest.heat_index,
                    'source': 'Cached Database Record (Fallback)'
                }
            })
        return jsonify({'success': False, 'error': str(e)}), 500

@weather_bp.route('/api/search-city')
@login_required
def api_search_city():
    """Geocoding search endpoint to look up any city or town globally."""
    from services.realtime_weather_service import search_cities_online
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []})
    results = search_cities_online(q)
    return jsonify({'results': results})

@weather_bp.route('/api/add-city', methods=['POST'])
@login_required
def api_add_city():
    """Add a dynamically searched city to database and pull its real-time weather."""
    from services.realtime_weather_service import add_and_sync_city
    data = request.get_json(silent=True) or request.form
    name = data.get('name')
    state = data.get('state', '')
    lat = data.get('latitude')
    lng = data.get('longitude')

    if not name or lat is None or lng is None:
        return jsonify({'success': False, 'error': 'Missing required coordinates or city name.'}), 400

    try:
        res = add_and_sync_city(name, state, lat, lng)
        return jsonify({'success': True, 'data': res})
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



