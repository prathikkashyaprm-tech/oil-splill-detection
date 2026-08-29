"""
MarineAI Automated Test Suite
Validates computer vision pipelines, look-alike discrimination, Bonn Agreement calculations,
and Lagrangian ocean drift physics.
"""

import unittest
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from marineai_engine.sample_generator import (
    generate_sar_oil_spill_image,
    generate_clean_ocean_sar_image,
    generate_drone_optical_slick_image,
    generate_algal_bloom_image,
    generate_ship_wake_image
)
from marineai_engine.detector import process_marine_image
from marineai_engine.bonn_scale import calculate_bonn_metrics
from marineai_engine.drift_simulator import simulate_oil_drift

class TestMarineAIEngine(unittest.TestCase):
    
    def test_sar_oil_spill_detection(self):
        """Test that synthetic SAR oil spill is correctly classified as positive spill."""
        img = generate_sar_oil_spill_image(width=300, height=300, seed=42)
        res = process_marine_image(img, sensor_type="SAR")
        
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["sensor_modality"], "SAR")
        self.assertTrue(res["classification"]["is_spill_positive"])
        self.assertEqual(res["classification"]["verdict"], "OIL_SPILL_DETECTED")
        self.assertGreater(res["classification"]["confidence_score"], 70.0)
        self.assertGreater(res["bonn_metrics"]["spill_area_km2"], 0.0)
        self.assertGreater(res["bonn_metrics"]["estimated_volume_m3"], 0.0)
        self.assertIn("data:image/png;base64,", res["visual_overlay_url"])

    def test_clean_ocean_sar(self):
        """Test that clean ocean SAR does not trigger false positive."""
        img = generate_clean_ocean_sar_image(width=300, height=300, seed=12)
        res = process_marine_image(img, sensor_type="SAR")
        
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["classification"]["is_spill_positive"])
        self.assertEqual(res["classification"]["verdict"], "NO_SPILL_CLEAN")

    def test_algal_bloom_lookalike_rejection(self):
        """Test that biogenic algal bloom is classified as look-alike rather than oil spill."""
        img = generate_algal_bloom_image(width=300, height=300, seed=88)
        res = process_marine_image(img, sensor_type="OPTICAL")
        
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["classification"]["is_spill_positive"])
        self.assertEqual(res["classification"]["verdict"], "LOOKALIKE_ALGAL_BLOOM")

    def test_drone_optical_slick_detection(self):
        """Test detection on drone aerial optical RGB imagery."""
        img = generate_drone_optical_slick_image(width=300, height=300, seed=200)
        res = process_marine_image(img, sensor_type="OPTICAL")
        
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["classification"]["is_spill_positive"])
        self.assertEqual(res["classification"]["verdict"], "OIL_SPILL_DETECTED")

    def test_bonn_agreement_calculations(self):
        """Test Bonn Agreement volume math."""
        # 10 km2 of Metallic slick (code 3 = 25 m3/km2 nominal)
        metrics = calculate_bonn_metrics(spill_area_km2=10.0, bonn_code=3)
        self.assertEqual(metrics["bonn_code"], 3)
        self.assertAlmostEqual(metrics["estimated_volume_m3"], 250.0, places=1)
        self.assertGreater(metrics["estimated_volume_bbl"], 1500.0)
        self.assertEqual(metrics["severity_class"], "warning")

    def test_lagrangian_drift_simulation(self):
        """Test 72-hour drift trajectory physics."""
        sim = simulate_oil_drift(
            origin_lat=28.0,
            origin_lon=-88.0,
            wind_speed_knots=15.0,
            wind_direction_deg=180.0,  # South wind blowing North
            current_speed_knots=1.0,
            current_direction_deg=0.0,  # Northward current
            spill_area_km2=10.0,
            spill_volume_m3=200.0,
            simulation_hours=72,
            time_step_hours=12
        )
        
        self.assertIn("trajectory", sim)
        self.assertEqual(len(sim["trajectory"]), 7)  # T+0, 12, 24, 36, 48, 60, 72
        self.assertGreater(sim["total_distance_72h_km"], 10.0)
        # Lat should have increased northward
        dest_lat = sim["destination_72h_coordinates"][0]
        self.assertGreater(dest_lat, 28.0)
        # Check evaporation weathering
        weathering = sim["weathering"]
        self.assertGreater(weathering[-1]["evaporated_percent"], 20.0)

if __name__ == "__main__":
    unittest.main()
