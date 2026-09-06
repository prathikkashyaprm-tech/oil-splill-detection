"""
MarineGuard AI - Demo Scenarios & Preset Incident Engine
Provides preloaded, benchmark-validated scenarios for SIH 2026 PS-1655 demonstrations:
1. NOAA Gulf of Mexico Tanker Incident (Mississippi Canyon Block)
2. Sentinel-1 Arabian Sea / Mumbai High Offshore Spill
3. Strait of Malacca Tanker Discharge
4. Red Sea Bab-el-Mandeb Transit Spill
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from backend.app.services.vessel_behavior import rank_candidate_vessels
from backend.app.services.trajectory_simulator import simulate_oil_spill_trajectory
from backend.app.services.ecological_service import assess_ecological_impact
from backend.app.services.environmental_service import get_environmental_context
from backend.app.services.evidence_fusion import synthesize_evidence_dossier


def load_ais_scenarios() -> List[Dict[str, Any]]:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ais", "ais_sample_data.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f).get("scenarios", [])
    return []


def build_demo_scenario(scenario_id: str = "demo_gulf_of_mexico") -> Dict[str, Any]:
    scenarios = load_ais_scenarios()
    scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), scenarios[0] if scenarios else None)

    if not scenario:
        # Fallback default
        center_lat, center_lon = 28.7350, -88.3820
        vessels = []
        name = "NOAA Gulf of Mexico Incident"
        region = "Gulf of Mexico"
    else:
        center_lat = scenario["spill_location"]["lat"]
        center_lon = scenario["spill_location"]["lon"]
        vessels = scenario.get("vessels", [])
        name = scenario["name"]
        region = scenario["region"]

    incident_id = f"MG-2026-{scenario_id.split('_')[-1].upper()[:4]}"

    # 1. Base Spill Detection & Polygon
    # Generate realistic polygon around spill location
    coords = []
    num_pts = 12
    r_lat = 0.04
    r_lon = 0.06
    for i in range(num_pts):
        angle = (i / num_pts) * 2 * 3.14159
        # Irregular shape
        factor = 0.7 + 0.5 * ((i * 7) % 5) / 5.0
        lat = center_lat + r_lat * factor * 3.14159 * 0.3 * (1.0 if i % 2 == 0 else 0.6)
        lon = center_lon + r_lon * factor * 3.14159 * 0.3 * (0.8 if i % 3 == 0 else 1.1)
        coords.append([round(lon, 5), round(lat, 5)])
    coords.append(coords[0])

    spill_area_km2 = 42.5 if "gulf" in scenario_id else 58.0 if "mumbai" in scenario_id else 28.0
    thickness_um = 25.0
    est_vol_m3 = (spill_area_km2 * 1e6) * (thickness_um * 1e-6)
    est_vol_bbl = est_vol_m3 * 6.2898

    spill_detection = {
        "id": f"SPILL_{incident_id}",
        "timestamp": datetime.utcnow().isoformat(),
        "source_satellite": "Sentinel-1 C-Band SAR / NOAA NESDIS",
        "center_latitude": center_lat,
        "center_longitude": center_lon,
        "spill_polygon_geojson": {
            "type": "Polygon",
            "coordinates": [coords]
        },
        "confidence_score": 0.94,
        "affected_area_km2": spill_area_km2,
        "estimated_volume_m3": round(est_vol_m3, 2),
        "estimated_volume_bbl": round(est_vol_bbl, 1),
        "bonn_code": 3,
        "bonn_description": "Code 3: Metallic Sheen to Heavy True Oil",
        "nominal_thickness_um": thickness_um,
        "slick_classification": "Mineral Oil Spill",
        "raw_image_url": "/static/samples/noaa_sar_gulf_sample.png",
        "mask_image_url": "/static/samples/noaa_sar_gulf_mask.png"
    }

    # 2. Environmental Context
    preset_key = "mumbai_high" if "mumbai" in scenario_id else "gulf_of_mexico"
    env_record = get_environmental_context(center_lat, center_lon, preset_key)

    # 3. AIS Candidate Ranking
    ranked_candidates = rank_candidate_vessels(vessels, center_lat, center_lon)

    # 4. Trajectory Simulation
    trajectories = simulate_oil_spill_trajectory(
        origin_lat=center_lat,
        origin_lon=center_lon,
        spill_polygon=spill_detection["spill_polygon_geojson"],
        wind_speed_knots=env_record["wind_speed_knots"],
        wind_direction_deg=env_record["wind_direction_deg"],
        current_speed_knots=env_record["current_speed_knots"],
        current_direction_deg=env_record["current_direction_deg"],
        detection_time=datetime.utcnow()
    )

    # 5. Ecological Assessment
    eco_assessment = assess_ecological_impact(center_lat, center_lon, spill_area_km2, trajectories)

    # 6. Evidence Fusion
    dossier = synthesize_evidence_dossier(
        incident_id=incident_id,
        spill_detection=spill_detection,
        candidate_vessels=ranked_candidates,
        trajectories=trajectories,
        ecological_assessment=eco_assessment,
        environmental_record=env_record
    )

    return {
        "scenario_id": scenario_id,
        "scenario_name": name,
        "region": region,
        "incident_id": incident_id,
        "spill_detection": spill_detection,
        "candidate_vessels": ranked_candidates,
        "trajectories": trajectories,
        "ecological_assessment": eco_assessment,
        "environmental_record": env_record,
        "evidence_dossier": dossier,
        "demo_mode": True
    }


def list_available_scenarios() -> List[Dict[str, str]]:
    return [
        {
            "id": "demo_gulf_of_mexico",
            "title": "NOAA Gulf of Mexico Tanker Incident (Mississippi Canyon)",
            "region": "Northern Gulf of Mexico",
            "lat": 28.7350,
            "lon": -88.3820,
            "vessels_count": 3,
            "severity": "HIGH"
        },
        {
            "id": "demo_mumbai_high",
            "title": "Sentinel-1 Arabian Sea / Mumbai High Offshore Spill",
            "region": "Arabian Sea Offshore Hub",
            "lat": 19.4200,
            "lon": 71.3300,
            "vessels_count": 2,
            "severity": "CRITICAL"
        }
    ]
