"""
MarineGuard AI - 72-Hour Lagrangian Oil Spill Drift & Weathering Simulator
Calculates advection from wind & surface current vectors (including Coriolis deflection)
and physical weathering curves (evaporative decay % and emulsification water uptake %).
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List


def simulate_oil_spill_trajectory(
    origin_lat: float,
    origin_lon: float,
    spill_polygon: Dict[str, Any],
    wind_speed_knots: float,
    wind_direction_deg: float,
    current_speed_knots: float,
    current_direction_deg: float,
    detection_time: datetime = None,
    intervals_hours: List[int] = [6, 12, 24, 48, 72]
) -> List[Dict[str, Any]]:
    """
    Simulates Lagrangian trajectory steps and expanding polygon bounding cones.
    """
    if detection_time is None:
        detection_time = datetime.utcnow()

    # 1. Advection Vectors:
    # Oil drift = 100% Surface Current + 3.0% 10-meter Wind (with ~15 deg Coriolis deflection in NH)
    # Wind direction is "direction wind blows FROM", so drift is (wind_direction + 180 + 15) % 360
    wind_drift_angle_rad = math.radians((wind_direction_deg + 180.0 + 15.0) % 360.0)
    wind_drift_speed_knots = wind_speed_knots * 0.03  # 3% rule of thumb

    # Current direction is "direction current flows TO"
    current_angle_rad = math.radians(current_direction_deg)
    current_speed = current_speed_knots

    # Vector components in knots (1 knot = 1.852 km/h)
    u_total_kn = current_speed * math.sin(current_angle_rad) + wind_drift_speed_knots * math.sin(wind_drift_angle_rad)
    v_total_kn = current_speed * math.cos(current_angle_rad) + wind_drift_speed_knots * math.cos(wind_drift_angle_rad)

    # Speed in km/h
    drift_speed_kmh = math.sqrt(u_total_kn**2 + v_total_kn**2) * 1.852
    drift_bearing_deg = (math.degrees(math.atan2(u_total_kn, v_total_kn)) + 360.0) % 360.0

    forecast_steps = []
    coords_list = spill_polygon.get("coordinates", [])
    base_coords = coords_list[0] if (coords_list and len(coords_list) > 0 and len(coords_list[0]) > 0) else []

    for t_hours in intervals_hours:
        # Distance traveled in km
        total_dist_km = drift_speed_kmh * t_hours
        
        # Approximate delta lat/lon
        # 1 deg lat = 111.0 km
        delta_lat = (total_dist_km * math.cos(math.radians(drift_bearing_deg))) / 111.0
        delta_lon = (total_dist_km * math.sin(math.radians(drift_bearing_deg))) / (111.0 * max(0.1, math.cos(math.radians(origin_lat))))

        step_lat = round(origin_lat + delta_lat, 6)
        step_lon = round(origin_lon + delta_lon, 6)
        step_time = detection_time + timedelta(hours=t_hours)

        # Weathering calculations (Mackay / ADIOS model approximations)
        # Evaporative fraction % increases logarithmically
        evap_pct = min(68.0, 15.0 * math.log(1.0 + 0.8 * t_hours) + (wind_speed_knots * 0.4))
        # Emulsification water uptake % increases asymptotically to ~75-80%
        emuls_pct = min(78.0, 80.0 * (1.0 - math.exp(-0.06 * t_hours)))

        # Expanding turbulent dispersion radius (Fay spread)
        dispersion_scale = 1.0 + 0.15 * math.sqrt(t_hours)

        # Project transformed polygon
        step_coords = []
        if base_coords:
            for pt in base_coords:
                pt_lon, pt_lat = pt[0], pt[1]
                # Shift and slightly expand
                c_lon = step_lon + (pt_lon - origin_lon) * dispersion_scale
                c_lat = step_lat + (pt_lat - origin_lat) * dispersion_scale
                step_coords.append([round(float(c_lon), 6), round(float(c_lat), 6)])
        else:
            # Generate elliptical bounding box if no base coords
            r_deg = (1.5 * dispersion_scale) / 111.0
            for ang in range(0, 360, 30):
                rad = math.radians(ang)
                step_coords.append([round(step_lon + r_deg * math.sin(rad), 6), round(step_lat + r_deg * math.cos(rad), 6)])
            step_coords.append(step_coords[0])

        # Coastal proximity / impact alert check (e.g. if approaching lat > 29.2 in Gulf)
        coastal_hit = False
        coastal_eta = None
        if origin_lat < 29.0 and step_lat >= 29.25:
            coastal_hit = True
            coastal_eta = t_hours

        forecast_steps.append({
            "forecast_hours": t_hours,
            "forecast_timestamp": step_time.isoformat(),
            "center_latitude": step_lat,
            "center_longitude": step_lon,
            "wind_drift_km": round(wind_drift_speed_knots * 1.852 * t_hours, 2),
            "current_drift_km": round(current_speed * 1.852 * t_hours, 2),
            "total_drift_km": round(total_dist_km, 2),
            "drift_bearing_deg": round(drift_bearing_deg, 1),
            "drift_speed_kmh": round(drift_speed_kmh, 2),
            "evaporated_fraction_pct": round(evap_pct, 1),
            "emulsified_water_pct": round(emuls_pct, 1),
            "coastal_hit_warning": coastal_hit,
            "coastal_eta_hours": coastal_eta,
            "predicted_polygon_geojson": {
                "type": "Polygon",
                "coordinates": [step_coords]
            }
        })

    return forecast_steps
