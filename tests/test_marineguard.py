"""
MarineGuard AI - Comprehensive Automated Test Suite
Smart India Hackathon 2026 (PS-1655)
Tests:
1. SAR preprocessing, U-Net inference, Lee Filter, GLCM texture
2. Bonn Agreement oil quantification
3. AIS spatial-temporal filtering & behavioral anomaly priority scoring (0-100)
4. 72h Lagrangian drift & physical weathering decay (evaporation + emulsification)
5. OBIS marine biodiversity & ecological risk assessment (LOW/MED/HIGH/CRITICAL)
6. MetOcean environmental & SST anomaly analytics
7. Pre-incident maritime risk modeling
8. Multi-pillar evidence fusion dossier
9. FastAPI REST API endpoints
"""

import os
import unittest
import numpy as np
from datetime import datetime

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.sar_detection import process_sar_imagery
from backend.app.services.ais_service import calculate_haversine_distance_km, find_candidate_vessels_near_spill
from backend.app.services.vessel_behavior import compute_vessel_behavior_metrics, rank_candidate_vessels
from backend.app.services.trajectory_simulator import simulate_oil_spill_trajectory
from backend.app.services.ecological_service import assess_ecological_impact
from backend.app.services.environmental_service import get_environmental_context
from backend.app.services.risk_assessment import get_pre_incident_risk_zones
from backend.app.services.evidence_fusion import synthesize_evidence_dossier
from backend.app.services.demo_scenarios import build_demo_scenario


class TestMarineGuardAI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_sar_detection_and_bonn_scale(self):
        """Test SAR U-Net preprocessing, segmentation, and Bonn classification"""
        test_img = np.random.normal(130, 20, (256, 256, 3)).astype(np.uint8)
        # Add synthetic dark spot
        test_img[100:150, 100:150] = 30

        result = process_sar_imagery(test_img, center_lat=28.735, center_lon=-88.382, pixel_res_m=10.0)
        self.assertIn("spill_polygons", result)
        self.assertIn("total_affected_area_km2", result)
        self.assertIn("overall_confidence", result)
        self.assertIn("raw_image_url", result)
        self.assertIn("overlay_image_url", result)

        if result["spill_polygons"]:
            first_poly = result["spill_polygons"][0]
            self.assertIn("bonn_code", first_poly)
            self.assertIn("estimated_volume_bbl", first_poly)
            self.assertIn("nominal_thickness_um", first_poly)
            self.assertGreater(first_poly["area_km2"], 0)

    def test_02_ais_spatial_distance_and_queries(self):
        """Test great-circle distance and nearest vessel spatial filtering"""
        dist = calculate_haversine_distance_km(28.735, -88.382, 28.740, -88.380)
        self.assertGreater(dist, 0.0)
        self.assertLess(dist, 5.0)

        vessels = [
            {
                "mmsi": "111222333",
                "vessel_name": "Test Vessel A",
                "positions": [{"lat": 28.736, "lon": -88.381, "sog_knots": 4.0}]
            },
            {
                "mmsi": "444555666",
                "vessel_name": "Far Away Vessel B",
                "positions": [{"lat": 35.0, "lon": -70.0, "sog_knots": 15.0}]
            }
        ]
        candidates = find_candidate_vessels_near_spill(vessels, 28.735, -88.382, spill_radius_km=10.0)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["vessel"]["mmsi"], "111222333")

    def test_03_vessel_behavior_and_investigation_priority(self):
        """Test explainable investigation priority score (0-100) and ranking"""
        vessel_anomalous = {
            "mmsi": "356891000",
            "vessel_name": "Anomalous Tanker",
            "vessel_type": "Crude Oil Tanker",
            "simulated_features": {
                "min_distance_km": 0.5,
                "speed_anomaly_drop_knots": 12.0,
                "route_deviation_deg": 65.0,
                "time_in_spill_zone_min": 40.0
            }
        }
        vessel_innocent = {
            "mmsi": "228394000",
            "vessel_name": "Passing Cargo",
            "vessel_type": "Container Ship",
            "simulated_features": {
                "min_distance_km": 15.0,
                "speed_anomaly_drop_knots": 0.2,
                "route_deviation_deg": 1.0,
                "time_in_spill_zone_min": 0.0
            }
        }

        ranked = rank_candidate_vessels([vessel_innocent, vessel_anomalous], 28.735, -88.382)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["vessel"]["mmsi"], "356891000")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertGreater(ranked[0]["priority_score"], 70.0)
        self.assertLess(ranked[1]["priority_score"], 40.0)
        self.assertIn("score_breakdown", ranked[0]["metrics"])

    def test_04_lagrangian_drift_and_weathering(self):
        """Test 72-hour drift advection and physical weathering decay"""
        polygon = {"coordinates": [[[ -88.38, 28.73], [-88.37, 28.73], [-88.37, 28.74], [-88.38, 28.74], [-88.38, 28.73] ]]}
        steps = simulate_oil_spill_trajectory(
            origin_lat=28.735,
            origin_lon=-88.382,
            spill_polygon=polygon,
            wind_speed_knots=12.0,
            wind_direction_deg=135.0,
            current_speed_knots=1.0,
            current_direction_deg=310.0,
            intervals_hours=[6, 12, 24, 48, 72]
        )

        self.assertEqual(len(steps), 5)
        # Check monotonic increase of drift distance and evaporation
        distances = [s["total_drift_km"] for s in steps]
        evaporations = [s["evaporated_fraction_pct"] for s in steps]
        emulsifications = [s["emulsified_water_pct"] for s in steps]

        self.assertTrue(all(distances[i] < distances[i+1] for i in range(len(distances)-1)))
        self.assertTrue(all(evaporations[i] < evaporations[i+1] for i in range(len(evaporations)-1)))
        self.assertTrue(all(emulsifications[i] <= emulsifications[i+1] for i in range(len(emulsifications)-1)))

    def test_05_ecological_impact_and_obis(self):
        """Test OBIS marine species vulnerability and categorical rating"""
        eco = assess_ecological_impact(28.735, -88.382, spill_area_km2=45.0)
        self.assertIn(eco["ecological_risk_level"], ["HIGH", "CRITICAL"])
        self.assertGreater(eco["exposed_species_count"], 0)
        self.assertIn("Lepidochelys kempii", [s["scientific_name"] for s in eco["exposed_species_records"]])

    def test_06_climate_and_environmental_analytics(self):
        """Test SST, SST anomaly, marine heatwaves, and MetOcean vectors"""
        env = get_environmental_context(28.735, -88.382, "gulf_of_mexico")
        self.assertIn("sea_surface_temp_c", env)
        self.assertIn("sst_anomaly_c", env)
        self.assertIn("marine_heatwave_category", env)
        self.assertGreater(env["wind_speed_knots"], 0)

    def test_07_pre_incident_risk_zones(self):
        """Test predictive maritime risk zones"""
        zones = get_pre_incident_risk_zones()
        self.assertGreaterEqual(len(zones), 2)
        for z in zones:
            self.assertIn("zone_id", z)
            self.assertIn("composite_risk_score", z)
            self.assertIn("traffic_density_ships_per_day", z)

    def test_08_evidence_fusion_dossier(self):
        """Test multi-pillar evidence fusion dossier"""
        scenario = build_demo_scenario("demo_gulf_of_mexico")
        dossier = scenario["evidence_dossier"]
        self.assertIn("executive_summary", dossier)
        self.assertIn("pillars", dossier)
        self.assertEqual(len(dossier["pillars"]), 5)
        self.assertGreaterEqual(len(dossier["recommended_response_actions"]), 1)

    def test_09_api_endpoints(self):
        """Test all core REST API endpoints"""
        # GET /api/demo/scenarios
        res_scenarios = self.client.get("/api/demo/scenarios")
        self.assertEqual(res_scenarios.status_code, 200)

        # POST /api/demo/load-scenario
        res_load = self.client.post("/api/demo/load-scenario?scenario_id=demo_gulf_of_mexico")
        self.assertEqual(res_load.status_code, 200)

        # GET /api/incidents
        res_incidents = self.client.get("/api/incidents")
        self.assertEqual(res_incidents.status_code, 200)

        # GET /api/spills
        res_spills = self.client.get("/api/spills")
        self.assertEqual(res_spills.status_code, 200)

        # GET /api/vessels
        res_vessels = self.client.get("/api/vessels")
        self.assertEqual(res_vessels.status_code, 200)

        # GET /api/risk-zones
        res_risk = self.client.get("/api/risk-zones")
        self.assertEqual(res_risk.status_code, 200)

        # POST /api/detect-spill (synthetic)
        res_detect = self.client.post("/api/detect-spill", data={"center_lat": 28.735, "center_lon": -88.382})
        self.assertEqual(res_detect.status_code, 200)
        data = res_detect.json()
        self.assertIn("spill_detection", data)
        self.assertIn("candidate_vessels", data)


if __name__ == "__main__":
    unittest.main()
