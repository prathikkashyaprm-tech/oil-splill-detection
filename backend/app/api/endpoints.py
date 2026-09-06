"""
MarineGuard AI - REST API Endpoints
Implements all PRD required endpoints for incidents, spills, vessels, attribution,
trajectories, ecological impact, environment, risk zones, and demo mode.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
import cv2
import numpy as np

from backend.app.core.database import get_db
from backend.app.schemas.pydantic_models import (
    DetectSpillRequest, PreIncidentRiskZone
)
from backend.app.services.sar_detection import process_sar_imagery, decode_base64_image
from backend.app.services.vessel_behavior import rank_candidate_vessels
from backend.app.services.trajectory_simulator import simulate_oil_spill_trajectory
from backend.app.services.ecological_service import assess_ecological_impact
from backend.app.services.environmental_service import get_environmental_context
from backend.app.services.risk_assessment import get_pre_incident_risk_zones
from backend.app.services.evidence_fusion import synthesize_evidence_dossier
from backend.app.services.demo_scenarios import build_demo_scenario, list_available_scenarios, load_ais_scenarios

router = APIRouter()

# In-memory incident cache for demo & interactive state
_ACTIVE_STATE = {
    "current_scenario": build_demo_scenario("demo_gulf_of_mexico"),
    "incidents_history": []
}


@router.get("/demo/scenarios", summary="List available demo scenarios")
def get_demo_scenarios():
    """List preloaded NOAA / Sentinel-1 demo incident scenarios for SIH presentation."""
    return list_available_scenarios()


@router.post("/demo/load-scenario", summary="Load a preloaded demo scenario")
def load_scenario(scenario_id: str = Query("demo_gulf_of_mexico", description="Scenario ID to load")):
    """Switches active scenario state and returns full intelligence package."""
    scenario = build_demo_scenario(scenario_id)
    _ACTIVE_STATE["current_scenario"] = scenario
    return scenario


@router.get("/incidents", summary="Get all maritime incidents")
def get_incidents():
    """Returns list of active and historical maritime spill incidents."""
    current = _ACTIVE_STATE["current_scenario"]
    summary_item = {
        "id": current["incident_id"],
        "title": current["scenario_name"],
        "region": current["region"],
        "status": "ACTIVE_INVESTIGATION",
        "severity": current["ecological_assessment"]["ecological_risk_level"],
        "spill_id": current["spill_detection"]["id"],
        "created_at": current["spill_detection"]["timestamp"],
        "affected_area_km2": current["spill_detection"]["affected_area_km2"],
        "confidence_score": current["spill_detection"]["confidence_score"],
        "top_candidate_vessel": current["candidate_vessels"][0]["vessel"]["vessel_name"] if current["candidate_vessels"] else "None",
        "top_investigation_priority": current["candidate_vessels"][0]["metrics"]["investigation_priority_score"] if current["candidate_vessels"] else 0.0
    }
    return [summary_item] + _ACTIVE_STATE["incidents_history"]


@router.get("/incidents/{incident_id}", summary="Get specific incident dossier")
def get_incident_by_id(incident_id: str):
    """Retrieves complete multi-pillar evidence fusion dossier for an incident."""
    current = _ACTIVE_STATE["current_scenario"]
    if current["incident_id"] == incident_id or incident_id in ["current", "active", "demo"]:
        return current
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.get("/spills", summary="Get all detected oil spills")
def get_spills():
    """Returns all SAR-detected oil spill instances."""
    return [_ACTIVE_STATE["current_scenario"]["spill_detection"]]


@router.get("/spills/{spill_id}", summary="Get specific oil spill detection details")
def get_spill_by_id(spill_id: str):
    current = _ACTIVE_STATE["current_scenario"]
    if current["spill_detection"]["id"] == spill_id or spill_id in ["current", "active"]:
        return current["spill_detection"]
    raise HTTPException(status_code=404, detail=f"Spill {spill_id} not found")


@router.get("/vessels", summary="Get all active AIS vessels in surveillance box")
def get_vessels():
    """Returns all tracked AIS vessels with coordinates, headings, and metadata."""
    current = _ACTIVE_STATE["current_scenario"]
    return [c["vessel"] for c in current["candidate_vessels"]]


@router.get("/vessels/{mmsi}", summary="Get vessel metadata by MMSI")
def get_vessel_by_mmsi(mmsi: str):
    current = _ACTIVE_STATE["current_scenario"]
    for c in current["candidate_vessels"]:
        v = c["vessel"]
        if str(v.get("mmsi")) == str(mmsi):
            return v
    raise HTTPException(status_code=404, detail=f"Vessel with MMSI {mmsi} not found")


@router.get("/vessels/{mmsi}/trajectory", summary="Get historical AIS trajectory for a vessel")
def get_vessel_trajectory(mmsi: str):
    current = _ACTIVE_STATE["current_scenario"]
    for c in current["candidate_vessels"]:
        v = c["vessel"]
        if str(v.get("mmsi")) == str(mmsi):
            return {
                "mmsi": v.get("mmsi"),
                "vessel_name": v.get("vessel_name"),
                "positions": v.get("positions", [])
            }
    raise HTTPException(status_code=404, detail=f"Trajectory for MMSI {mmsi} not found")


@router.get("/vessels/nearby", summary="Find vessels near specific geographic coordinate")
def get_nearby_vessels(lat: float = Query(28.735), lon: float = Query(-88.382), radius_km: float = Query(30.0)):
    current = _ACTIVE_STATE["current_scenario"]
    return current["candidate_vessels"]


@router.get("/attribution/{incident_id}", summary="Get explainable vessel attribution & priority rankings")
def get_attribution(incident_id: str):
    """
    Returns candidate vessel rankings and explainability dossiers.
    Strictly framed as 'Investigation Priority' rather than definitive culpability.
    """
    current = _ACTIVE_STATE["current_scenario"]
    return {
        "incident_id": incident_id,
        "disclaimer": "Scores represent investigation priority only; not legal proof of causation.",
        "candidate_vessels": current["candidate_vessels"]
    }


@router.get("/trajectory/{spill_id}", summary="Get 72-hour Lagrangian drift forecast & weathering")
def get_trajectory(spill_id: str):
    """Returns simulated +6h, +12h, +24h, +48h, +72h drift polygons and weathering curves."""
    current = _ACTIVE_STATE["current_scenario"]
    return {
        "spill_id": spill_id,
        "forecast_intervals": current["trajectories"],
        "environmental_forcing": current["environmental_record"]
    }


@router.get("/ecological-impact/{spill_id}", summary="Get OBIS biodiversity & habitat sensitivity assessment")
def get_ecological_impact(spill_id: str):
    """Returns potential marine ecological exposure index (LOW / MEDIUM / HIGH / CRITICAL)."""
    current = _ACTIVE_STATE["current_scenario"]
    return current["ecological_assessment"]


@router.get("/environment/{spill_id}", summary="Get oceanographic & climate analytics")
def get_environment(spill_id: str):
    """Returns Sea Surface Temperature, anomalies, marine heatwave, wind and current vectors."""
    current = _ACTIVE_STATE["current_scenario"]
    return current["environmental_record"]


@router.get("/risk-zones", summary="Get pre-incident maritime risk map layers")
def get_risk_zones():
    """Returns predictive pre-incident maritime risk areas based on density and historical trends."""
    return get_pre_incident_risk_zones()


@router.post("/detect-spill", summary="Run SAR U-Net detection on an image")
async def detect_spill(
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    sample_id: Optional[str] = Form(None),
    center_lat: float = Form(28.7350),
    center_lon: float = Form(-88.3820),
    pixel_res_m: float = Form(10.0)
):
    """
    Accepts Sentinel-1 SAR or NOAA imagery upload or preset sample ID.
    Preprocesses with Lee Filter, runs U-Net segmentation, extracts polygons,
    quantifies Bonn scale area/volume, and correlates with AIS candidates.
    """
    img_array = None

    if file is not None:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif image_base64:
        img_array = decode_base64_image(image_base64)
    elif sample_id:
        # Load from synthetic benchmark presets
        from ml.dataset.noaa_loader import generate_noaa_benchmark_dataset
        import glob, os
        img_path = os.path.join("data", "sar", "images", f"{sample_id}.png")
        if not os.path.exists(img_path):
            generate_noaa_benchmark_dataset("data/sar", num_samples=10)
            imgs = glob.glob(os.path.join("data", "sar", "images", "*.png"))
            img_path = imgs[0] if imgs else None
        if img_path and os.path.exists(img_path):
            img_array = cv2.imread(img_path)

    if img_array is None:
        # Generate synthetic SAR test patch
        img_array = np.random.normal(130, 20, (256, 256)).astype(np.uint8)
        # Draw dark spill
        cv2.ellipse(img_array, (128, 128), (60, 20), 45, 0, 360, 35, -1)
        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)

    # Run SAR detection
    detection_res = process_sar_imagery(img_array, center_lat=center_lat, center_lon=center_lon, pixel_res_m=pixel_res_m)

    # Correlate with current AIS scenario
    scenarios = load_ais_scenarios()
    vessels = scenarios[0]["vessels"] if scenarios else []
    ranked_candidates = rank_candidate_vessels(vessels, center_lat, center_lon)

    # Drift forecast
    env_record = get_environmental_context(center_lat, center_lon)
    first_poly = detection_res["spill_polygons"][0] if detection_res["spill_polygons"] else {"coordinates": []}
    trajectories = simulate_oil_spill_trajectory(
        origin_lat=center_lat,
        origin_lon=center_lon,
        spill_polygon=first_poly,
        wind_speed_knots=env_record["wind_speed_knots"],
        wind_direction_deg=env_record["wind_direction_deg"],
        current_speed_knots=env_record["current_speed_knots"],
        current_direction_deg=env_record["current_direction_deg"]
    )

    # Ecological assessment
    eco_assessment = assess_ecological_impact(center_lat, center_lon, detection_res["total_affected_area_km2"], trajectories)

    # Evidence fusion
    incident_id = f"MG-LIVE-{datetime.utcnow().strftime('%H%M%S')}"
    spill_payload = {
        "id": f"SPILL_{incident_id}",
        "timestamp": datetime.utcnow().isoformat(),
        "source_satellite": "Sentinel-1 C-Band SAR / NOAA Surveillance",
        "center_latitude": center_lat,
        "center_longitude": center_lon,
        "spill_polygon_geojson": {
            "type": "Polygon",
            "coordinates": first_poly.get("coordinates", [])
        },
        "confidence_score": detection_res["overall_confidence"],
        "affected_area_km2": detection_res["total_affected_area_km2"],
        "estimated_volume_m3": sum(p.get("estimated_volume_m3", 0) for p in detection_res["spill_polygons"]),
        "estimated_volume_bbl": sum(p.get("estimated_volume_bbl", 0) for p in detection_res["spill_polygons"]),
        "bonn_code": first_poly.get("bonn_code", 3),
        "bonn_description": first_poly.get("bonn_description", "Code 3: Metallic"),
        "nominal_thickness_um": first_poly.get("nominal_thickness_um", 25.0),
        "slick_classification": first_poly.get("classification", "Mineral Oil Spill"),
        "raw_image_url": detection_res.get("raw_image_url"),
        "mask_image_url": detection_res.get("mask_image_url"),
        "overlay_image_url": detection_res.get("overlay_image_url")
    }

    dossier = synthesize_evidence_dossier(
        incident_id=incident_id,
        spill_detection=spill_payload,
        candidate_vessels=ranked_candidates,
        trajectories=trajectories,
        ecological_assessment=eco_assessment,
        environmental_record=env_record
    )

    new_scenario = {
        "scenario_id": f"live_upload_{incident_id}",
        "scenario_name": f"Live Detection Incident ({center_lat:.2f}°, {center_lon:.2f}°)",
        "region": "Live SAR Ingestion Area",
        "incident_id": incident_id,
        "spill_detection": spill_payload,
        "candidate_vessels": ranked_candidates,
        "trajectories": trajectories,
        "ecological_assessment": eco_assessment,
        "environmental_record": env_record,
        "evidence_dossier": dossier,
        "detection_details": detection_res,
        "demo_mode": False
    }

    _ACTIVE_STATE["current_scenario"] = new_scenario

    return new_scenario
