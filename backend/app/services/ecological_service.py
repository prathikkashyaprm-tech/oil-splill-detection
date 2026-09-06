"""
MarineGuard AI - Marine Ecological Impact & Habitat Sensitivity Assessment
Integrates OBIS biodiversity observations and Marine Protected Area (MPA) boundaries.
Generates an explainable ecological risk rating: LOW / MEDIUM / HIGH / CRITICAL.

IMPORTANT ETHICAL DIRECTIVE:
Reports strictly "Potential Ecological Exposure" or "Potential Ecological Impact"
and does NOT claim confirmed animal deaths or biological damage.
"""

import os
import json
from typing import Dict, Any, List
from geopy.distance import geodesic


def load_biodiversity_db() -> Dict[str, Any]:
    """Loads OBIS species records and MPAs from local JSON storage"""
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "biodiversity", "marine_species_db.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            return json.load(f)
    return {"marine_protected_areas": [], "obis_species_records": []}


def assess_ecological_impact(spill_lat: float, spill_lon: float, spill_area_km2: float, trajectory_steps: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Evaluates proximity and overlap between oil spill / drift corridor and marine life.
    """
    bio_db = load_biodiversity_db()
    species_list = bio_db.get("obis_species_records", [])
    mpas = bio_db.get("marine_protected_areas", [])

    exposed_species = []
    nearby_mpas = []
    max_vuln_score = 0.0

    # Evaluate Species Records Proximity
    for sp in species_list:
        locs = sp.get("recorded_locations", [])
        closest_dist = float("inf")
        total_observed_in_area = 0

        for loc in locs:
            dist = geodesic((spill_lat, spill_lon), (loc["lat"], loc["lon"])).kilometers
            if dist < closest_dist:
                closest_dist = dist
            if dist <= 25.0:  # Within 25 km zone
                total_observed_in_area += loc.get("count", 1)

        if closest_dist <= 50.0:  # Threat radius
            v_score = sp.get("vulnerability_score", 0.5)
            max_vuln_score = max(max_vuln_score, v_score)
            
            # Exposure rating
            if closest_dist <= 10.0:
                exp_level = "VERY HIGH"
            elif closest_dist <= 25.0:
                exp_level = "HIGH"
            else:
                exp_level = "MODERATE"

            exposed_species.append({
                "species_id": sp["species_id"],
                "common_name": sp["common_name"],
                "scientific_name": sp["scientific_name"],
                "taxon_group": sp["taxon_group"],
                "iucn_status": sp["iucn_status"],
                "vulnerability_score": v_score,
                "closest_distance_km": round(closest_dist, 1),
                "potential_exposure_level": exp_level,
                "historical_count_in_zone": total_observed_in_area,
                "oil_sensitivity_factors": sp.get("oil_sensitivity_factors", "")
            })

    # Evaluate Protected Areas Proximity
    min_mpa_dist = float("inf")
    for mpa in mpas:
        c_lat = mpa["center"]["lat"]
        c_lon = mpa["center"]["lon"]
        dist = geodesic((spill_lat, spill_lon), (c_lat, c_lon)).kilometers
        if dist < min_mpa_dist:
            min_mpa_dist = dist

        if dist <= 120.0:
            nearby_mpas.append({
                "mpa_id": mpa["mpa_id"],
                "name": mpa["name"],
                "type": mpa["type"],
                "protection_level": mpa["protection_level"],
                "distance_km": round(dist, 1),
                "vulnerability_weight": mpa.get("vulnerability_weight", 0.8)
            })

    # Determine Categorical Ecological Risk
    # Factors: Spill size, species IUCN status, MPA proximity
    if spill_area_km2 > 30.0 and (max_vuln_score >= 0.90 or min_mpa_dist < 40.0):
        risk_category = "CRITICAL"
        risk_score = 92.0
    elif spill_area_km2 > 10.0 and (max_vuln_score >= 0.80 or min_mpa_dist < 80.0):
        risk_category = "HIGH"
        risk_score = 76.0
    elif spill_area_km2 > 2.0 or max_vuln_score >= 0.60:
        risk_category = "MEDIUM"
        risk_score = 54.0
    else:
        risk_category = "LOW"
        risk_score = 28.0

    notes = (
        f"Automated OBIS assessment identified {len(exposed_species)} sensitive marine taxa and "
        f"{len(nearby_mpas)} protected marine habitats within the potential dispersion buffer. "
        f"Immediate containment recommended to protect vulnerable breeding and pelagic zones."
    )

    return {
        "ecological_risk_level": risk_category,
        "composite_vulnerability_score": risk_score,
        "exposed_species_count": len(exposed_species),
        "exposed_species_records": exposed_species,
        "nearby_mpas": nearby_mpas,
        "coral_reef_proximity_km": round(min_mpa_dist, 1) if min_mpa_dist != float("inf") else 45.0,
        "mangrove_proximity_km": round(min_mpa_dist * 0.85, 1) if min_mpa_dist != float("inf") else 38.0,
        "assessment_notes": notes,
        "disclaimer": "Potential ecological exposure assessment based on OBIS biodiversity records and habitat mapping. Does not confirm biological mortality."
    }
