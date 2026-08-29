"""
Lagrangian Ocean Drift & Weathering Trajectory Simulator
Simulates the 24h/48h/72h advection, turbulent diffusion, Coriolis deflection,
and weathering degradation (evaporation, emulsification) of marine oil spills.
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple

def simulate_oil_drift(
    origin_lat: float,
    origin_lon: float,
    wind_speed_knots: float = 14.0,
    wind_direction_deg: float = 225.0,  # Direction wind is blowing FROM (degrees true)
    current_speed_knots: float = 1.2,
    current_direction_deg: float = 65.0,  # Direction current is flowing TO
    spill_area_km2: float = 12.5,
    spill_volume_m3: float = 250.0,
    oil_api_gravity: float = 32.0,  # Medium Crude
    simulation_hours: int = 72,
    time_step_hours: int = 6
) -> Dict[str, Any]:
    """
    Simulate oil slick advection trajectory and physical weathering over time.
    
    Advection Velocity Vector = V_current + 0.033 * V_wind (with Coriolis deflection)
    """
    # Windage coefficient is standard 3.3% of 10m wind velocity
    windage_coeff = 0.033
    
    # Wind direction conversion: Wind direction is usually "from", so "blowing towards" is +180 deg
    wind_towards_deg = (wind_direction_deg + 180.0) % 360.0
    
    # Coriolis deflection angle: In Northern Hemisphere (>0 lat), wind drift deflects ~12 deg to the right (+12 deg)
    coriolis_deflection = 12.0 if origin_lat >= 0 else -12.0
    effective_wind_deg = (wind_towards_deg + coriolis_deflection) % 360.0
    
    # Convert knots to km/h (1 knot = 1.852 km/h)
    u_wind_kmh = (wind_speed_knots * 1.852 * windage_coeff) * math.sin(math.radians(effective_wind_deg))
    v_wind_kmh = (wind_speed_knots * 1.852 * windage_coeff) * math.cos(math.radians(effective_wind_deg))
    
    u_curr_kmh = (current_speed_knots * 1.852) * math.sin(math.radians(current_direction_deg))
    v_curr_kmh = (current_speed_knots * 1.852) * math.cos(math.radians(current_direction_deg))
    
    # Net drift vector (km/h)
    u_net = u_curr_kmh + u_wind_kmh
    v_net = v_curr_kmh + v_wind_kmh
    net_speed_kmh = math.sqrt(u_net ** 2 + v_net ** 2)
    net_bearing_deg = (math.degrees(math.atan2(u_net, v_net)) + 360.0) % 360.0
    
    # 1 deg latitude is approx 111.32 km
    # 1 deg longitude is approx 111.32 * cos(lat) km
    km_per_lat_deg = 111.32
    km_per_lon_deg = 111.32 * math.cos(math.radians(origin_lat))
    if abs(km_per_lon_deg) < 1e-4:
        km_per_lon_deg = 1e-4

    trajectory_points = []
    weathering_timeline = []
    
    current_lat = origin_lat
    current_lon = origin_lon
    
    # Weathering coefficients for evaporation & emulsification
    # Evaporation: M(t) = M0 * (1 - 0.45 * (1 - exp(-0.06 * t)))
    evap_rate = 0.05 + (wind_speed_knots / 100.0) * 0.04
    
    cumulative_dist_km = 0.0
    
    for h in range(0, simulation_hours + 1, time_step_hours):
        if h > 0:
            delta_dist_km = net_speed_kmh * time_step_hours
            cumulative_dist_km += delta_dist_km
            
            delta_lat = (v_net * time_step_hours) / km_per_lat_deg
            delta_lon = (u_net * time_step_hours) / km_per_lon_deg
            
            current_lat += delta_lat
            current_lon += delta_lon
            
        # Physical weathering
        # Evaporated percentage
        evap_percent = min(58.0, 100.0 * (1.0 - math.exp(-evap_rate * h))) if h > 0 else 0.0
        remaining_vol_m3 = spill_volume_m3 * (1.0 - (evap_percent / 100.0))
        
        # Emulsification increases water content up to ~65-75% for crude mousse
        water_content_pct = min(70.0, 100.0 * (1.0 - math.exp(-0.03 * h))) if h > 0 else 0.0
        
        # Dispersion spreading radius (Fay gravity-viscous regime expansion)
        spread_radius_km = math.sqrt(max(spill_area_km2, 0.1) / math.pi) + (0.08 * (h ** 0.6))
        dispersed_area_km2 = math.pi * (spread_radius_km ** 2)
        
        # Particle ensemble bounding cloud (4 corner variance points for polygon visualization)
        disp_lat_offset = spread_radius_km / km_per_lat_deg
        disp_lon_offset = spread_radius_km / km_per_lon_deg
        
        cloud_polygon = [
            [round(current_lat + disp_lat_offset, 5), round(current_lon, 5)],
            [round(current_lat, 5), round(current_lon + disp_lon_offset, 5)],
            [round(current_lat - disp_lat_offset, 5), round(current_lon, 5)],
            [round(current_lat, 5), round(current_lon - disp_lon_offset, 5)]
        ]
        
        trajectory_points.append({
            "hour": h,
            "timestamp_offset": f"T+{h:02d}h",
            "lat": round(current_lat, 5),
            "lon": round(current_lon, 5),
            "cumulative_distance_km": round(cumulative_dist_km, 2),
            "cloud_radius_km": round(spread_radius_km, 2),
            "cloud_polygon": cloud_polygon
        })
        
        weathering_timeline.append({
            "hour": h,
            "evaporated_percent": round(evap_percent, 1),
            "water_emulsification_percent": round(water_content_pct, 1),
            "remaining_volume_m3": round(remaining_vol_m3, 1),
            "dispersed_area_km2": round(dispersed_area_km2, 2)
        })

    # Shoreline risk assessment
    total_travel_km = round(cumulative_dist_km, 2)
    estimated_speed_knots = round(net_speed_kmh / 1.852, 2)
    
    return {
        "origin_coordinates": [round(origin_lat, 5), round(origin_lon, 5)],
        "destination_72h_coordinates": [round(current_lat, 5), round(current_lon, 5)],
        "drift_speed_kmh": round(net_speed_kmh, 2),
        "drift_speed_knots": estimated_speed_knots,
        "drift_bearing_deg": round(net_bearing_deg, 1),
        "total_distance_72h_km": total_travel_km,
        "wind_vector": {
            "speed_knots": wind_speed_knots,
            "direction_from_deg": wind_direction_deg,
            "drift_component_kmh": round(math.sqrt(u_wind_kmh**2 + v_wind_kmh**2), 2)
        },
        "current_vector": {
            "speed_knots": current_speed_knots,
            "direction_to_deg": current_direction_deg,
            "drift_component_kmh": round(math.sqrt(u_curr_kmh**2 + v_curr_kmh**2), 2)
        },
        "trajectory": trajectory_points,
        "weathering": weathering_timeline
    }
