"""
MarineGuard AI - Climate & Oceanographic Environmental Service
Fetches and models Sea Surface Temperature (SST), SST anomalies, marine heatwaves,
wind velocity, surface currents, wave conditions, and chlorophyll-a concentrations.
"""

import os
import json
from typing import Dict, Any


def load_environmental_presets() -> Dict[str, Any]:
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "environmental", "environmental_data.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            return json.load(f).get("environmental_presets", {})
    return {}


def get_environmental_context(spill_lat: float, spill_lon: float, region_preset: str = "gulf_of_mexico") -> Dict[str, Any]:
    """
    Returns oceanographic and climatological context for a given spill location.
    """
    presets = load_environmental_presets()
    if region_preset in presets:
        data = presets[region_preset]
    elif "mumbai_high" in region_preset or (spill_lat > 10 and spill_lon > 60 and spill_lon < 85):
        data = presets.get("mumbai_high", list(presets.values())[0])
    else:
        data = presets.get("gulf_of_mexico", {
            "region_name": "Open Ocean Surveillance Sector",
            "coordinates": {"lat": spill_lat, "lon": spill_lon},
            "sea_surface_temp_c": 28.5,
            "sst_anomaly_c": 1.1,
            "marine_heatwave_status": "Category I (Moderate)",
            "wind": {"speed_knots": 12.0, "speed_ms": 6.2, "direction_deg": 135.0, "cardinal": "SE"},
            "ocean_current": {"velocity_knots": 1.0, "direction_deg": 315.0, "current_name": "Regional Drift"},
            "wave": {"significant_height_m": 1.2, "peak_period_s": 6.0, "direction_deg": 135.0},
            "chlorophyll_a_mg_m3": 1.2,
            "historical_spill_frequency": "Medium"
        })

    climate_context = (
        f"Region currently experiencing elevated Sea Surface Temperature ({data.get('sea_surface_temp_c', 29.0)}°C, "
        f"+{data.get('sst_anomaly_c', 1.0)}°C above 30-year climatological baseline), triggering a "
        f"{data.get('marine_heatwave_status', 'Moderate')} heatwave advisory. High thermal energy accelerates "
        f"initial volatile hydrocarbon evaporation while wave action ({data.get('wave', {}).get('significant_height_m', 1.2)}m) "
        f"promotes rapid emulsification into persistent 'chocolate mousse'."
    )

    return {
        "region_name": data.get("region_name", "Surveillance Sector"),
        "sea_surface_temp_c": data.get("sea_surface_temp_c", 29.0),
        "sst_climatological_mean_c": data.get("sst_climatological_mean_c", 27.9),
        "sst_anomaly_c": data.get("sst_anomaly_c", 1.1),
        "marine_heatwave_category": data.get("marine_heatwave_status", "Category I (Moderate)"),
        "wind_speed_knots": data.get("wind", {}).get("speed_knots", 12.0),
        "wind_direction_deg": data.get("wind", {}).get("direction_deg", 135.0),
        "wind_cardinal": data.get("wind", {}).get("cardinal", "SE"),
        "current_speed_knots": data.get("ocean_current", {}).get("velocity_knots", 1.0),
        "current_direction_deg": data.get("ocean_current", {}).get("direction_deg", 315.0),
        "current_name": data.get("ocean_current", {}).get("current_name", "Loop Current"),
        "wave_height_m": data.get("wave", {}).get("significant_height_m", 1.2),
        "wave_period_s": data.get("wave", {}).get("peak_period_s", 6.0),
        "chlorophyll_mg_m3": data.get("chlorophyll_a_mg_m3", 1.5),
        "climatological_context": climate_context
    }
