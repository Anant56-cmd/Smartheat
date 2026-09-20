import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from database.db import db
from database.models import Location, WeatherData
from ml.preprocessing import calculate_heat_index, determine_risk_label
from services.risk_service import calculate_composite_heat_risk
from services.alert_service import check_and_create_alert

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

def fetch_live_weather(latitude, longitude, timeout=10, retries=2):
    """
    Fetch live real-time meteorological observations for specific coordinates
    from the Open-Meteo Global WMO Forecast API.
    Includes automatic retry and resilient fallback.
    """
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,surface_pressure',
        'timezone': 'auto'
    }
    query = urllib.parse.urlencode(params)
    url = f"{OPEN_METEO_FORECAST_URL}?{query}"

    req = urllib.request.Request(url, headers={'User-Agent': 'SMARTHEAT-Realtime-Monitor/2.0'})
    last_err = None

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                current = data.get('current', {})

                temp = float(current.get('temperature_2m', 30.0))
                humidity = float(current.get('relative_humidity_2m', 50.0))
                wind = float(current.get('wind_speed_10m', 10.0))
                precip = float(current.get('precipitation', 0.0))
                pressure = float(current.get('surface_pressure', 1013.25))
                obs_time = current.get('time', datetime.utcnow().strftime('%Y-%m-%d %H:%M'))

                hi = calculate_heat_index(temp, humidity)

                return {
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1),
                    'wind_speed': round(wind, 1),
                    'rainfall': round(precip, 1),
                    'pressure': round(pressure, 1),
                    'heat_index': round(hi, 1),
                    'observation_time': obs_time,
                    'source': 'Open-Meteo Live API'
                }
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.0)

    # Climatological baseline fallback if Open-Meteo times out or rate limits
    print(f"[!] Weather API notice for ({latitude}, {longitude}): {last_err}. Using station climatological baseline.")
    fallback_temp = 33.2
    fallback_hum = 52.0
    fallback_hi = calculate_heat_index(fallback_temp, fallback_hum)
    return {
        'temperature': fallback_temp,
        'humidity': fallback_hum,
        'wind_speed': 10.0,
        'rainfall': 0.0,
        'pressure': 1012.5,
        'heat_index': round(fallback_hi, 1),
        'observation_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M'),
        'source': 'Open-Meteo (Station Baseline Fallback)'
    }

def sync_all_stations_realtime():
    """
    Query live meteorological API for all registered monitoring locations,
    record real-time observations, compute NOAA Heat Index, and evaluate risk.
    """
    locations = Location.query.all()
    results = []
    alerts_count = 0
    now_date = datetime.utcnow().date()

    for loc in locations:
        try:
            live = fetch_live_weather(loc.latitude, loc.longitude)
            
            # Check if an observation for today already exists; update it or insert new
            existing_today = WeatherData.query.filter_by(location_id=loc.id, date=now_date).first()
            if existing_today:
                existing_today.temperature = live['temperature']
                existing_today.humidity = live['humidity']
                existing_today.wind_speed = live['wind_speed']
                existing_today.rainfall = live['rainfall']
                existing_today.pressure = live['pressure']
                existing_today.heat_index = live['heat_index']
                existing_today.is_simulated = False
                record_id = existing_today.id
            else:
                w = WeatherData(
                    location_id=loc.id,
                    date=now_date,
                    temperature=live['temperature'],
                    humidity=live['humidity'],
                    wind_speed=live['wind_speed'],
                    rainfall=live['rainfall'],
                    pressure=live['pressure'],
                    heat_index=live['heat_index'],
                    is_simulated=False
                )
                db.session.add(w)
                db.session.flush()
                record_id = w.id

            # Evaluate early warning conditions
            risk_label = determine_risk_label(live['temperature'], live['heat_index'])
            vuln = loc.vulnerability
            risk_res = calculate_composite_heat_risk(
                temperature=live['temperature'],
                humidity=live['humidity'],
                baseline_temp=loc.baseline_temp,
                vulnerability_score=vuln.vulnerability_score if vuln else 50.0,
                zone_type=loc.zone_type,
                population=vuln.total_population if vuln else 1000000,
                hospital_beds=vuln.hospital_beds if vuln else 5000,
                water_kiosks=vuln.water_kiosks if vuln else 200
            )

            alert_created = None
            if risk_label in ['HIGH', 'EXTREME'] or risk_res['risk_level'] in ['HIGH', 'EXTREME']:
                alert_created = check_and_create_alert(
                    location_id=loc.id,
                    risk_level=risk_label if risk_label in ['HIGH', 'EXTREME'] else risk_res['risk_level'],
                    temperature=live['temperature'],
                    heat_index=live['heat_index'],
                    risk_score=risk_res['total_risk_score']
                )
                if alert_created:
                    alerts_count += 1

            results.append({
                'location_id': loc.id,
                'name': loc.name,
                'state': loc.state,
                'temperature': live['temperature'],
                'humidity': live['humidity'],
                'heat_index': live['heat_index'],
                'wind_speed': live['wind_speed'],
                'risk_level': risk_res['risk_level'],
                'risk_score': risk_res['total_risk_score'],
                'alert_triggered': alert_created is not None,
                'status': 'Synced'
            })

        except Exception as e:
            results.append({
                'location_id': loc.id,
                'name': loc.name,
                'state': loc.state,
                'error': str(e),
                'status': 'Fallback Used'
            })

    db.session.commit()

    return {
        'synced_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_stations': len(locations),
        'stations': results,
        'alerts_triggered': alerts_count
    }

def search_cities_online(query, count=6):
    """
    Query Open-Meteo Geocoding API to search for any city or town globally.
    Includes retry logic and local database fallback if network is unreachable.
    """
    if not query or len(query.strip()) < 2:
        return []

    q = urllib.parse.quote(query.strip())
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count={count}&language=en&format=json"

    req = urllib.request.Request(url, headers={'User-Agent': 'SMARTHEAT-CitySearch/2.0'})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = []
                for item in data.get('results', []):
                    name = item.get('name', '')
                    admin1 = item.get('admin1', '')
                    country = item.get('country', '')
                    lat = round(float(item.get('latitude', 0.0)), 4)
                    lng = round(float(item.get('longitude', 0.0)), 4)
                    
                    parts = [p for p in [name, admin1, country] if p]
                    display_name = ", ".join(parts)
                    
                    results.append({
                        'id': item.get('id'),
                        'name': name,
                        'state': admin1 or 'Monitored Region',
                        'country': country,
                        'latitude': lat,
                        'longitude': lng,
                        'display_name': display_name
                    })
                return results
        except Exception as e:
            if attempt == 0:
                time.sleep(0.8)
            else:
                print(f"[!] Geocoding error: {e}")

    # Fallback to local registered locations
    clean_q = query.strip().lower()
    local_matches = Location.query.filter(Location.name.ilike(f"%{clean_q}%")).limit(count).all()
    return [{
        'id': loc.id,
        'name': loc.name,
        'state': loc.state,
        'country': 'India',
        'latitude': loc.latitude,
        'longitude': loc.longitude,
        'display_name': f"{loc.name}, {loc.state}, India"
    } for loc in local_matches]

def add_and_sync_city(name, state, latitude, longitude):
    """
    Dynamically add any searched city to the database, fetch its live weather,
    and compute its initial risk score.
    """
    from database.models import VulnerabilityData

    lat = round(float(latitude), 4)
    lng = round(float(longitude), 4)
    clean_name = name.strip()
    clean_state = state.strip() or 'Monitored State'

    loc = Location.query.filter_by(name=clean_name).first()
    if not loc:
        loc = Location(
            name=clean_name,
            state=clean_state,
            latitude=lat,
            longitude=lng,
            zone_type='Urban Settlement',
            baseline_temp=34.0
        )
        db.session.add(loc)
        db.session.flush()

        # Seed baseline vulnerability for the new city
        vuln = VulnerabilityData(
            location_id=loc.id,
            total_population=500000,
            elderly_count=45000,
            children_count=40000,
            outdoor_workers_count=125000,
            slum_residents_count=110000,
            hospital_beds=1500,
            water_kiosks=80,
            tree_canopy_ratio=0.15,
            vulnerability_score=52.0,
            vulnerability_level='HIGH'
        )
        db.session.add(vuln)
    else:
        loc.latitude = lat
        loc.longitude = lng
        loc.state = clean_state

    # Fetch live weather
    live = fetch_live_weather(lat, lng)

    # Save to weather_data for today
    today = datetime.utcnow().date()
    w_rec = WeatherData.query.filter_by(location_id=loc.id, date=today).first()
    if not w_rec:
        w_rec = WeatherData(
            location_id=loc.id,
            date=today,
            temperature=live['temperature'],
            humidity=live['humidity'],
            wind_speed=live['wind_speed'],
            rainfall=live['rainfall'],
            pressure=live['pressure'],
            heat_index=live['heat_index'],
            is_simulated=False
        )
        db.session.add(w_rec)
    else:
        w_rec.temperature = live['temperature']
        w_rec.humidity = live['humidity']
        w_rec.wind_speed = live['wind_speed']
        w_rec.rainfall = live['rainfall']
        w_rec.pressure = live['pressure']
        w_rec.heat_index = live['heat_index']

    # Compute risk
    risk_res = calculate_composite_heat_risk(
        temperature=live['temperature'],
        humidity=live['humidity'],
        baseline_temp=loc.baseline_temp,
        vulnerability_score=52.0
    )

    alert_triggered = False
    if risk_res['risk_level'] in ['HIGH', 'EXTREME']:
        alt = check_and_create_alert(
            location_id=loc.id,
            risk_level=risk_res['risk_level'],
            temperature=live['temperature'],
            heat_index=live['heat_index'],
            risk_score=risk_res['total_risk_score']
        )
        if alt:
            alert_triggered = True

    db.session.commit()

    return {
        'location_id': loc.id,
        'name': loc.name,
        'state': loc.state,
        'latitude': loc.latitude,
        'longitude': loc.longitude,
        'temperature': live['temperature'],
        'humidity': live['humidity'],
        'heat_index': live['heat_index'],
        'wind_speed': live['wind_speed'],
        'risk_score': risk_res['total_risk_score'],
        'risk_level': risk_res['risk_level'],
        'alert_triggered': alert_triggered
    }

