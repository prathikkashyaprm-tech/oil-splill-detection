"""
MarineGuard AI - Database Models (SQLAlchemy 2.0 + GeoSpatial support)
Includes 12 tables matching PRD specification for PostgreSQL/PostGIS with SQLite fallback:
1. vessels
2. ais_positions
3. spill_detections
4. incidents
5. vessel_anomalies
6. attribution_scores
7. spill_trajectories
8. marine_species
9. ecological_assessments
10. environmental_records
11. alerts
12. response_actions
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Vessel(Base):
    __tablename__ = "vessels"

    mmsi = Column(String(20), primary_key=True, index=True)
    vessel_name = Column(String(100), nullable=False)
    imo = Column(String(20), nullable=True)
    callsign = Column(String(20), nullable=True)
    vessel_type = Column(String(50), nullable=False)
    flag = Column(String(50), nullable=True)
    length_m = Column(Float, nullable=True)
    width_m = Column(Float, nullable=True)
    draft_m = Column(Float, nullable=True)
    destination = Column(String(100), nullable=True)
    eta = Column(String(50), nullable=True)
    risk_profile = Column(String(50), default="NORMAL")  # NORMAL, WATCHLIST, ELEVATED

    positions = relationship("AISPosition", back_populates="vessel", cascade="all, delete-orphan")
    attributions = relationship("AttributionScore", back_populates="vessel")


class AISPosition(Base):
    __tablename__ = "ais_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(String(20), ForeignKey("vessels.mmsi", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    sog_knots = Column(Float, nullable=True)  # Speed over ground
    cog_deg = Column(Float, nullable=True)    # Course over ground
    heading_deg = Column(Float, nullable=True)
    nav_status = Column(String(50), nullable=True)
    # GeoJSON geometry representation for SQLite/PostGIS interoperability
    geom_geojson = Column(JSON, nullable=True)

    vessel = relationship("Vessel", back_populates="positions")


class SpillDetection(Base):
    __tablename__ = "spill_detections"

    id = Column(String(50), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    source_satellite = Column(String(50), default="Sentinel-1 SAR C-Band")
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    spill_polygon_geojson = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=False)
    affected_area_km2 = Column(Float, nullable=False)
    estimated_volume_m3 = Column(Float, nullable=True)
    estimated_volume_bbl = Column(Float, nullable=True)
    bonn_code = Column(Integer, default=3)
    bonn_description = Column(String(100), default="Code 3: Metallic")
    nominal_thickness_um = Column(Float, default=25.0)
    texture_homogeneity = Column(Float, nullable=True)
    texture_contrast = Column(Float, nullable=True)
    slick_classification = Column(String(50), default="Mineral Oil Spill")
    raw_image_url = Column(String(255), nullable=True)
    mask_image_url = Column(String(255), nullable=True)

    incident = relationship("Incident", back_populates="spill_detection", uselist=False)
    trajectories = relationship("SpillTrajectory", back_populates="spill")
    ecological_assessment = relationship("EcologicalAssessment", back_populates="spill", uselist=False)
    environmental_record = relationship("EnvironmentalRecord", back_populates="spill", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(50), primary_key=True, index=True)  # e.g. MG-2026-001
    title = Column(String(150), nullable=False)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, INVESTIGATING, CONTAINED, CLOSED
    severity = Column(String(50), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    spill_id = Column(String(50), ForeignKey("spill_detections.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    summary = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)

    spill_detection = relationship("SpillDetection", back_populates="incident")
    attributions = relationship("AttributionScore", back_populates="incident", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("ResponseAction", back_populates="incident", cascade="all, delete-orphan")


class VesselAnomaly(Base):
    __tablename__ = "vessel_anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(String(20), ForeignKey("vessels.mmsi"), nullable=False)
    incident_id = Column(String(50), ForeignKey("incidents.id"), nullable=True)
    anomaly_type = Column(String(50), nullable=False)  # SPEED_DROP, UNUSUAL_STOP, ROUTE_DEVIATION, HEADING_JUMP
    severity = Column(String(20), default="MEDIUM")
    details = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)


class AttributionScore(Base):
    __tablename__ = "attribution_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(50), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    mmsi = Column(String(20), ForeignKey("vessels.mmsi"), nullable=False)
    investigation_priority_score = Column(Float, nullable=False)  # 0 to 100
    rank = Column(Integer, nullable=False)
    distance_to_spill_km = Column(Float, nullable=False)
    temporal_overlap_rating = Column(String(50), nullable=False)  # HIGH, MEDIUM, LOW
    route_deviation_deg = Column(Float, nullable=True)
    speed_anomaly_drop_kn = Column(Float, nullable=True)
    heading_change_deg = Column(Float, nullable=True)
    time_in_spill_zone_min = Column(Float, nullable=True)
    vessel_type_risk_weight = Column(Float, nullable=True)
    explainability_dossier = Column(JSON, nullable=True)
    disclaimer = Column(String(255), default="Indicator of investigation priority only; not proof of causation.")

    incident = relationship("Incident", back_populates="attributions")
    vessel = relationship("Vessel", back_populates="attributions")


class SpillTrajectory(Base):
    __tablename__ = "spill_trajectories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spill_id = Column(String(50), ForeignKey("spill_detections.id", ondelete="CASCADE"), nullable=False)
    forecast_hours = Column(Integer, nullable=False)  # 6, 12, 24, 48, 72
    forecast_timestamp = Column(DateTime, nullable=False)
    predicted_polygon_geojson = Column(JSON, nullable=False)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    wind_drift_km = Column(Float, nullable=False)
    current_drift_km = Column(Float, nullable=False)
    evaporated_fraction_pct = Column(Float, nullable=False)
    emulsified_water_pct = Column(Float, nullable=False)
    coastal_hit_warning = Column(Boolean, default=False)
    coastal_eta_hours = Column(Float, nullable=True)

    spill = relationship("SpillDetection", back_populates="trajectories")


class MarineSpecies(Base):
    __tablename__ = "marine_species"

    id = Column(String(50), primary_key=True)
    scientific_name = Column(String(100), nullable=False)
    common_name = Column(String(100), nullable=False)
    taxon_group = Column(String(50), nullable=False)
    iucn_status = Column(String(50), nullable=False)
    vulnerability_score = Column(Float, nullable=False)
    oil_sensitivity_notes = Column(Text, nullable=True)
    region = Column(String(100), nullable=False)


class EcologicalAssessment(Base):
    __tablename__ = "ecological_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spill_id = Column(String(50), ForeignKey("spill_detections.id", ondelete="CASCADE"), nullable=False)
    ecological_risk_level = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    composite_vulnerability_score = Column(Float, nullable=False)
    exposed_species_count = Column(Integer, default=0)
    exposed_species_records = Column(JSON, nullable=True)
    nearby_mpas = Column(JSON, nullable=True)
    coral_reef_proximity_km = Column(Float, nullable=True)
    mangrove_proximity_km = Column(Float, nullable=True)
    assessment_notes = Column(Text, nullable=True)
    disclaimer = Column(String(255), default="Potential ecological exposure assessment; not confirmed mortality.")

    spill = relationship("SpillDetection", back_populates="ecological_assessment")


class EnvironmentalRecord(Base):
    __tablename__ = "environmental_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spill_id = Column(String(50), ForeignKey("spill_detections.id", ondelete="CASCADE"), nullable=False)
    sea_surface_temp_c = Column(Float, nullable=False)
    sst_anomaly_c = Column(Float, nullable=False)
    marine_heatwave_category = Column(String(50), nullable=True)
    wind_speed_knots = Column(Float, nullable=False)
    wind_direction_deg = Column(Float, nullable=False)
    current_speed_knots = Column(Float, nullable=False)
    current_direction_deg = Column(Float, nullable=False)
    wave_height_m = Column(Float, nullable=False)
    chlorophyll_mg_m3 = Column(Float, nullable=True)
    climatological_context = Column(Text, nullable=True)

    spill = relationship("SpillDetection", back_populates="environmental_record")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(50), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    alert_level = Column(String(20), default="HIGH")  # INFO, WARNING, CRITICAL
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged = Column(Boolean, default=False)

    incident = relationship("Incident", back_populates="alerts")


class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(50), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)
    action_title = Column(String(150), nullable=False)
    status = Column(String(50), default="RECOMMENDED")  # RECOMMENDED, DISPATCHED, COMPLETED
    priority = Column(String(20), default="P1")
    details = Column(Text, nullable=True)
    assigned_agency = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="actions")
