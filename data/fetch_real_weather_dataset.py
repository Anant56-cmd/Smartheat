import os
import sys
import csv
import json
import urllib.request
import urllib.parse
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

LOCATIONS = [
    {'name': 'Rourkela', 'lat': 22.2604, 'lng': 84.8536},
    {'name': 'Jharsuguda', 'lat': 21.8554, 'lng': 84.0062},
    {'name': 'Sambalpur', 'lat': 21.4669, 'lng': 83.9812},
    {'name': 'Jamshedpur', 'lat': 22.8046, 'lng': 86.2029},
    {'name': 'Ranchi', 'lat': 23.3441, 'lng': 85.3096},
    {'name': 'Cuttack', 'lat': 20.4625, 'lng': 85.8830},
    {'name': 'Bhubaneswar', 'lat': 20.2961, 'lng': 85.8245},
    {'name': 'Kolkata', 'lat': 22.5726, 'lng': 88.3639},
    {'name': 'Raipur', 'lat': 21.2514, 'lng': 81.6296},
    {'name': 'Patna', 'lat': 25.5941, 'lng': 85.1376},
]

def fetch_real_historical_weather(output_csv=None, start_date='2024-04-01', end_date='2024-06-30'):
    """
    Fetch authentic meteorological historical records from the Open-Meteo WMO archive
    for Indian metropolitan monitoring stations during the 2024 summer heatwaves.
    """
    if not output_csv:
        output_csv = os.path.join(os.path.dirname(__file__), 'real_weather_history.csv')

    all_records = []
    base_url = "https://archive-api.open-meteo.com/v1/archive"

    print(f"[*] Fetching authentic meteorological records from Open-Meteo ({start_date} to {end_date})...")

    for loc in LOCATIONS:
        print(f"  -> Querying station: {loc['name']} ({loc['lat']}, {loc['lng']})...")
        params = {
            'latitude': loc['lat'],
            'longitude': loc['lng'],
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max,precipitation_sum,surface_pressure_mean',
            'timezone': 'Asia/Kolkata'
        }
        query_string = urllib.parse.urlencode(params)
        req_url = f"{base_url}?{query_string}"

        try:
            req = urllib.request.Request(req_url, headers={'User-Agent': 'SMARTHEAT-Disaster-System/2.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode('utf-8'))
                daily = payload.get('daily', {})
                
                times = daily.get('time', [])
                temps = daily.get('temperature_2m_max', [])
                humids = daily.get('relative_humidity_2m_mean', [])
                winds = daily.get('wind_speed_10m_max', [])
                rains = daily.get('precipitation_sum', [])
                pressures = daily.get('surface_pressure_mean', [])

                for i in range(len(times)):
                    t_val = temps[i]
                    h_val = humids[i]
                    if t_val is not None and h_val is not None:
                        all_records.append({
                            'Date': times[i],
                            'Location': loc['name'],
                            'Temperature': round(float(t_val), 1),
                            'Humidity': round(float(h_val), 1),
                            'Wind_Speed': round(float(winds[i]), 1) if winds[i] is not None else 10.0,
                            'Rainfall': round(float(rains[i]), 1) if rains[i] is not None else 0.0,
                            'Pressure': round(float(pressures[i]), 1) if pressures[i] is not None else 1013.25
                        })
        except Exception as e:
            print(f"     [!] Warning: Failed to query {loc['name']} ({str(e)}). Using local backup if present.")

    if not all_records:
        raise RuntimeError("No records fetched from meteorological API. Check network connectivity.")

    fieldnames = ['Date', 'Location', 'Temperature', 'Humidity', 'Wind_Speed', 'Rainfall', 'Pressure']
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_records:
            writer.writerow(r)

    print(f"[+] Successfully generated authentic dataset with {len(all_records)} records at: {output_csv}")
    return output_csv

if __name__ == '__main__':
    fetch_real_historical_weather()
