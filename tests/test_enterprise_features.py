"""
Unit and Integration Tests for Enterprise Features:
- Explainable AI (XAI) Local Feature Attribution Engine
- Algorithmic Municipal Resource Dispatch Optimizer
- SRE Liveness/Readiness Probe & Prometheus Telemetry Metrics
- Versioned API (v1) Endpoints
"""

import unittest
import json
from app import create_app
from ml.predictor import get_model_and_scaler, predict_single
from ml.explainability import explain_prediction
from services.resource_optimizer import MunicipalResourceOptimizer

class EnterpriseFeaturesTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_01_explainable_ai_feature_attribution(self):
        """Test Explainable AI (XAI) feature attribution mathematics."""
        model, scaler = get_model_and_scaler()
        test_input = {
            'Temperature': 43.5,
            'Humidity': 55.0,
            'Wind_Speed': 6.0,
            'Rainfall': 0.0,
            'Pressure': 1011.0
        }
        xai = explain_prediction(model, scaler, test_input)
        self.assertIn('target_class', xai)
        self.assertIn('feature_attributions', xai)
        self.assertEqual(len(xai['feature_attributions']), 10)

        # Verify percentages sum to ~100%
        pct_sum = sum(a['percentage'] for a in xai['feature_attributions'])
        self.assertAlmostEqual(pct_sum, 100.0, delta=1.5)

        # High temperature input should have Temperature as a positive risk driver
        top_driver_features = [d['feature'] for d in xai['top_risk_drivers']]
        self.assertTrue(any(f in top_driver_features for f in ['Temperature', 'Heat_Index', 'Temp_Humid_Product']))

    def test_02_algorithmic_resource_optimizer(self):
        """Test greedy priority-queue resource allocation solver."""
        optimizer = MunicipalResourceOptimizer(fleet_water_tankers=20, total_ors_kits=3000, emergency_beds=50)
        wards_data = [
            {'id': 1, 'name': 'Ward A (Slum Belt)', 'risk_score': 85.0, 'risk_level': 'EXTREME', 'total_population': 50000, 'depot_distance_km': 2.0},
            {'id': 2, 'name': 'Ward B (Residential)', 'risk_score': 45.0, 'risk_level': 'MODERATE', 'total_population': 30000, 'depot_distance_km': 6.0},
            {'id': 3, 'name': 'Ward C (Dense Urban)', 'risk_score': 72.0, 'risk_level': 'HIGH', 'total_population': 60000, 'depot_distance_km': 3.5}
        ]
        result = optimizer.optimize_dispatch(wards_data)

        self.assertEqual(result['fleet_capacity'], 20)
        self.assertGreater(result['total_tankers_dispatched'], 0)
        self.assertLessEqual(result['total_tankers_dispatched'], 20)
        self.assertGreater(result['system_risk_mitigation_pct'], 0.0)

        # Priority verification: Ward A should have higher priority than Ward B
        alloc_map = {w['ward_name']: w for w in result['wards_allocation']}
        self.assertGreater(alloc_map['Ward A (Slum Belt)']['priority_score'], alloc_map['Ward B (Residential)']['priority_score'])
        self.assertGreaterEqual(alloc_map['Ward A (Slum Belt)']['allocated_tankers'], alloc_map['Ward B (Residential)']['allocated_tankers'])

    def test_03_sre_health_probe(self):
        """Test /api/v1/health liveness and readiness probe."""
        res = self.client.get('/api/v1/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['checks']['database'], 'up')
        self.assertEqual(data['checks']['ml_model_cache'], 'ready')

    def test_04_prometheus_metrics_endpoint(self):
        """Test /api/v1/metrics Prometheus exposition."""
        res = self.client.get('/api/v1/metrics')
        self.assertEqual(res.status_code, 200)
        text = res.data.decode('utf-8')
        self.assertIn('smartheat_uptime_seconds', text)
        self.assertIn('smartheat_http_requests_total', text)
        self.assertIn('smartheat_active_alerts', text)

    def test_05_api_predict_with_xai(self):
        """Test POST /api/v1/predict returns prediction + XAI payload."""
        payload = {
            'temperature': 41.0,
            'humidity': 50.0,
            'wind_speed': 8.0,
            'rainfall': 0.0,
            'pressure': 1012.0
        }
        res = self.client.post('/api/v1/predict', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('predicted_risk', data)
        self.assertIn('explainability', data)
        self.assertIn('feature_attributions', data['explainability'])
        self.assertIn('inference_latency_ms', data)

    def test_06_api_optimize_dispatch(self):
        """Test POST /api/v1/optimize/dispatch endpoint."""
        payload = {'fleet_water_tankers': 25, 'total_ors_kits': 4000, 'emergency_beds': 80}
        res = self.client.post('/api/v1/optimize/dispatch', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('system_risk_mitigation_pct', data)
        self.assertIn('wards_allocation', data)
