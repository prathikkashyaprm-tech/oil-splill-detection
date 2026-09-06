"""
MarineGuard AI - AIS Ingestion & Spatio-Temporal Query Service
Handles vessel spatial queries, distance calculations, and track interpolation.
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from geopy.distance import geodesic


def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in kilometers"""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def find_candidate_vessels_near_spill(
    vessels_data: List[Dict[str, Any]],
    spill_lat: float,
    spill_lon: float,
    spill_radius_km: float = 30.0,
    time_window_hours: float = 12.0
) -> List[Dict[str, Any]]:
    """
    Spatially and temporally filters vessels that crossed within the bounding
    area of the oil slick around the time of detection.
    """
    candidates = []

    for v in vessels_data:
        positions = v.get("positions", [])
        if not positions:
            continue

        min_dist = float("inf")
        closest_point = None
        points_in_zone = 0

        for p in positions:
            dist = calculate_haversine_distance_km(p["lat"], p["lon"], spill_lat, spill_lon)
            if dist < min_dist:
                min_dist = dist
                closest_point = p
            if dist <= spill_radius_km:
                points_in_zone += 1

        if min_dist <= spill_radius_km or points_in_zone > 0:
            candidates.append({
                "vessel": v,
                "min_distance_km": round(min_dist, 2),
                "closest_point": closest_point,
                "points_in_zone": points_in_zone
            })

    return candidates
