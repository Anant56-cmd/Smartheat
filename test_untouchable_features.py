"""
Unit and Integration Tests for the 4 Untouchable Enterprise Features:
1. OASIS CAP v1.2 XML Protocol compliance
2. IPCC Climate Crisis Stress-Testing Simulation
3. Capacitated Vehicle Routing Problem (CVRP) Dispatch Scheduler
4. OpenAPI 3.0 / Swagger Specification Endpoint
"""

import unittest
import json
import xml.etree.ElementTree as ET
from app import create_app
from services.cap_service import generate_cap_xml, CAP_NAMESPACE
from services.climate_simulator import run_climate_stress_simulation
from services.vrp_scheduler import FleetVRPScheduler

class UntouchableFeaturesTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_01_oasis_cap_xml_validity(self):
        """Test OASIS CAP v1.2 XML output against standard schema elements."""
        sample_alerts = [{
            'location_name': 'Rourkela',
            'risk_level': 'EXTREME',
            'temperature': 45.5,
            'heat_index': 54.0,
            'vulnerability_score': 72.0,
            'latitude': 22.26,
            'longitude': 84.85
        }]
        xml_str = generate_cap_xml(sample_alerts)
        root = ET.fromstring(xml_str)
        
        # Verify namespace & mandatory OASIS elements
        self.assertIn("alert", root.tag)
        self.assertIsNotNone(root.find(f"{{{CAP_NAMESPACE}}}identifier"))
        self.assertIsNotNone(root.find(f"{{{CAP_NAMESPACE}}}sender"))
        self.assertIsNotNone(root.find(f"{{{CAP_NAMESPACE}}}sent"))
        self.assertEqual(root.find(f"{{{CAP_NAMESPACE}}}status").text, "Actual")

        # Verify info block
        info = root.find(f"{{{CAP_NAMESPACE}}}info")
        self.assertIsNotNone(info)
        self.assertEqual(info.find(f"{{{CAP_NAMESPACE}}}severity").text, "Extreme")
        self.assertIn("Rourkela", info.find(f"{{{CAP_NAMESPACE}}}headline").text)

    def test_02_ipcc_climate_simulator(self):
        """Test IPCC climate stress test with compound blackout shock."""
        with self.app.app_context():
            res = run_climate_stress_simulation(temp_anomaly=3.0, grid_blackout=True, water_pipeline_rupture=True)
            self.assertEqual(res['scenario']['temperature_anomaly_deg_c'], 3.0)
            self.assertTrue(res['scenario']['grid_blackout_active'])
            self.assertGreater(res['systemic_impact']['simulated_extreme_stations'], 0)
            self.assertGreater(res['systemic_impact']['total_projected_bed_deficit'], 0)
            self.assertGreaterEqual(len(res['stations']), 24)

    def test_03_vrp_fleet_scheduler(self):
        """Test Capacitated Vehicle Routing Problem (CVRP) dispatch scheduler."""
        scheduler = FleetVRPScheduler()
        allocated_wards = [
            {'ward_name': 'Sector-19 Ward', 'allocated_tankers': 2, 'latitude': 22.258, 'longitude': 84.872, 'priority_score': 88.0, 'risk_level': 'EXTREME'},
            {'ward_name': 'Panposh Slum Cluster', 'allocated_tankers': 3, 'latitude': 22.245, 'longitude': 84.821, 'priority_score': 95.0, 'risk_level': 'EXTREME'},
            {'ward_name': 'Civil Township', 'allocated_tankers': 1, 'latitude': 22.240, 'longitude': 84.845, 'priority_score': 60.0, 'risk_level': 'MODERATE'}
        ]
        res = scheduler.generate_fleet_routes(allocated_wards, num_tankers=5, tanker_capacity_liters=10000)
        self.assertGreater(res['total_routes'], 0)
        self.assertGreater(res['total_transit_distance_km'], 0.0)
        self.assertGreater(res['total_fuel_saved_liters'], 0.0)
        self.assertEqual(res['total_water_dispatched_liters'], 60000)

    def test_04_api_cap_xml_endpoint(self):
        """Test GET /api/v1/alerts/cap.xml returns XML content-type."""
        res = self.client.get('/api/v1/alerts/cap.xml')
        self.assertEqual(res.status_code, 200)
        self.assertIn('alert', res.data.decode('utf-8'))
        self.assertIn('cap', res.data.decode('utf-8'))

    def test_05_api_climate_simulation_endpoint(self):
        """Test POST /api/v1/simulate/climate endpoint."""
        payload = {'temp_anomaly': 2.0, 'grid_blackout': False, 'water_pipeline_rupture': False}
        res = self.client.post('/api/v1/simulate/climate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('scenario', data)
        self.assertIn('systemic_impact', data)

    def test_06_openapi_spec_endpoint(self):
        """Test GET /api/v1/openapi.json returns valid OpenAPI 3.0 schema."""
        res = self.client.get('/api/v1/openapi.json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['openapi'], '3.0.3')
        self.assertIn('/api/v1/predict', data['paths'])
        self.assertIn('/api/v1/alerts/cap.xml', data['paths'])
