"""
MarineGuard AI - Vessel Behavior Analysis & Investigation Priority Scorer
Calculates kinematic anomalies (speed drops, heading zigzags, loitering, course deviation)
and synthesizes an explainable Investigation Priority Score (0-100).

IMPORTANT ETHICAL DIRECTIVE:
Does NOT assert definitive culpability; outputs strictly "Investigation Priority",
"Candidate Vessel", and "Association Confidence".
"""

import math
from typing import List, Dict, Any


def compute_vessel_behavior_metrics(vessel_record: Dict[str, Any], spill_lat: float, spill_lon: float) -> Dict[str, Any]:
    """
    Analyzes vessel trajectory to identify kinematic and behavioral anomalies.
    """
    positions = vessel_record.get("positions", [])
    sim_feat = vessel_record.get("simulated_features", {})

    if not positions and not sim_feat:
        return {
            "investigation_priority_score": 10.0,
            "min_distance_km": 50.0,
            "speed_anomaly_drop_kn": 0.0,
            "route_deviation_deg": 0.0,
            "time_in_spill_zone_min": 0.0,
            "temporal_overlap_rating": "LOW",
            "anomaly_flags": []
        }

    # 1. Proximity Feature
    min_dist = sim_feat.get("min_distance_km", 999.0)
    if min_dist == 999.0 and positions:
        from backend.app.services.ais_service import calculate_haversine_distance_km
        distances = [calculate_haversine_distance_km(p["lat"], p["lon"], spill_lat, spill_lon) for p in positions]
        min_dist = min(distances) if distances else 50.0

    # 2. Speed Anomaly Feature
    speed_drop = sim_feat.get("speed_anomaly_drop_knots", 0.0)
    if speed_drop == 0.0 and len(positions) >= 2:
        speeds = [p.get("sog_knots", 0.0) for p in positions if p.get("sog_knots") is not None]
        if speeds:
            max_spd = max(speeds)
            min_spd = min(speeds)
            speed_drop = max(0.0, max_spd - min_spd)

    # 3. Route Deviation / Course Variance Feature
    route_dev = sim_feat.get("route_deviation_deg", 0.0)
    if route_dev == 0.0 and len(positions) >= 3:
        headings = [p.get("cog_deg", 0.0) for p in positions if p.get("cog_deg") is not None]
        if len(headings) >= 2:
            heading_diffs = [abs(headings[i] - headings[i-1]) for i in range(1, len(headings))]
            route_dev = max(heading_diffs) if heading_diffs else 0.0

    # 4. Loitering Time in Bounding Box
    time_in_zone = sim_feat.get("time_in_spill_zone_min", 0.0)

    # 5. Vessel Type Factor (Crude tankers / chemical carriers carry higher oil volume risk)
    vessel_type = vessel_record.get("vessel_type", "").lower()
    if "tanker" in vessel_type or "crude" in vessel_type:
        type_risk_mult = 1.25
        type_risk_name = "High Risk Cargo Category (Liquid Bulk Hydrocarbons)"
    elif "chemical" in vessel_type or "bunker" in vessel_type:
        type_risk_mult = 1.15
        type_risk_name = "Medium-High Risk Cargo Category (Chemical / Fuel Oil)"
    elif "cargo" in vessel_type or "container" in vessel_type:
        type_risk_mult = 0.90
        type_risk_name = "Standard Risk Cargo Category (Bunker Fuel on board)"
    else:
        type_risk_mult = 0.80
        type_risk_name = "Low Risk Vessel Category (Offshore / Fishing / Tug)"

    # 6. Compute Sub-Component Priority Weights (Total = 100 max)
    # Distance score: closer -> higher score (up to 35 pts)
    # e.g., < 1km = 35 pts, 5km = 20 pts, > 25km = 0 pts
    dist_score = max(0.0, 35.0 * (1.0 - min(min_dist, 25.0) / 25.0))

    # Speed anomaly score: severe drop -> higher score (up to 25 pts)
    speed_score = min(25.0, (speed_drop / 12.0) * 25.0)

    # Route deviation score: erratic course change -> higher score (up to 20 pts)
    route_score = min(20.0, (route_dev / 60.0) * 20.0)

    # Loitering / dwell time near spill -> (up to 20 pts)
    loiter_score = min(20.0, (time_in_zone / 45.0) * 20.0)

    raw_priority = (dist_score + speed_score + route_score + loiter_score) * type_risk_mult
    priority_score = min(99.0, max(5.0, raw_priority))

    # Determine Temporal Overlap
    if min_dist < 3.0 and time_in_zone >= 15.0:
        temporal_overlap = "HIGH"
    elif min_dist < 10.0:
        temporal_overlap = "MEDIUM"
    else:
        temporal_overlap = "LOW"

    # Explainability breakdown tags
    anomaly_flags = []
    if min_dist < 2.0:
        anomaly_flags.append(f"Immediate Proximity: Passed within {min_dist:.2f} km of slick center")
    if speed_drop >= 5.0:
        anomaly_flags.append(f"Abrupt Speed Drop: Decelerated by {speed_drop:.1f} knots inside surveillance box")
    if route_dev >= 30.0:
        anomaly_flags.append(f"Course Deviation: Altered heading by {route_dev:.1f}° off navigation corridor")
    if time_in_zone >= 20.0:
        anomaly_flags.append(f"Extended Loitering: Remained within impact zone for {time_in_zone:.0f} minutes")

    return {
        "investigation_priority_score": round(priority_score, 1),
        "min_distance_km": round(min_dist, 2),
        "speed_anomaly_drop_kn": round(speed_drop, 1),
        "route_deviation_deg": round(route_dev, 1),
        "time_in_spill_zone_min": round(time_in_zone, 1),
        "temporal_overlap_rating": temporal_overlap,
        "type_risk_factor": type_risk_mult,
        "type_risk_description": type_risk_name,
        "score_breakdown": {
            "spatial_proximity_pts": round(dist_score, 1),
            "speed_anomaly_pts": round(speed_score, 1),
            "route_deviation_pts": round(route_score, 1),
            "loitering_duration_pts": round(loiter_score, 1)
        },
        "anomaly_flags": anomaly_flags,
        "disclaimer": "Automated behavioral ranking indicates investigation priority only. Does not establish legal causation."
    }


def rank_candidate_vessels(vessels_list: List[Dict[str, Any]], spill_lat: float, spill_lon: float) -> List[Dict[str, Any]]:
    """
    Ranks all candidate vessels by descending Investigation Priority Score.
    """
    scored_candidates = []

    for v in vessels_list:
        vessel_dict = v.get("vessel", v)
        metrics = compute_vessel_behavior_metrics(vessel_dict, spill_lat, spill_lon)
        scored_candidates.append({
            "vessel": vessel_dict,
            "metrics": metrics,
            "priority_score": metrics["investigation_priority_score"]
        })

    # Sort descending
    scored_candidates.sort(key=lambda x: x["priority_score"], reverse=True)

    # Assign ranks
    for idx, item in enumerate(scored_candidates):
        item["rank"] = idx + 1

    return scored_candidates
