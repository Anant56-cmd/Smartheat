import csv
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timezone, timedelta
from database.db import db
from database.models import (
    User, Location, CriticalFacility, ResponseRecommendation, VulnerabilityData,
    WeatherData, Prediction, Alert, RiskAssessment
)
from ml.preprocessing import calculate_heat_index

def seed_database(app):
    """
    Seed Pan-India National Network covering 24 major cities across all 6 climatic zones:
    - East Zone & Flagship Industrial Belt (Rourkela, Bhubaneswar, Cuttack, Jharsuguda, Sambalpur, Jamshedpur, Ranchi, Kolkata, Patna)
    - North Zone & Gangetic Plain (New Delhi, Lucknow, Varanasi, Chandigarh)
    - Northwest & Arid Desert Zone (Jaipur, Jodhpur, Ahmedabad, Nagpur)
    - West & Central (Mumbai, Pune, Bhopal, Raipur)
    - South Zone (Hyderabad, Chennai, Bengaluru)
    """
    with app.app_context():
        db.create_all()
        
        # 1. Seed Admin User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@smartheat.gov.in',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print(" -> Created default admin user: admin / admin123")
            
        # 2. Pan-India Locations (24 Major Metropolises & Heatwave Hotspots)
        locations_data = [
            # --- EAST ZONE (Flagship Ground Zero & Industrial Belt) ---
            {'name': 'Rourkela', 'state': 'Odisha', 'latitude': 22.2604, 'longitude': 84.8536, 'zone_type': 'Industrial Metropolis', 'baseline_temp': 35.0},
            {'name': 'Jharsuguda', 'state': 'Odisha', 'latitude': 21.8554, 'longitude': 84.0062, 'zone_type': 'Industrial Valley', 'baseline_temp': 36.0},
            {'name': 'Sambalpur', 'state': 'Odisha', 'latitude': 21.4669, 'longitude': 83.9812, 'zone_type': 'Urban River Basin', 'baseline_temp': 36.0},
            {'name': 'Bhubaneswar', 'state': 'Odisha', 'latitude': 20.2961, 'longitude': 85.8245, 'zone_type': 'State Capital / Coastal Urban', 'baseline_temp': 34.0},
            {'name': 'Cuttack', 'state': 'Odisha', 'latitude': 20.4625, 'longitude': 85.8830, 'zone_type': 'Coastal Delta Plain', 'baseline_temp': 34.0},
            {'name': 'Jamshedpur', 'state': 'Jharkhand', 'latitude': 22.8046, 'longitude': 86.2029, 'zone_type': 'Industrial Metropolis', 'baseline_temp': 35.5},
            {'name': 'Ranchi', 'state': 'Jharkhand', 'latitude': 23.3441, 'longitude': 85.3096, 'zone_type': 'Plateau Capital', 'baseline_temp': 33.0},
            {'name': 'Kolkata', 'state': 'West Bengal', 'latitude': 22.5726, 'longitude': 88.3639, 'zone_type': 'Megacity / Coastal Plain', 'baseline_temp': 33.5},
            {'name': 'Patna', 'state': 'Bihar', 'latitude': 25.5941, 'longitude': 85.1376, 'zone_type': 'Gangetic Plain Capital', 'baseline_temp': 35.0},

            # --- NORTH ZONE (National Capital & Gangetic Plain) ---
            {'name': 'New Delhi', 'state': 'Delhi NCT', 'latitude': 28.6139, 'longitude': 77.2090, 'zone_type': 'National Capital Megacity', 'baseline_temp': 37.0},
            {'name': 'Lucknow', 'state': 'Uttar Pradesh', 'latitude': 26.8467, 'longitude': 80.9462, 'zone_type': 'Gangetic Plain Capital', 'baseline_temp': 36.5},
            {'name': 'Varanasi', 'state': 'Uttar Pradesh', 'latitude': 25.3176, 'longitude': 82.9739, 'zone_type': 'Urban River Basin', 'baseline_temp': 36.8},
            {'name': 'Chandigarh', 'state': 'Chandigarh UT', 'latitude': 30.7333, 'longitude': 76.7794, 'zone_type': 'Sub-Himalayan Urban', 'baseline_temp': 35.5},

            # --- NORTHWEST & ARID ZONE (Desert & Extreme Heat Traps) ---
            {'name': 'Jaipur', 'state': 'Rajasthan', 'latitude': 26.9124, 'longitude': 75.7873, 'zone_type': 'Semi-Arid State Capital', 'baseline_temp': 38.0},
            {'name': 'Jodhpur', 'state': 'Rajasthan', 'latitude': 26.2389, 'longitude': 73.0243, 'zone_type': 'Arid Desert Metropolis', 'baseline_temp': 39.5},
            {'name': 'Ahmedabad', 'state': 'Gujarat', 'latitude': 23.0225, 'longitude': 72.5714, 'zone_type': 'Semi-Arid Megacity', 'baseline_temp': 38.5},
            {'name': 'Nagpur', 'state': 'Maharashtra', 'latitude': 21.1458, 'longitude': 79.0882, 'zone_type': 'Vidarbha Continental Plateau', 'baseline_temp': 39.0},

            # --- WEST & CENTRAL ZONE ---
            {'name': 'Mumbai', 'state': 'Maharashtra', 'latitude': 19.0760, 'longitude': 72.8777, 'zone_type': 'Coastal Megacity / High Humidity', 'baseline_temp': 33.5},
            {'name': 'Pune', 'state': 'Maharashtra', 'latitude': 18.5204, 'longitude': 73.8567, 'zone_type': 'Deccan Plateau Urban', 'baseline_temp': 34.5},
            {'name': 'Bhopal', 'state': 'Madhya Pradesh', 'latitude': 23.2599, 'longitude': 77.4126, 'zone_type': 'Central Plateau Capital', 'baseline_temp': 37.0},
            {'name': 'Raipur', 'state': 'Chhattisgarh', 'latitude': 21.2514, 'longitude': 81.6296, 'zone_type': 'Central Plain Capital', 'baseline_temp': 36.5},

            # --- SOUTH ZONE (Peninsular Metros) ---
            {'name': 'Hyderabad', 'state': 'Telangana', 'latitude': 17.3850, 'longitude': 78.4867, 'zone_type': 'Deccan Plateau Metropolis', 'baseline_temp': 36.0},
            {'name': 'Chennai', 'state': 'Tamil Nadu', 'latitude': 13.0827, 'longitude': 80.2707, 'zone_type': 'Coastal Megacity / High Humidity', 'baseline_temp': 34.5},
            {'name': 'Bengaluru', 'state': 'Karnataka', 'latitude': 12.9716, 'longitude': 77.5946, 'zone_type': 'Southern Plateau Urban', 'baseline_temp': 31.0},
        ]
        
        loc_map = {}
        for loc in locations_data:
            existing = Location.query.filter_by(name=loc['name']).first()
            if not existing:
                existing = Location(**loc)
                db.session.add(existing)
                db.session.flush()
                print(f" -> Added Pan-India location: {loc['name']} ({loc['state']})")
            else:
                existing.latitude = loc['latitude']
                existing.longitude = loc['longitude']
                existing.state = loc['state']
                existing.zone_type = loc['zone_type']
                existing.baseline_temp = loc['baseline_temp']
            loc_map[loc['name']] = existing

        # 3. Seed Critical Facilities (Premier National Hospitals, Cooling Shelters, Water Points)
        facilities_data = [
            # Rourkela (Ground Zero Flagship Hub)
            {'location': 'Rourkela', 'name': 'Ispat General Hospital (IGH) Emergency Heat Wing', 'type': 'Hospital', 'lat': 22.2540, 'lng': 84.8620, 'cap': 350, 'phone': '+91-661-2448888'},
            {'location': 'Rourkela', 'name': 'Rourkela Government Hospital (RGH)', 'type': 'Hospital', 'lat': 22.2380, 'lng': 84.8450, 'cap': 200, 'phone': '+91-661-2500100'},
            {'location': 'Rourkela', 'name': 'Sector-19 Shaded Civic Cooling Pavilion', 'type': 'Cooling Center', 'lat': 22.2580, 'lng': 84.8720, 'cap': 450, 'phone': '+91-661-2641234'},
            {'location': 'Rourkela', 'name': 'Panposh High-Capacity Water Tanker Post', 'type': 'Water Point', 'lat': 22.2450, 'lng': 84.8210, 'cap': 1200, 'phone': '+91-661-2400999'},
            
            # New Delhi
            {'location': 'New Delhi', 'name': 'AIIMS New Delhi National Heat Trauma Center', 'type': 'Hospital', 'lat': 28.5672, 'lng': 77.2100, 'cap': 600, 'phone': '+91-11-26588500'},
            {'location': 'New Delhi', 'name': 'Safdarjung Hospital Emergency Heat Stroke Ward', 'type': 'Hospital', 'lat': 28.5700, 'lng': 77.2070, 'cap': 450, 'phone': '+91-11-26165060'},
            {'location': 'New Delhi', 'name': 'Connaught Place Civic Air-Cooled Relief Hub', 'type': 'Cooling Center', 'lat': 28.6315, 'lng': 77.2167, 'cap': 700, 'phone': '+91-11-23360000'},
            {'location': 'New Delhi', 'name': 'ISBT Kashmere Gate Municipal Water Tanker Station', 'type': 'Water Point', 'lat': 28.6665, 'lng': 77.2285, 'cap': 2500, 'phone': '+91-11-23860000'},

            # Jaipur
            {'location': 'Jaipur', 'name': 'SMS Hospital & Medical College Heat Critical Care', 'type': 'Hospital', 'lat': 26.8910, 'lng': 75.8160, 'cap': 480, 'phone': '+91-141-2560291'},
            {'location': 'Jaipur', 'name': 'Sindhi Camp Shaded Transit Cooling Center', 'type': 'Cooling Center', 'lat': 26.9220, 'lng': 75.8010, 'cap': 500, 'phone': '+91-141-2200111'},
            {'location': 'Jaipur', 'name': 'Badi Chaupar Emergency Water Distribution Post', 'type': 'Water Point', 'lat': 26.9240, 'lng': 75.8310, 'cap': 1400, 'phone': '+91-141-2561234'},

            # Ahmedabad
            {'location': 'Ahmedabad', 'name': 'Civil Hospital Ahmedabad Heat Action Ward', 'type': 'Hospital', 'lat': 23.0530, 'lng': 72.6030, 'cap': 520, 'phone': '+91-79-22680074'},
            {'location': 'Ahmedabad', 'name': 'Sabarmati Riverfront Civic Cooling Pavilion', 'type': 'Cooling Center', 'lat': 23.0300, 'lng': 72.5700, 'cap': 650, 'phone': '+91-79-27550000'},
            {'location': 'Ahmedabad', 'name': 'Kalupur Transit Water Station', 'type': 'Water Point', 'lat': 23.0280, 'lng': 72.6010, 'cap': 1800, 'phone': '+91-79-22120000'},

            # Mumbai
            {'location': 'Mumbai', 'name': 'KEM Hospital & Seth GS Medical College Heat Emergency', 'type': 'Hospital', 'lat': 19.0020, 'lng': 72.8420, 'cap': 420, 'phone': '+91-22-24107000'},
            {'location': 'Mumbai', 'name': 'Dadar Central Transit Cooling Shelter', 'type': 'Cooling Center', 'lat': 19.0178, 'lng': 72.8478, 'cap': 600, 'phone': '+91-22-24300000'},
            {'location': 'Mumbai', 'name': 'Dharavi Emergency Potable Water Depot', 'type': 'Water Point', 'lat': 19.0400, 'lng': 72.8550, 'cap': 3000, 'phone': '+91-22-24070000'},

            # Lucknow
            {'location': 'Lucknow', 'name': 'King George Medical University (KGMU) Heat Ward', 'type': 'Hospital', 'lat': 26.8680, 'lng': 80.9160, 'cap': 400, 'phone': '+91-522-2257450'},
            {'location': 'Lucknow', 'name': 'Charbagh Railway Station Shaded Relief Wing', 'type': 'Cooling Center', 'lat': 26.8320, 'lng': 80.9190, 'cap': 450, 'phone': '+91-522-2635000'},

            # Hyderabad
            {'location': 'Hyderabad', 'name': 'Nizam Institute of Medical Sciences (NIMS) Heat Cell', 'type': 'Hospital', 'lat': 17.4220, 'lng': 78.4520, 'cap': 380, 'phone': '+91-40-23489000'},
            {'location': 'Hyderabad', 'name': 'Secunderabad Transit Shaded Cooling Center', 'type': 'Cooling Center', 'lat': 17.4399, 'lng': 78.5017, 'cap': 500, 'phone': '+91-40-27820000'},

            # Chennai
            {'location': 'Chennai', 'name': 'Rajiv Gandhi Government General Hospital (RGGGH)', 'type': 'Hospital', 'lat': 13.0805, 'lng': 80.2775, 'cap': 450, 'phone': '+91-44-25305000'},
            {'location': 'Chennai', 'name': 'Chennai Central Passenger Cooling Pavilion', 'type': 'Cooling Center', 'lat': 13.0827, 'lng': 80.2750, 'cap': 550, 'phone': '+91-44-25350000'},

            # Nagpur
            {'location': 'Nagpur', 'name': 'Government Medical College (GMC) Nagpur Heat Stroke Ward', 'type': 'Hospital', 'lat': 21.1350, 'lng': 79.0980, 'cap': 360, 'phone': '+91-712-2744400'},
            {'location': 'Nagpur', 'name': 'Sitabuldi Public Relief Shelter', 'type': 'Cooling Center', 'lat': 21.1440, 'lng': 79.0850, 'cap': 400, 'phone': '+91-712-2560000'},

            # Bhubaneswar
            {'location': 'Bhubaneswar', 'name': 'AIIMS Bhubaneswar Emergency Heat Trauma Center', 'type': 'Hospital', 'lat': 20.2310, 'lng': 85.7750, 'cap': 300, 'phone': '+91-674-2476789'},
            {'location': 'Bhubaneswar', 'name': 'Capital Hospital Dedicated Heat Ward', 'type': 'Hospital', 'lat': 20.2618, 'lng': 85.8290, 'cap': 180, 'phone': '+91-674-2391983'},
            {'location': 'Bhubaneswar', 'name': 'Baramunda Inter-State Transit Water Hub', 'type': 'Water Point', 'lat': 20.2780, 'lng': 85.7950, 'cap': 1000, 'phone': '+91-674-2351234'},

            # Kolkata
            {'location': 'Kolkata', 'name': 'SSKM Hospital Dedicated Heat Stroke Center', 'type': 'Hospital', 'lat': 22.5395, 'lng': 88.3429, 'cap': 350, 'phone': '+91-33-22231589'},
            {'location': 'Kolkata', 'name': 'Howrah Transit Shaded Cooling Pavilion', 'type': 'Cooling Center', 'lat': 22.5850, 'lng': 88.3410, 'cap': 500, 'phone': '+91-33-26602000'},

            # Cuttack
            {'location': 'Cuttack', 'name': 'SCB Medical College & Hospital Heat Stroke Ward', 'type': 'Hospital', 'lat': 20.4780, 'lng': 85.8920, 'cap': 380, 'phone': '+91-671-2414004'},

            # Patna
            {'location': 'Patna', 'name': 'PMCH Emergency Heat Management Wing', 'type': 'Hospital', 'lat': 25.6208, 'lng': 85.1612, 'cap': 280, 'phone': '+91-612-2300080'},

            # Bengaluru
            {'location': 'Bengaluru', 'name': 'Victoria Hospital Emergency Clinical Care', 'type': 'Hospital', 'lat': 12.9630, 'lng': 77.5740, 'cap': 300, 'phone': '+91-80-26701150'},
        ]

        CriticalFacility.query.delete()
        for fac in facilities_data:
            loc = loc_map.get(fac['location'])
            if loc:
                facility = CriticalFacility(
                    location_id=loc.id,
                    name=fac['name'],
                    facility_type=fac['type'],
                    latitude=fac['lat'],
                    longitude=fac['lng'],
                    capacity=fac['cap'],
                    contact_phone=fac['phone']
                )
                db.session.add(facility)
        print(f" -> Seeded {len(facilities_data)} Pan-India Critical Facilities across key zones.")

        # 4. Standard Operating Procedures (NDMA aligned)
        if ResponseRecommendation.query.count() == 0:
            sops_data = [
                {'level': 'LOW', 'sector': 'Public', 'priority': 'P3', 'title': 'Routine Hydration & Sun Awareness', 'desc': 'Advise citizens to maintain regular hydration and carry umbrellas or head coverings during peak solar hours.'},
                {'level': 'LOW', 'sector': 'Health', 'priority': 'P3', 'title': 'Routine Facility Monitoring', 'desc': 'Ensure primary health centers maintain adequate inventory of oral rehydration salts (ORS) and IV fluids.'},
                {'level': 'LOW', 'sector': 'Municipal', 'priority': 'P3', 'title': 'Park & Green Space Maintenance', 'desc': 'Maintain public fountains, water troughs, and ensure urban parks remain open for natural canopy shade.'},
                {'level': 'MODERATE', 'sector': 'Public', 'priority': 'P2', 'title': 'Issue Yellow Heat Advisory', 'desc': 'Broadcast advisory warning vulnerable citizens (elderly, infants, outdoor laborers) to avoid direct sun exposure between 11 AM and 4 PM.'},
                {'level': 'MODERATE', 'sector': 'Labor', 'priority': 'P2', 'title': 'Adjust Outdoor Labor Timings', 'desc': 'Recommend rescheduling heavy construction, street sweeping, and steel plant outdoor work to morning (6 AM - 11 AM) and late afternoon (4 PM - 7 PM).'},
                {'level': 'MODERATE', 'sector': 'Health', 'priority': 'P2', 'title': 'Heat-Cramp First-Aid Readiness', 'desc': 'Staff emergency clinics with designated heat-exhaustion observation beds and distribute free ORS packets at bus stands and railway stations.'},
                {'level': 'MODERATE', 'sector': 'Municipal', 'priority': 'P2', 'title': 'Deploy Municipal Water Kiosks', 'desc': 'Ensure all public water kiosks and shaded waiting areas in marketplaces are fully functional.'},
                {'level': 'HIGH', 'sector': 'Public', 'priority': 'P1', 'title': 'Issue Orange Heat Warning & Restrict Gatherings', 'desc': 'Issue multi-channel emergency broadcast warnings. Advise postponement of non-essential open-air gatherings and sports tournaments.'},
                {'level': 'HIGH', 'sector': 'Labor', 'priority': 'P1', 'title': 'Mandate Cease-Work During Peak Hours', 'desc': 'Enforce mandatory suspension of direct-sun construction and heavy manual labor between 12:00 PM and 3:30 PM with provided shaded resting areas.'},
                {'level': 'HIGH', 'sector': 'Health', 'priority': 'P1', 'title': 'Activate Hospital Dedicated Heat Wards', 'desc': 'Open specialized cooling wards equipped with ice packs, air conditioning, and emergency cooling baths in major tertiary hospitals.'},
                {'level': 'HIGH', 'sector': 'Municipal', 'priority': 'P1', 'title': 'Dispatch Emergency Water Tankers to Slums', 'desc': 'Direct municipal water tankers to high-density informal settlements and industrial worker colonies experiencing water scarcity.'},
                {'level': 'EXTREME', 'sector': 'Public', 'priority': 'P1', 'title': 'Declare Red Alert & Emergency Protocol Activation', 'desc': 'Activate Disaster Management Authority emergency heat protocol. Advise citizens to remain indoors in well-ventilated or cooled spaces.'},
                {'level': 'EXTREME', 'sector': 'Municipal', 'priority': 'P1', 'title': 'Activate All Civic Cooling Shelters 24/7', 'desc': 'Open government community halls, transit hubs, and commercial centers as public air-conditioned relief centers with drinking water and medical attendants.'},
                {'level': 'EXTREME', 'sector': 'Labor', 'priority': 'P1', 'title': 'Total Ban on Outdoor Physical Work', 'desc': 'Mandate complete prohibition of outdoor manual labor, delivery services without AC, and heavy construction until temperatures subside.'},
                {'level': 'EXTREME', 'sector': 'Health', 'priority': 'P1', 'title': 'Mass Casualty Heat-Stroke Preparedness', 'desc': 'Put state ambulance networks on high alert with on-board cooling pads, rapid rehydration systems, and real-time bed tracking.'},
            ]
            for sop in sops_data:
                item = ResponseRecommendation(
                    risk_level=sop['level'],
                    title=sop['title'],
                    description=sop['desc'],
                    target_sector=sop['sector'],
                    priority=sop['priority']
                )
                db.session.add(item)
            print(" -> Seeded 15 Disaster Response SOPs.")

        # 5. Seed Socio-Demographic Vulnerability Data (All 24 Cities)
        vulnerability_dict = {
            # East Zone
            'Rourkela': {'pop': 650000, 'eld': 58500, 'chi': 52000, 'out': 162500, 'slum': 175000, 'beds': 2200, 'water': 120, 'canopy': 0.16},
            'Jharsuguda': {'pop': 280000, 'eld': 25200, 'chi': 22400, 'out': 75600, 'slum': 72800, 'beds': 650, 'water': 45, 'canopy': 0.12},
            'Sambalpur': {'pop': 335000, 'eld': 33500, 'chi': 26800, 'out': 83750, 'slum': 87100, 'beds': 1100, 'water': 65, 'canopy': 0.15},
            'Bhubaneswar': {'pop': 880000, 'eld': 88000, 'chi': 70400, 'out': 220000, 'slum': 237600, 'beds': 3800, 'water': 150, 'canopy': 0.19},
            'Cuttack': {'pop': 658000, 'eld': 65800, 'chi': 52640, 'out': 164500, 'slum': 184240, 'beds': 2800, 'water': 110, 'canopy': 0.14},
            'Jamshedpur': {'pop': 1340000, 'eld': 134000, 'chi': 107200, 'out': 348400, 'slum': 361800, 'beds': 4200, 'water': 180, 'canopy': 0.18},
            'Ranchi': {'pop': 1125000, 'eld': 101250, 'chi': 90000, 'out': 281250, 'slum': 270000, 'beds': 3500, 'water': 160, 'canopy': 0.20},
            'Kolkata': {'pop': 4486679, 'eld': 583268, 'chi': 314067, 'out': 1121669, 'slum': 1480604, 'beds': 24000, 'water': 820, 'canopy': 0.10},
            'Patna': {'pop': 1683200, 'eld': 151488, 'chi': 168320, 'out': 471296, 'slum': 538624, 'beds': 8200, 'water': 240, 'canopy': 0.09},

            # North Zone
            'New Delhi': {'pop': 16787941, 'eld': 1343035, 'chi': 1510914, 'out': 4532744, 'slum': 5204261, 'beds': 54000, 'water': 2800, 'canopy': 0.13},
            'Lucknow': {'pop': 2815601, 'eld': 253404, 'chi': 281560, 'out': 788368, 'slum': 844680, 'beds': 11200, 'water': 450, 'canopy': 0.14},
            'Varanasi': {'pop': 1201815, 'eld': 120181, 'chi': 132199, 'out': 348526, 'slum': 408617, 'beds': 4800, 'water': 220, 'canopy': 0.11},
            'Chandigarh': {'pop': 1055450, 'eld': 94990, 'chi': 105545, 'out': 263862, 'slum': 189981, 'beds': 4200, 'water': 280, 'canopy': 0.35},

            # Northwest & Arid
            'Jaipur': {'pop': 3073350, 'eld': 276601, 'chi': 338068, 'out': 860538, 'slum': 799071, 'beds': 12500, 'water': 420, 'canopy': 0.09},
            'Jodhpur': {'pop': 1033918, 'eld': 93052, 'chi': 113730, 'out': 299836, 'slum': 289497, 'beds': 4100, 'water': 160, 'canopy': 0.06},
            'Ahmedabad': {'pop': 5577940, 'eld': 502014, 'chi': 557794, 'out': 1506043, 'slum': 1561823, 'beds': 21000, 'water': 750, 'canopy': 0.08},
            'Nagpur': {'pop': 2405665, 'eld': 216509, 'chi': 216509, 'out': 649529, 'slum': 769812, 'beds': 9800, 'water': 360, 'canopy': 0.15},

            # West & Central
            'Mumbai': {'pop': 12442373, 'eld': 1119813, 'chi': 995389, 'out': 3483864, 'slum': 5225796, 'beds': 45000, 'water': 2100, 'canopy': 0.11},
            'Pune': {'pop': 3124458, 'eld': 312445, 'chi': 281201, 'out': 843603, 'slum': 874848, 'beds': 13500, 'water': 520, 'canopy': 0.22},
            'Bhopal': {'pop': 1798218, 'eld': 161839, 'chi': 179821, 'out': 503501, 'slum': 485518, 'beds': 7200, 'water': 280, 'canopy': 0.21},
            'Raipur': {'pop': 1010000, 'eld': 90900, 'chi': 80800, 'out': 262600, 'slum': 272700, 'beds': 3400, 'water': 140, 'canopy': 0.13},

            # South Zone
            'Hyderabad': {'pop': 6809970, 'eld': 612897, 'chi': 680997, 'out': 1906791, 'slum': 2179190, 'beds': 26000, 'water': 920, 'canopy': 0.12},
            'Chennai': {'pop': 4681087, 'eld': 514919, 'chi': 374486, 'out': 1310704, 'slum': 1357515, 'beds': 22000, 'water': 880, 'canopy': 0.15},
            'Bengaluru': {'pop': 8443675, 'eld': 759930, 'chi': 759930, 'out': 2279792, 'slum': 1688735, 'beds': 34000, 'water': 1350, 'canopy': 0.24},
        }

        VulnerabilityData.query.delete()
        for loc_name, vdata in vulnerability_dict.items():
            loc = loc_map.get(loc_name)
            if loc:
                pop = vdata['pop']
                eld = vdata['eld']
                chi = vdata['chi']
                out = vdata['out']
                slum = vdata['slum']
                beds = vdata['beds']
                water = vdata['water']
                canopy = vdata['canopy']
                
                sens_pop_ratio = (eld + chi + out + slum) / max(pop, 1)
                bed_ratio = (beds / (pop / 1000.0))
                water_ratio = (water / (pop / 10000.0))
                
                demographic_factor = min(sens_pop_ratio * 100.0 * 1.5, 60.0)
                healthcare_gap = max(0.0, 20.0 - (bed_ratio * 3.0))
                water_gap = max(0.0, 15.0 - (water_ratio * 5.0))
                canopy_gap = max(0.0, (0.25 - canopy) * 40.0)
                
                v_score = min(max(demographic_factor + healthcare_gap + water_gap + canopy_gap, 10.0), 98.0)
                v_level = 'EXTREME' if v_score >= 75 else ('HIGH' if v_score >= 50 else ('MODERATE' if v_score >= 25 else 'LOW'))

                v_obj = VulnerabilityData(
                    location_id=loc.id,
                    total_population=pop,
                    elderly_count=eld,
                    children_count=chi,
                    outdoor_workers_count=out,
                    slum_residents_count=slum,
                    hospital_beds=beds,
                    water_kiosks=water,
                    tree_canopy_ratio=canopy,
                    vulnerability_score=v_score,
                    vulnerability_level=v_level
                )
                db.session.add(v_obj)
        print(" -> Seeded ground-level vulnerability data for all 24 Pan-India stations.")

        # 6. Ensure initial realistic Weather Readings for all 24 stations
        today = datetime.now(timezone.utc).date()
        for loc_name, loc in loc_map.items():
            w_rec = WeatherData.query.filter_by(location_id=loc.id, date=today).first()
            if not w_rec:
                # Provide calibrated seasonal baseline reading
                base = loc.baseline_temp
                hum = 65.0 if 'Coastal' in loc.zone_type else (35.0 if 'Arid' in loc.zone_type else 50.0)
                hi = calculate_heat_index(base, hum)
                w_rec = WeatherData(
                    location_id=loc.id,
                    date=today,
                    temperature=base,
                    humidity=hum,
                    wind_speed=12.0,
                    rainfall=0.0,
                    pressure=1012.0,
                    heat_index=round(hi, 1),
                    is_simulated=True
                )
                db.session.add(w_rec)
        print(" -> Ensured active baseline weather records for all 24 stations.")

        db.session.commit()
        print(" -> Pan-India National Network successfully seeded!")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    seed_database(app)
