import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from datetime import datetime
from app import create_app
from database.db import db
from database.models import Location, WeatherData, Alert
from ml.preprocessing import calculate_heat_index, determine_risk_label
from services.risk_service import calculate_composite_heat_risk
from services.alert_service import check_and_create_alert

def load_weather_records():
    app = create_app()
    with app.app_context():
        if WeatherData.query.count() > 0:
            print(f"[*] Weather data already populated ({WeatherData.query.count()} records). Skipping.")
            return

        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_weather.csv')
        df = pd.read_csv(csv_path)
        print(f"[*] Ingesting {len(df)} sample weather observations into database...")

        loc_map = {loc.name.lower(): loc for loc in Location.query.all()}
        inserted = 0

        for _, row in df.iterrows():
            loc_name = str(row['Location']).strip()
            loc_obj = loc_map.get(loc_name.lower())
            if not loc_obj:
                continue

            date_val = pd.to_datetime(row['Date']).date()
            temp = float(row['Temperature'])
            humidity = float(row['Humidity'])
            wind = float(row.get('Wind_Speed', 10.0))
            rain = float(row.get('Rainfall', 0.0))
            press = float(row.get('Pressure', 1013.25))
            hi = calculate_heat_index(temp, humidity)

            w = WeatherData(
                location_id=loc_obj.id,
                date=date_val,
                temperature=temp,
                humidity=humidity,
                wind_speed=wind,
                rainfall=rain,
                pressure=press,
                heat_index=hi,
                is_simulated=True
            )
            db.session.add(w)
            inserted += 1

            # For recent dates, trigger realistic alerts if HIGH or EXTREME
            risk_label = determine_risk_label(temp, hi)
            if risk_label in ['HIGH', 'EXTREME']:
                # Calculate composite risk
                vuln = loc_obj.vulnerability
                risk_res = calculate_composite_heat_risk(
                    temperature=temp,
                    humidity=humidity,
                    baseline_temp=loc_obj.baseline_temp,
                    vulnerability_score=vuln.vulnerability_score if vuln else 50.0
                )
                check_and_create_alert(
                    location_id=loc_obj.id,
                    risk_level=risk_label,
                    temperature=temp,
                    heat_index=hi,
                    risk_score=risk_res['total_risk_score']
                )

        db.session.commit()
        print(f"[+] Successfully loaded {inserted} weather records and generated baseline alerts!")

if __name__ == '__main__':
    load_weather_records()
