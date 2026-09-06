"""
MarineGuard AI - Pre-Incident Maritime Risk Assessment Service
Generates predictive maritime risk zones based on historical shipping density,
tanker route congestion, weather severity, and ecological proximity.
"""

from typing import List, Dict, Any


def get_pre_incident_risk_zones() -> List[Dict[str, Any]]:
    """
    Returns geographical risk zones with quantified vulnerability and risk ratings.
    """
    zones = [
        {
            "zone_id": "RISK_GOM_01",
            "zone_name": "Mississippi Canyon - High Density Tanker Corridor",
            "risk_level": "HIGH",
            "composite_risk_score": 84.5,
            "traffic_density_ships_per_day": 142,
            "tanker_percentage": 46.5,
            "weather_severity": "Moderate (Convective squalls)",
            "center": {"lat": 28.70, "lon": -88.40},
            "radius_km": 45.0,
            "recommended_patrol": "Frequent SAR & Coast Guard Aerial Reconnaissance",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-88.80, 28.40],
                    [-88.00, 28.40],
                    [-88.00, 29.00],
                    [-88.80, 29.00],
                    [-88.80, 28.40]
                ]]
            }
        },
        {
            "zone_id": "RISK_IND_01",
            "zone_name": "Mumbai High Offshore Extraction & Tanker Choke Point",
            "risk_level": "CRITICAL",
            "composite_risk_score": 91.2,
            "traffic_density_ships_per_day": 210,
            "tanker_percentage": 58.0,
            "weather_severity": "Severe (Monsoon Swells)",
            "center": {"lat": 19.40, "lon": 71.30},
            "radius_km": 60.0,
            "recommended_patrol": "Continuous AIS Anomaly Monitoring & Satellite Tasking",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [70.80, 19.00],
                    [71.80, 19.00],
                    [71.80, 19.80],
                    [70.80, 19.80],
                    [70.80, 19.00]
                ]]
            }
        },
        {
            "zone_id": "RISK_MALACCA_01",
            "zone_name": "Strait of Malacca - Supertanker Transit Channel",
            "risk_level": "HIGH",
            "composite_risk_score": 88.0,
            "traffic_density_ships_per_day": 340,
            "tanker_percentage": 38.0,
            "weather_severity": "Low-Moderate (Squalls)",
            "center": {"lat": 2.45, "lon": 101.88},
            "radius_km": 50.0,
            "recommended_patrol": "Multinational Coordinated Coastal Radar & AIS",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [101.40, 2.10],
                    [102.30, 2.10],
                    [102.30, 2.80],
                    [101.40, 2.80],
                    [101.40, 2.10]
                ]]
            }
        },
        {
            "zone_id": "RISK_REDSEA_01",
            "zone_name": "Southern Red Sea Shipping Lane",
            "risk_level": "MEDIUM",
            "composite_risk_score": 68.4,
            "traffic_density_ships_per_day": 95,
            "tanker_percentage": 42.0,
            "weather_severity": "Moderate (Strong northerly winds)",
            "center": {"lat": 15.50, "lon": 41.80},
            "radius_km": 55.0,
            "recommended_patrol": "Satellite Synthetic Aperture Radar Tracking",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [41.20, 15.00],
                    [42.40, 15.00],
                    [42.40, 16.00],
                    [41.20, 16.00],
                    [41.20, 15.00]
                ]]
            }
        }
    ]
    return zones
