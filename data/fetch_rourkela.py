import time
import csv
import json
import urllib.request
import os

url = "https://archive-api.open-meteo.com/v1/archive?latitude=22.2604&longitude=84.8536&start_date=2024-04-01&end_date=2024-06-30&daily=temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max,precipitation_sum,surface_pressure_mean&timezone=Asia/Kolkata"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

req = urllib.request.Request(url, headers=headers)

for attempt in range(5):
    try:
        print(f"[*] Querying Rourkela archive (attempt {attempt+1})...")
        time.sleep(2)
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode('utf-8'))
            daily = data['daily']
            times = daily['time']
            temps = daily['temperature_2m_max']
            humids = daily['relative_humidity_2m_mean']
            winds = daily['wind_speed_10m_max']
            rains = daily['precipitation_sum']
            pressures = daily['surface_pressure_mean']

            rows = []
            for i in range(len(times)):
                rows.append({
                    'Date': times[i],
                    'Location': 'Rourkela',
                    'Temperature': round(float(temps[i]), 1),
                    'Humidity': round(float(humids[i]), 1),
                    'Wind_Speed': round(float(winds[i]), 1) if winds[i] is not None else 10.0,
                    'Rainfall': round(float(rains[i]), 1) if rains[i] is not None else 0.0,
                    'Pressure': round(float(pressures[i]), 1) if pressures[i] is not None else 1013.25
                })

            csv_path = os.path.join(os.path.dirname(__file__), 'real_weather_history.csv')
            existing = list(csv.DictReader(open(csv_path, encoding='utf-8')))
            existing = [r for r in existing if r['Location'] != 'Rourkela'] + rows

            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Date', 'Location', 'Temperature', 'Humidity', 'Wind_Speed', 'Rainfall', 'Pressure'])
                writer.writeheader()
                writer.writerows(existing)

            print(f"[+] Successfully fetched {len(rows)} real records for Rourkela!")
            print(f"[+] Total records in real_weather_history.csv: {len(existing)}")
            break
    except Exception as e:
        print(f"[-] Attempt {attempt+1} failed: {e}")
        time.sleep(4)
