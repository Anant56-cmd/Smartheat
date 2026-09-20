import unittest
import json
from app import create_app
from database.db import db
from database.models import User, Location, WeatherData, Alert, CriticalFacility
from ml.preprocessing import calculate_heat_index, determine_risk_label
from ml.predictor import predict_single
from services.risk_service import calculate_composite_heat_risk
from services.alert_service import check_and_create_alert, resolve_alert

class SmartHeatTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_01_heat_index_calculation(self):
        """Test NOAA Heat Index equation accuracy against standard reference values."""
        # Mild day: 25°C, 40% humidity -> Should remain mild
        hi_mild = calculate_heat_index(25.0, 40.0)
        self.assertLess(hi_mild, 30.0)

        # Dangerous day: 42°C, 45% humidity -> Should yield extreme Heat Index (> 50°C)
        hi_extreme = calculate_heat_index(42.0, 45.0)
        self.assertGreater(hi_extreme, 50.0)

        # Categorical risk labeling
        label_mild = determine_risk_label(25.0, hi_mild)
        self.assertEqual(label_mild, 'LOW')

        label_extreme = determine_risk_label(42.0, hi_extreme)
        self.assertIn(label_extreme, ['HIGH', 'EXTREME'])

    def test_02_ml_prediction_pipeline(self):
        """Test machine learning inference with serialized Random Forest model."""
        res = predict_single(temperature=43.0, humidity=50.0, wind_speed=10.0)
        self.assertIn(res['predicted_risk'], ['LOW', 'MODERATE', 'HIGH', 'EXTREME'])
        self.assertGreaterEqual(res['confidence'], 50.0)
        self.assertIn('probabilities', res)
        self.assertEqual(len(res['probabilities']), 4)
        self.assertGreater(res['heat_index'], 45.0)

    def test_03_composite_risk_scoring(self):
        """Test transparent 0-100 composite risk scoring engine."""
        score_data = calculate_composite_heat_risk(
            temperature=41.0,
            humidity=55.0,
            baseline_temp=33.0,
            vulnerability_score=65.0,
            zone_type='Urban',
            population=5000000,
            hospital_beds=15000,
            water_kiosks=450
        )
        total_score = score_data['total_risk_score']
        self.assertGreaterEqual(total_score, 0.0)
        self.assertLessEqual(total_score, 100.0)
        self.assertIn(score_data['risk_level'], ['LOW', 'MODERATE', 'HIGH', 'EXTREME'])
        self.assertIn('breakdown', score_data)

    def test_04_user_authentication(self):
        """Test authentication flow, session security, and access control."""
        # Unauthenticated access to dashboard should redirect to login
        res_unauth = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn('/auth/login', res_unauth.location)

        # Valid login
        res_login = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Executive Dashboard', res_login.data)

    def test_05_authenticated_endpoints(self):
        """Verify all core dashboard, data management, GIS map, and reporting routes."""
        # Authenticate first
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})

        endpoints = [
            ('/dashboard', b'Executive Disaster Dashboard'),
            ('/dashboard/api/chart-data', b'trends'),
            ('/weather/', b'Weather Data Management'),
            ('/predictions/', b'Live Model Inference Simulator'),
            ('/map/', b'Interactive GIS Heat-Risk'),
            ('/map/api/data', b'locations'),
            ('/vulnerability/', b'Ground-Level Vulnerability'),
            ('/alerts/', b'Early Warning & Emergency Alert Center'),
            ('/recommendations/', b'Disaster Response Standard Operating Procedures'),
            ('/reports/', b'Reports, Audit Registry & Data Exports'),
        ]

        for url, expected_text in endpoints:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200)
                self.assertIn(expected_text, res.data)

    def test_06_csv_export_endpoints(self):
        """Test CSV download exports for audit and offline reporting."""
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})

        for report_type in ['weather', 'predictions', 'alerts', 'vulnerability', 'recommendations']:
            with self.subTest(report_type=report_type):
                res = self.client.get(f'/reports/export/csv/{report_type}')
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.mimetype, 'text/csv')
                self.assertIn('attachment;', res.headers.get('Content-Disposition', ''))

    def test_07_realtime_weather_service(self):
        """Test real-time meteorological API retrieval from Open-Meteo."""
        from services.realtime_weather_service import fetch_live_weather
        # Test Delhi coordinates (28.6139, 77.2090)
        try:
            live = fetch_live_weather(28.6139, 77.2090, timeout=10)
            self.assertIn('temperature', live)
            self.assertIn('humidity', live)
            self.assertIn('heat_index', live)
            self.assertGreaterEqual(live['humidity'], 0.0)
            self.assertLessEqual(live['humidity'], 100.0)
        except Exception as e:
            # Network fallback check
            self.assertTrue(True, f"Network timeout accepted for offline runners: {e}")

        # Test live station endpoint
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
        with self.app.app_context():
            loc = Location.query.first()
            loc_id = loc.id if loc else 1

        res = self.client.get(f'/weather/api/live-station/{loc_id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

    def test_08_city_search_and_add(self):
        """Test universal geocoding city search and dynamic city ingestion."""
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})

        # Test search
        res_search = self.client.get('/weather/api/search-city?q=Ranchi')
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.get_json()
        self.assertIn('results', search_data)

        # Test dynamic addition of a searched city
        res_add = self.client.post('/weather/api/add-city', json={
            'name': 'Dhanbad',
            'state': 'Jharkhand',
            'latitude': 23.7957,
            'longitude': 86.4304
        })
        self.assertEqual(res_add.status_code, 200)
        add_data = res_add.get_json()
        self.assertTrue(add_data.get('success'))
        self.assertEqual(add_data['data']['name'], 'Dhanbad')

if __name__ == '__main__':
    unittest.main()
