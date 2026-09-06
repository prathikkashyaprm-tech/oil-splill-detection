"""
MarineGuard AI - Multi-Source Evidence Fusion Engine
Synthesizes SAR, AIS spatial/temporal trajectories, vessel behavior, environmental forces,
and OBIS ecological sensitivity into an explainable, audit-ready Incident Assessment Dossier.
"""

from typing import Dict, Any, List


def synthesize_evidence_dossier(
    incident_id: str,
    spill_detection: Dict[str, Any],
    candidate_vessels: List[Dict[str, Any]],
    trajectories: List[Dict[str, Any]],
    ecological_assessment: Dict[str, Any],
    environmental_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates structured multi-pillar evidence fusion summary.
    """
    top_candidate = candidate_vessels[0] if candidate_vessels else None
    vessel_data = top_candidate.get("vessel", {}) if top_candidate else {}
    metrics = top_candidate.get("metrics", {}) if top_candidate else {}

    # Pillar 1: SAR Satellite Evidence
    sar_pillar = {
        "pillar": "Satellite Synthetic Aperture Radar (SAR)",
        "confidence_score": f"{spill_detection.get('confidence_score', 0.90) * 100:.1f}%",
        "affected_area_km2": f"{spill_detection.get('affected_area_km2', 0.0):.2f} km²",
        "bonn_appearance": spill_detection.get('bonn_description', 'Code 3: Metallic'),
        "estimated_volume": f"{spill_detection.get('estimated_volume_bbl', 0.0):.1f} bbl (~{spill_detection.get('estimated_volume_m3', 0.0):.1f} m³)",
        "lookalike_discrimination": spill_detection.get('slick_classification', 'Mineral Oil Spill')
    }

    # Pillar 2: AIS Spatio-Temporal Evidence
    ais_pillar = {
        "pillar": "AIS Spatio-Temporal Trajectory",
        "primary_candidate_mmsi": vessel_data.get("mmsi", "N/A"),
        "primary_candidate_name": vessel_data.get("vessel_name", "N/A"),
        "vessel_type": vessel_data.get("vessel_type", "N/A"),
        "closest_distance_km": f"{metrics.get('min_distance_km', 0.0):.2f} km",
        "temporal_overlap": metrics.get("temporal_overlap_rating", "LOW"),
        "time_in_spill_bounding_box": f"{metrics.get('time_in_spill_zone_min', 0.0):.0f} min"
    }

    # Pillar 3: Behavioral Anomaly Evidence
    behavior_pillar = {
        "pillar": "Kinematic & Behavioral Anomaly",
        "investigation_priority_score": f"{metrics.get('investigation_priority_score', 0.0):.1f} / 100",
        "speed_anomaly": f"Deceleration of {metrics.get('speed_anomaly_drop_kn', 0.0):.1f} knots",
        "course_deviation": f"{metrics.get('route_deviation_deg', 0.0):.1f}° departure from lane",
        "anomaly_indicators": metrics.get("anomaly_flags", [])
    }

    # Pillar 4: Environmental & Drift Vectors
    env_pillar = {
        "pillar": "Oceanographic Drift & Weathering",
        "wind_forcing": f"{environmental_record.get('wind_speed_knots', 10.0):.1f} kn @ {environmental_record.get('wind_direction_deg', 0.0):.0f}°",
        "surface_current": f"{environmental_record.get('current_speed_knots', 1.0):.1f} kn @ {environmental_record.get('current_direction_deg', 0.0):.0f}°",
        "sea_surface_temp": f"{environmental_record.get('sea_surface_temp_c', 28.0):.1f}°C (Anomaly: +{environmental_record.get('sst_anomaly_c', 1.0):.1f}°C)",
        "72h_drift_forecast_km": f"{trajectories[-1].get('total_drift_km', 0.0) if trajectories else 0.0:.1f} km",
        "72h_evaporation_decay": f"{trajectories[-1].get('evaporated_fraction_pct', 0.0) if trajectories else 0.0:.1f}%"
    }

    # Pillar 5: OBIS Ecological Vulnerability
    eco_pillar = {
        "pillar": "Marine Biodiversity & Sensitive Habitats",
        "ecological_risk_rating": ecological_assessment.get("ecological_risk_level", "HIGH"),
        "exposed_species_count": ecological_assessment.get("exposed_species_count", 0),
        "coral_reef_proximity": f"{ecological_assessment.get('coral_reef_proximity_km', 0.0):.1f} km",
        "protected_areas_at_risk": [m["name"] for m in ecological_assessment.get("nearby_mpas", [])[:2]]
    }

    # Generate Response Playbook
    response_actions = []
    eco_risk = ecological_assessment.get("ecological_risk_level", "HIGH")
    if top_candidate and metrics.get("investigation_priority_score", 0) >= 70:
        response_actions.append({
            "priority": "P1 - CRITICAL",
            "action": f"Dispatch Maritime Coast Guard inspection to candidate vessel '{vessel_data.get('vessel_name', 'MMSI ' + str(vessel_data.get('mmsi')))}' at destination port for bilge/cargo tank log inspection.",
            "agency": "Coast Guard & Port State Control (PSC)"
        })
    
    if eco_risk in ["HIGH", "CRITICAL"]:
        response_actions.append({
            "priority": "P1 - URGENT",
            "action": f"Deploy containment booms and skimmers around sensitive marine habitats in predicted 24h drift corridor.",
            "agency": "Marine Environmental Protection Authority (MEPA)"
        })

    response_actions.append({
        "priority": "P2 - HIGH",
        "action": "Task follow-up Sentinel-1 / Sentinel-2 satellite passes over predicted trajectory cone (+24h & +48h).",
        "agency": "National Remote Sensing Centre (NRSC) / Copernicus"
    })

    return {
        "incident_id": incident_id,
        "executive_summary": (
            f"Multi-source evidence fusion confirms a {spill_detection.get('affected_area_km2', 0.0):.2f} km² "
            f"hydrocarbon slick classified as {spill_detection.get('bonn_description', 'Metallic')} "
            f"with {spill_detection.get('confidence_score', 0.90)*100:.0f}% confidence. AIS correlation identified "
            f"{len(candidate_vessels)} candidate vessels in the surveillance window; "
            f"'{vessel_data.get('vessel_name', 'Unknown')}' holds highest investigation priority "
            f"({metrics.get('investigation_priority_score', 0.0):.0f}/100) due to temporal alignment, "
            f"{metrics.get('min_distance_km', 0.0):.1f} km proximity, and speed drop anomaly. "
            f"Ecological exposure is rated {eco_risk}."
        ),
        "pillars": [sar_pillar, ais_pillar, behavior_pillar, env_pillar, eco_pillar],
        "candidate_ranking_summary": [
            {
                "rank": c.get("rank", i+1),
                "mmsi": c.get("vessel", {}).get("mmsi"),
                "vessel_name": c.get("vessel", {}).get("vessel_name"),
                "vessel_type": c.get("vessel", {}).get("vessel_type"),
                "investigation_priority_score": c.get("metrics", {}).get("investigation_priority_score"),
                "distance_km": c.get("metrics", {}).get("min_distance_km"),
                "speed_drop_kn": c.get("metrics", {}).get("speed_anomaly_drop_kn"),
                "route_deviation_deg": c.get("metrics", {}).get("route_deviation_deg"),
                "temporal_overlap": c.get("metrics", {}).get("temporal_overlap_rating")
            }
            for i, c in enumerate(candidate_vessels)
        ],
        "recommended_response_actions": response_actions,
        "disclaimer": "This intelligence dossier combines satellite SAR, AIS telemetry, and oceanographic modeling. Association scores indicate priority for maritime investigation and do not constitute legal determinations of liability."
    }
