import csv
import random
from datetime import datetime, timedelta

def generate_weather_dataset(output_path):
    locations = [
        {'name': 'Delhi', 'base_temp': 34.0, 'base_humidity': 42.0, 'coastal': False},
        {'name': 'Ahmedabad', 'base_temp': 35.0, 'base_humidity': 45.0, 'coastal': False},
        {'name': 'Nagpur', 'base_temp': 36.5, 'base_humidity': 38.0, 'coastal': False},
        {'name': 'Hyderabad', 'base_temp': 33.5, 'base_humidity': 52.0, 'coastal': False},
        {'name': 'Kolkata', 'base_temp': 32.0, 'base_humidity': 75.0, 'coastal': True},
        {'name': 'Jaipur', 'base_temp': 35.5, 'base_humidity': 30.0, 'coastal': False},
        {'name': 'Bhubaneswar', 'base_temp': 33.0, 'base_humidity': 72.0, 'coastal': True},
        {'name': 'Chennai', 'base_temp': 32.5, 'base_humidity': 78.0, 'coastal': True},
        {'name': 'Lucknow', 'base_temp': 34.5, 'base_humidity': 48.0, 'coastal': False},
        {'name': 'Patna', 'base_temp': 34.0, 'base_humidity': 55.0, 'coastal': False},
    ]

    start_date = datetime(2025, 4, 1)  # April to June (60 days across 10 cities = 600 records)
    records = []

    random.seed(42)

    for day_offset in range(65):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Summer peak simulation factor (peaks in late May / early June)
        # days 40-55 are peak summer heatwaves
        is_peak_heatwave = 35 <= day_offset <= 55
        is_early_summer = day_offset < 20

        for loc in locations:
            name = loc['name']
            base_t = loc['base_temp']
            base_h = loc['base_humidity']
            
            # Fluctuation
            if is_peak_heatwave:
                temp_delta = random.uniform(4.0, 10.5)
                humid_delta = random.uniform(-10.0, 10.0) if not loc['coastal'] else random.uniform(5.0, 18.0)
                wind = random.uniform(4.0, 15.0)
                rain = 0.0 if random.random() > 0.05 else random.uniform(0.1, 2.0)
                pressure = random.uniform(1001.0, 1008.0)
            elif is_early_summer:
                temp_delta = random.uniform(-5.0, 2.0)
                humid_delta = random.uniform(-8.0, 12.0)
                wind = random.uniform(8.0, 20.0)
                rain = 0.0 if random.random() > 0.15 else random.uniform(0.5, 12.0)
                pressure = random.uniform(1008.0, 1016.0)
            else: # regular summer
                temp_delta = random.uniform(-1.0, 5.0)
                humid_delta = random.uniform(-5.0, 15.0)
                wind = random.uniform(6.0, 18.0)
                rain = 0.0 if random.random() > 0.10 else random.uniform(0.2, 5.0)
                pressure = random.uniform(1005.0, 1012.0)

            temp = round(base_t + temp_delta, 1)
            humidity = round(min(max(base_h + humid_delta, 15.0), 96.0), 1)
            wind_speed = round(wind, 1)
            rainfall = round(rain, 1)
            press = round(pressure, 1)

            records.append({
                'Date': date_str,
                'Location': name,
                'Temperature': temp,
                'Humidity': humidity,
                'Wind_Speed': wind_speed,
                'Rainfall': rainfall,
                'Pressure': press
            })

    # Write out to CSV
    fieldnames = ['Date', 'Location', 'Temperature', 'Humidity', 'Wind_Speed', 'Rainfall', 'Pressure']
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    print(f"Generated {len(records)} realistic weather records in {output_path}")

if __name__ == '__main__':
    import os
    out = os.path.join(os.path.dirname(__file__), 'sample_weather.csv')
    generate_weather_dataset(out)
