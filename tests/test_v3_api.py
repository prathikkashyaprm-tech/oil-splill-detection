import unittest
from fastapi.testclient import TestClient
from app import app

class TestMarineAIv3API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dashboard_stats(self):
        resp = self.client.get("/api/dashboard/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["active_incidents"], 3)
        self.assertEqual(data["high_risk_vessels"], 7)
        self.assertEqual(data["spills_detected"], 5)
        self.assertEqual(data["total_area_affected"], 12.48)

    def test_ais_vessels_and_track(self):
        resp = self.client.get("/api/ais/vessels")
        self.assertEqual(resp.status_code, 200)
        vessels = resp.json()
        self.assertGreater(len(vessels), 0)

        # Track endpoint
        resp_track = self.client.get("/api/ais/track/419001234")
        self.assertEqual(resp_track.status_code, 200)
        track_data = resp_track.json()
        self.assertEqual(track_data["mmsi"], 419001234)
        self.assertGreater(len(track_data["positions"]), 0)

    def test_anomaly_fleet(self):
        resp = self.client.get("/api/anomaly/fleet")
        self.assertEqual(resp.status_code, 200)
        reports = resp.json()
        self.assertGreater(len(reports), 0)
        vessel_a = next(r for r in reports if r["mmsi"] == 419001234)
        self.assertEqual(vessel_a["risk_level"], "HIGH")

    def test_incidents_and_attribution(self):
        resp = self.client.get("/api/incidents")
        self.assertEqual(resp.status_code, 200)
        incidents = resp.json()
        self.assertEqual(len(incidents), 3)

        # Detail
        resp_detail = self.client.get("/api/incidents/INC-2025-05-20-01")
        self.assertEqual(resp_detail.status_code, 200)
        inc = resp_detail.json()
        self.assertEqual(inc["id"], "INC-2025-05-20-01")

        # Attribution
        resp_attr = self.client.get("/api/incidents/INC-2025-05-20-01/attribution")
        self.assertEqual(resp_attr.status_code, 200)
        attrs = resp_attr.json()
        self.assertGreater(len(attrs), 0)
        self.assertEqual(attrs[0]["mmsi"], 419001234)
        self.assertEqual(attrs[0]["combined_score"], 91)

    def test_alerts_and_response(self):
        resp = self.client.get("/api/alerts")
        self.assertEqual(resp.status_code, 200)
        alerts = resp.json()
        self.assertGreater(len(alerts), 0)

        # Response recommendations
        resp_rec = self.client.get("/api/incidents/INC-2025-05-20-01/response")
        self.assertEqual(resp_rec.status_code, 200)
        recs = resp_rec.json()
        self.assertGreater(len(recs), 0)

    def test_report_generation(self):
        resp = self.client.post("/api/report/INC-2025-05-20-01")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Investigation Report", resp.text)
        self.assertIn("MT SHIVALIK", resp.text)

    def test_root_serves_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("MARINEGUARD AI", resp.text)

if __name__ == "__main__":
    unittest.main()
