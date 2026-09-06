"""
MarineGuard AI - Pydantic Request & Response Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# --- Vessel & AIS Schemas ---
class AISPositionSchema(BaseModel):
    id: Optional[int] = None
    mmsi: str
    timestamp: datetime
    latitude: float
    longitude: float
    sog_knots: Optional[float] = None
    cog_deg: Optional[float] = None
    heading_deg: Optional[float] = None
    nav_status: Optional[str] = None
    geom_geojson: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class VesselSchema(BaseModel):
    mmsi: str
    vessel_name: str
    imo: Optional[str] = None
    callsign: Optional[str] = None
    vessel_type: str
    flag: Optional[str] = None
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    draft_m: Optional[float] = None
    destination: Optional[str] = None
    risk_profile: Optional[str] = "NORMAL"
    positions: Optional[List[AISPositionSchema]] = []

    class Config:
        from_attributes = True


# --- Spill Detection Schemas ---
class SpillPolygonSchema(BaseModel):
    polygon_id: str
    type: str = "Polygon"
    coordinates: List[List[List[float]]]
    area_km2: float
    estimated_volume_m3: Optional[float] = None
    estimated_volume_bbl: Optional[float] = None
    bonn_code: int = 3
    bonn_description: str = "Code 3: Metallic"
    nominal_thickness_um: float = 25.0
    classification: str = "Mineral Oil Spill"
    confidence: float = 0.90


class SpillDetectionSchema(BaseModel):
    id: str
    timestamp: datetime
    source_satellite: str
    center_latitude: float
    center_longitude: float
    spill_polygon_geojson: Dict[str, Any]
    confidence_score: float
    affected_area_km2: float
    estimated_volume_m3: Optional[float] = None
    estimated_volume_bbl: Optional[float] = None
    bonn_code: int
    bonn_description: str
    nominal_thickness_um: float
    slick_classification: str
    raw_image_url: Optional[str] = None
    mask_image_url: Optional[str] = None

    class Config:
        from_attributes = True


# --- Attribution & Vessel Ranking Schemas ---
class AttributionScoreSchema(BaseModel):
    id: Optional[int] = None
    incident_id: str
    mmsi: str
    investigation_priority_score: float  # 0 to 100
    rank: int
    distance_to_spill_km: float
    temporal_overlap_rating: str  # HIGH, MEDIUM, LOW
    route_deviation_deg: Optional[float] = None
    speed_anomaly_drop_kn: Optional[float] = None
    heading_change_deg: Optional[float] = None
    time_in_spill_zone_min: Optional[float] = None
    explainability_dossier: Optional[Dict[str, Any]] = None
    disclaimer: str = "Indicator of investigation priority only; not proof of causation."
    vessel: Optional[VesselSchema] = None

    class Config:
        from_attributes = True


# --- Spill Trajectory Schemas ---
class SpillTrajectorySchema(BaseModel):
    id: Optional[int] = None
    spill_id: str
    forecast_hours: int
    forecast_timestamp: datetime
    predicted_polygon_geojson: Dict[str, Any]
    center_latitude: float
    center_longitude: float
    wind_drift_km: float
    current_drift_km: float
    evaporated_fraction_pct: float
    emulsified_water_pct: float
    coastal_hit_warning: bool
    coastal_eta_hours: Optional[float] = None

    class Config:
        from_attributes = True


# --- Ecological & Environmental Schemas ---
class EcologicalAssessmentSchema(BaseModel):
    id: Optional[int] = None
    spill_id: str
    ecological_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    composite_vulnerability_score: float
    exposed_species_count: int
    exposed_species_records: Optional[List[Dict[str, Any]]] = []
    nearby_mpas: Optional[List[Dict[str, Any]]] = []
    coral_reef_proximity_km: Optional[float] = None
    mangrove_proximity_km: Optional[float] = None
    assessment_notes: Optional[str] = None
    disclaimer: str = "Potential ecological exposure assessment; not confirmed biological mortality."

    class Config:
        from_attributes = True


class EnvironmentalRecordSchema(BaseModel):
    id: Optional[int] = None
    spill_id: str
    sea_surface_temp_c: float
    sst_anomaly_c: float
    marine_heatwave_category: Optional[str] = None
    wind_speed_knots: float
    wind_direction_deg: float
    current_speed_knots: float
    current_direction_deg: float
    wave_height_m: float
    chlorophyll_mg_m3: Optional[float] = None
    climatological_context: Optional[str] = None

    class Config:
        from_attributes = True


# --- Alert & Response Action Schemas ---
class AlertSchema(BaseModel):
    id: Optional[int] = None
    incident_id: str
    alert_level: str
    alert_type: str
    message: str
    created_at: datetime
    acknowledged: bool = False

    class Config:
        from_attributes = True


class ResponseActionSchema(BaseModel):
    id: Optional[int] = None
    incident_id: str
    action_type: str
    action_title: str
    status: str = "RECOMMENDED"
    priority: str = "P1"
    details: Optional[str] = None
    assigned_agency: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Incident Dossier Schemas ---
class IncidentSchema(BaseModel):
    id: str
    title: str
    status: str
    severity: str
    spill_id: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    recommended_action: Optional[str] = None
    spill_detection: Optional[SpillDetectionSchema] = None
    attributions: Optional[List[AttributionScoreSchema]] = []
    alerts: Optional[List[AlertSchema]] = []
    actions: Optional[List[ResponseActionSchema]] = []

    class Config:
        from_attributes = True


# --- Request Input Payloads ---
class DetectSpillRequest(BaseModel):
    image_base64: Optional[str] = None
    sample_id: Optional[str] = None
    center_lat: float = 28.7350
    center_lon: float = -88.3820
    pixel_res_m: float = 10.0


class PreIncidentRiskZone(BaseModel):
    zone_id: str
    zone_name: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    composite_risk_score: float
    traffic_density_ships_per_day: int
    tanker_percentage: float
    weather_severity: str
    center: Dict[str, float]
    radius_km: float
    geometry: Dict[str, Any]
