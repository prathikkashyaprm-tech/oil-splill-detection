"""
Bonn Agreement Oil Appearance Code (BAOAC) Calculator
Standardized international maritime system for quantifying oil slick thickness, 
estimating volume, and prescribing countermeasure protocols.
"""

from typing import Dict, Any, List

BONN_CODES = {
    1: {
        "name": "Sheen (Silvery/Grey)",
        "code": 1,
        "thickness_range_um": [0.04, 0.30],
        "nominal_thickness_um": 0.1,
        "nominal_m3_per_km2": 0.1,
        "visual_description": "Silvery or grey sheen with high reflectance, thin single-molecule film.",
        "environmental_impact": "Low direct smothering; volatile fraction evaporating rapidly.",
        "recommended_action": "Natural dispersion & real-time satellite/drone tracking. No mechanical recovery needed."
    },
    2: {
        "name": "Rainbow",
        "code": 2,
        "thickness_range_um": [0.30, 5.0],
        "nominal_thickness_um": 1.0,
        "nominal_m3_per_km2": 1.0,
        "visual_description": "Multi-colored rainbow bands caused by light wave interference.",
        "environmental_impact": "Moderate surface microlayer toxicity to plankton and fish larvae.",
        "recommended_action": "Passive containment if drifting toward shoreline or coral reef sanctuaries."
    },
    3: {
        "name": "Metallic",
        "code": 3,
        "thickness_range_um": [5.0, 50.0],
        "nominal_thickness_um": 25.0,
        "nominal_m3_per_km2": 25.0,
        "visual_description": "Dull metallic sheen reflecting true oil coloration under diffuse sunlight.",
        "environmental_impact": "Substantial hazard to seabird plumage and marine fauna.",
        "recommended_action": "Deploy rapid offshore containment booms and dynamic weir skimmers."
    },
    4: {
        "name": "Discontinuous True Oil Color",
        "code": 4,
        "thickness_range_um": [50.0, 200.0],
        "nominal_thickness_um": 100.0,
        "nominal_m3_per_km2": 100.0,
        "visual_description": "Broken patches of dark brown or black crude oil surrounded by metallic sheen.",
        "environmental_impact": "High risk of heavy coastal contamination and benthic toxicity.",
        "recommended_action": "Mobilize high-capacity brush skimmers; evaluate aerial dispersant application."
    },
    5: {
        "name": "Continuous True Oil Color (Heavy Slick)",
        "code": 5,
        "thickness_range_um": [200.0, 1000.0],
        "nominal_thickness_um": 300.0,
        "nominal_m3_per_km2": 300.0,
        "visual_description": "Continuous thick black/dark-brown viscous emulsion layer (chocolate mousse).",
        "environmental_impact": "Critical environmental catastrophe. Immediate risk of catastrophic shoreline fouling.",
        "recommended_action": "TIER-3 emergency mobilization: ocean booms, offshore vacuum recovery, shoreline protection."
    }
}

BARRELS_PER_M3 = 6.28981077  # 1 m^3 = ~6.2898 oil barrels (bbl)

def calculate_bonn_metrics(spill_area_km2: float, bonn_code: int = 3, coverage_distribution: Dict[int, float] = None) -> Dict[str, Any]:
    """
    Calculate volume and environmental risk metrics using Bonn Agreement guidelines.
    
    Args:
        spill_area_km2: Total detected slick area in square kilometers.
        bonn_code: Dominant Bonn Code (1-5) if distribution not specified.
        coverage_distribution: Optional dictionary mapping bonn_code -> fractional area coverage (summing to 1.0).
        
    Returns:
        Comprehensive dictionary of volume metrics, severity grade, and emergency recommendations.
    """
    if spill_area_km2 <= 0:
        return {
            "bonn_code": 0,
            "bonn_name": "No Spill / Clean Marine Surface",
            "spill_area_km2": 0.0,
            "spill_area_m2": 0.0,
            "estimated_volume_m3": 0.0,
            "estimated_volume_bbl": 0.0,
            "estimated_thickness_um": 0.0,
            "severity_level": "CLEAR",
            "severity_score": 0.0,
            "countermeasures": ["Routine satellite & aerial patrol."]
        }
    
    if coverage_distribution:
        total_vol_m3 = 0.0
        weighted_thick_um = 0.0
        for code, fraction in coverage_distribution.items():
            spec = BONN_CODES.get(code, BONN_CODES[3])
            sub_area = spill_area_km2 * fraction
            sub_vol = sub_area * spec["nominal_m3_per_km2"]
            total_vol_m3 += sub_vol
            weighted_thick_um += spec["nominal_thickness_um"] * fraction
        dominant_code = max(coverage_distribution, key=coverage_distribution.get)
    else:
        dominant_code = bonn_code if bonn_code in BONN_CODES else 3
        spec = BONN_CODES[dominant_code]
        total_vol_m3 = spill_area_km2 * spec["nominal_m3_per_km2"]
        weighted_thick_um = spec["nominal_thickness_um"]

    total_bbl = total_vol_m3 * BARRELS_PER_M3
    
    # Severity grading based on area and volume
    if total_vol_m3 > 500 or spill_area_km2 > 25.0 or dominant_code >= 4:
        severity_level = "TIER-3 CRITICAL EMERGENCY"
        severity_class = "critical"
        severity_score = min(100.0, 75.0 + (spill_area_km2 / 50.0) * 25.0)
    elif total_vol_m3 > 50 or spill_area_km2 > 5.0 or dominant_code == 3:
        severity_level = "TIER-2 REGIONAL ALERT"
        severity_class = "warning"
        severity_score = 45.0 + min(30.0, (spill_area_km2 / 25.0) * 30.0)
    else:
        severity_level = "TIER-1 LOCALIZED INCIDENT"
        severity_class = "caution"
        severity_score = 15.0 + min(30.0, (spill_area_km2 / 5.0) * 30.0)

    spec = BONN_CODES.get(dominant_code, BONN_CODES[3])
    
    # Recommended Response Tactics
    countermeasures = [
        spec["recommended_action"],
        f"Deploy primary containment boom with minimum length {max(500, int(spill_area_km2 * 400))} meters.",
        f"Estimated mechanical skimmer recovery capacity required: {max(10, int(total_vol_m3 * 0.4))} m³/day.",
        "Initiate 72-hour Lagrangian ocean drift simulation and issue NAVTEX coastal hazard warning."
    ]

    return {
        "bonn_code": dominant_code,
        "bonn_name": spec["name"],
        "visual_description": spec["visual_description"],
        "environmental_impact": spec["environmental_impact"],
        "spill_area_km2": round(spill_area_km2, 4),
        "spill_area_m2": round(spill_area_km2 * 1_000_000, 2),
        "estimated_volume_m3": round(total_vol_m3, 2),
        "estimated_volume_bbl": round(total_bbl, 2),
        "estimated_thickness_um": round(weighted_thick_um, 2),
        "severity_level": severity_level,
        "severity_class": severity_class,
        "severity_score": round(severity_score, 1),
        "countermeasures": countermeasures
    }
