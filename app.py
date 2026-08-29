"""
MarineAI v3.0 — Maritime Incident Intelligence System
Full FastAPI application serving all API endpoints and the web dashboard.
"""
import dataclasses
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from marineai_engine.ais_pipeline import (
    get_current_positions, get_vessel_track,
    ingest_ais_csv, generate_vessel_tracks
)
from marineai_engine.anomaly_detector import analyze_vessel_fleet
from marineai_engine.attribution_engine import attribute_spill
from marineai_engine.incident_store import INCIDENT_STORE
from marineai_engine.alert_system import ALERT_STORE, broadcast_alert, generate_response_recommendations
from marineai_engine.sample_generator import generate_all_sample_assets

app = FastAPI(title="MarineAI v3.0 — Maritime Incident Intelligence System", version="3.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SAMPLES_DIR = STATIC_DIR / "samples"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_sample_registry = {}

@app.on_event("startup")
async def startup_event():
    global _sample_registry
    try:
        _sample_registry = generate_all_sample_assets(str(SAMPLES_DIR))
        print("✓ MarineAI v3.0 Maritime Surveillance System ONLINE")
    except Exception as e:
        print(f"[startup] Sample generation note: {e}")

# ─── Pydantic Models ────────────────────────────────────────────────────────

class CSVData(BaseModel):
    csv_content: str

class DriftRequest(BaseModel):
    origin_lat: float = 10.820
    origin_lon: float = 79.130
    wind_speed_knots: float = 12.0
    wind_direction_deg: float = 200.0
    current_speed_knots: float = 1.0
    current_direction_deg: float = 60.0
    spill_area_km2: float = 4.8
    spill_volume_m3: float = 120.0
    simulation_hours: int = 72

class IncidentCreate(BaseModel):
    title: str
    status: str = "INVESTIGATING"
    severity: str = "HIGH"
    lat: float
    lon: float
    location_name: str
    area_km2: float
    confidence: int
    detection_method: str = "SAR Satellite"
    satellite_scene: str = "AUTO"
    bonn_code: int = 3
    primary_vessel_mmsi: int = 0

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class AlertBroadcast(BaseModel):
    incident_id: str
    alert_type: str = "SPILL_DETECTED"
    severity: str = "HIGH"

class DetectRequest(BaseModel):
    sample_name: Optional[str] = None
    sensor_type: str = "AUTO"

class ReportRequest(BaseModel):
    analysis_data: Dict[str, Any]
    location_name: Optional[str] = "Bay of Bengal"

# ─── Utilities ───────────────────────────────────────────────────────────────

def _serialize(obj):
    """Convert dataclass instances and non-serializable objects to dicts."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# ─── Root / Dashboard ────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>MarineAI v3.0 — Backend Online. Frontend loading...</h1>"

# ─── Dashboard Stats ─────────────────────────────────────────────────────────

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    return {
        "active_incidents": 3,
        "high_risk_vessels": 7,
        "spills_detected": 5,
        "total_area_affected": 12.48,
        "ais_vessels_count": 12842,
        "satellite_scenes": 186,
        "coverage_area_km2": 2300000,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "system_status": {
            "ais_stream": "ONLINE",
            "satellite_feed": "ONLINE",
            "ai_models": "ONLINE",
            "database": "ONLINE"
        }
    }

# ─── AIS Fleet ───────────────────────────────────────────────────────────────

@app.get("/api/ais/vessels")
def get_ais_vessels():
    return get_current_positions()

@app.get("/api/ais/track/{mmsi}")
def get_ais_track(mmsi: int):
    track = get_vessel_track(mmsi)
    if not track:
        raise HTTPException(404, "Track not found")
    return {"mmsi": mmsi, "positions": track}

@app.post("/api/ais/ingest")
def ingest_ais(data: CSVData):
    count = ingest_ais_csv(data.csv_content)
    return {"status": "success", "ingested_records": count}

# ─── Anomaly Detection ───────────────────────────────────────────────────────

@app.get("/api/anomaly/fleet")
def get_fleet_anomaly():
    tracks = generate_vessel_tracks()
    return analyze_vessel_fleet(tracks)

@app.get("/api/anomaly/vessel/{mmsi}")
def get_vessel_anomaly(mmsi: int):
    fleet_reports = get_fleet_anomaly()
    for rep in fleet_reports:
        if rep["mmsi"] == mmsi:
            return rep
    raise HTTPException(404, "Vessel anomaly report not found")

# ─── Incidents ───────────────────────────────────────────────────────────────

@app.get("/api/incidents")
def get_incidents():
    return [dataclasses.asdict(i) for i in INCIDENT_STORE.get_all()]

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    inc = INCIDENT_STORE.get(incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return dataclasses.asdict(inc)

@app.post("/api/incidents", status_code=201)
def create_incident(data: IncidentCreate):
    inc = INCIDENT_STORE.create(data.dict())
    return dataclasses.asdict(inc)

@app.patch("/api/incidents/{incident_id}")
def update_incident(incident_id: str, data: IncidentUpdate):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    inc = INCIDENT_STORE.update(incident_id, update_data)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return dataclasses.asdict(inc)

@app.get("/api/incidents/{incident_id}/attribution")
def get_incident_attribution(incident_id: str):
    inc = INCIDENT_STORE.get(incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    tracks = generate_vessel_tracks()
    anomaly_reports = {r["mmsi"]: r for r in analyze_vessel_fleet(tracks)}
    spill_event = {
        "incident_id": inc.id,
        "lat": inc.lat,
        "lon": inc.lon,
        "detection_time": inc.detection_time,
        "area_km2": inc.area_km2,
        "bonn_code": inc.bonn_code,
        "confidence": inc.confidence
    }
    return attribute_spill(spill_event, tracks, anomaly_reports)

@app.get("/api/incidents/{incident_id}/response")
def get_incident_response(incident_id: str):
    inc = INCIDENT_STORE.get(incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return generate_response_recommendations(inc)

# ─── Alerts ──────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
def get_alerts():
    return [dataclasses.asdict(a) for a in ALERT_STORE.get_all()]

@app.post("/api/alerts/broadcast")
def api_broadcast_alert(data: AlertBroadcast):
    alert = broadcast_alert(data.incident_id, data.alert_type, data.severity)
    return dataclasses.asdict(alert)

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    result = ALERT_STORE.acknowledge(alert_id)
    if not result:
        raise HTTPException(404, "Alert not found")
    return dataclasses.asdict(result)

# ─── Report Generation ───────────────────────────────────────────────────────

@app.post("/api/report/{incident_id}", response_class=HTMLResponse)
def generate_full_report(incident_id: str):
    inc = INCIDENT_STORE.get(incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")

    tracks = generate_vessel_tracks()
    anomaly_reports = {r["mmsi"]: r for r in analyze_vessel_fleet(tracks)}
    spill_event = {
        "incident_id": inc.id, "lat": inc.lat, "lon": inc.lon,
        "detection_time": inc.detection_time, "area_km2": inc.area_km2,
        "bonn_code": inc.bonn_code, "confidence": inc.confidence
    }
    attributions = attribute_spill(spill_event, tracks, anomaly_reports)
    response_actions = generate_response_recommendations(inc)

    primary = attributions[0] if attributions else {}
    action_rows = "".join(
        f"<tr><td>{a['action']}</td><td>{a['agency']}</td><td>{a['priority']}</td><td>{a['estimated_response_time_hours']}h</td><td>{a['status']}</td></tr>"
        for a in response_actions
    )
    attr_rows = "".join(
        f"<tr><td>{a['vessel_name']}</td><td>{a['mmsi']}</td><td>{a['vessel_type']}</td><td>{a['combined_score']}%</td></tr>"
        for a in attributions
    )
    timeline_rows = "".join(
        f"<tr><td>{e['time']}</td><td>{e['event']}</td></tr>"
        for e in (inc.timeline or [])
    )
    gen_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MarineAI Investigation Report — {inc.id}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', sans-serif; background: #f1f5f9; color: #0f172a; padding: 40px 20px; line-height: 1.6; }}
    .report {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,.1); overflow: hidden; }}
    .report-header {{ background: #0a1628; color: #fff; padding: 32px 36px; }}
    .report-header h1 {{ font-size: 24px; font-weight: 800; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }}
    .report-header p {{ font-size: 13px; color: #8eaac8; margin-top: 8px; font-family: 'JetBrains Mono', monospace; }}
    .severity-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-top: 10px; }}
    .HIGH {{ background: rgba(255,23,68,.2); color: #ff1744; border: 1px solid rgba(255,23,68,.4); }}
    .MEDIUM {{ background: rgba(255,171,0,.2); color: #ffab00; border: 1px solid rgba(255,171,0,.4); }}
    .CONFIRMED {{ background: rgba(255,23,68,.15); color: #ff1744; }}
    .INVESTIGATING {{ background: rgba(255,171,0,.15); color: #ffab00; }}
    .report-body {{ padding: 32px 36px; }}
    h2 {{ font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #1e293b; border-bottom: 2px solid #0a1628; padding-bottom: 8px; margin: 28px 0 16px; }}
    .grid-3 {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-bottom: 20px; }}
    .stat-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
    .stat-card .lbl {{ font-size: 11px; text-transform: uppercase; color: #64748b; margin-bottom: 4px; }}
    .stat-card .val {{ font-size: 20px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #0f172a; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: #f1f5f9; color: #475569; font-weight: 600; padding: 10px 14px; text-align: left; }}
    td {{ padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #334155; }}
    .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px dashed #cbd5e1; display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; }}
    .rationale {{ background: #f8fafc; border-left: 4px solid #0284c7; padding: 14px 16px; border-radius: 0 6px 6px 0; font-size: 13px; color: #475569; margin-top: 10px; }}
    @media print {{ body {{ padding: 0; }} .report {{ box-shadow: none; border-radius: 0; }} }}
  </style>
</head>
<body>
<div class="report">
  <div class="report-header">
    <h1>🛡️ MARINEGUARD AI — Investigation Report</h1>
    <p>REPORT REF: {inc.id} &nbsp;|&nbsp; GENERATED: {gen_time} &nbsp;|&nbsp; LOCATION: {inc.location_name}</p>
    <div class="severity-badge {inc.severity}">{inc.severity} SEVERITY</div>
    &nbsp;
    <div class="severity-badge {inc.status}">{inc.status}</div>
  </div>
  <div class="report-body">
    <h2>1. Incident Overview</h2>
    <div class="grid-3">
      <div class="stat-card"><div class="lbl">Spill Area</div><div class="val">{inc.area_km2} km²</div></div>
      <div class="stat-card"><div class="lbl">AI Confidence</div><div class="val">{inc.confidence}%</div></div>
      <div class="stat-card"><div class="lbl">Bonn Code</div><div class="val">Code {inc.bonn_code}</div></div>
      <div class="stat-card"><div class="lbl">Detection Method</div><div class="val" style="font-size:13px">{inc.detection_method}</div></div>
      <div class="stat-card"><div class="lbl">Coordinates</div><div class="val" style="font-size:13px">{inc.lat}°N, {inc.lon}°E</div></div>
      <div class="stat-card"><div class="lbl">Detection Time</div><div class="val" style="font-size:13px">{inc.detection_time[:16].replace("T"," ")} UTC</div></div>
    </div>

    <h2>2. Attribution Analysis</h2>
    {"<p style='font-size:13px;color:#64748b'>Most probable source: <strong>" + primary.get('vessel_name','Unknown') + "</strong> — Attribution Score: <strong style='color:#0284c7'>" + str(primary.get('combined_score','N/A')) + "%</strong></p><div class='rationale'>" + primary.get('explanation','') + "</div>" if primary else "<p>No attribution data.</p>"}
    <table style="margin-top:16px">
      <thead><tr><th>Vessel</th><th>MMSI</th><th>Type</th><th>Attribution Score</th></tr></thead>
      <tbody>{attr_rows}</tbody>
    </table>

    <h2>3. Incident Timeline</h2>
    <table>
      <thead><tr><th>Timestamp</th><th>Event</th></tr></thead>
      <tbody>{timeline_rows if timeline_rows else "<tr><td colspan='2' style='color:#64748b'>No timeline data available.</td></tr>"}</tbody>
    </table>

    <h2>4. Response Recommendations</h2>
    <table>
      <thead><tr><th>Action</th><th>Agency</th><th>Priority</th><th>ETA</th><th>Status</th></tr></thead>
      <tbody>{action_rows}</tbody>
    </table>

    <div class="footer">
      <span>MarineAI Maritime Incident Intelligence System v3.0</span>
      <span>IMO / Bonn Agreement Standards Compliant</span>
    </div>
  </div>
</div>
</body>
</html>"""
    return html

# ─── Legacy / Utility Endpoints ──────────────────────────────────────────────

@app.get("/api/samples")
def get_samples():
    return {"samples": list(_sample_registry.values())}

@app.post("/api/detect")
async def detect_spill(
    file: Optional[UploadFile] = File(None),
    sample_name: Optional[str] = Form(None),
    sensor_type: Optional[str] = Form("AUTO"),
):
    try:
        from marineai_engine.detector import process_marine_image
        from marineai_engine.sample_generator import generate_all_sample_assets
        if file and file.filename:
            contents = await file.read()
            result = process_marine_image(contents, sensor_type=sensor_type)
        elif sample_name:
            sample_path = SAMPLES_DIR / sample_name
            if not sample_path.exists():
                generate_all_sample_assets(str(SAMPLES_DIR))
            result = process_marine_image(str(sample_path), sensor_type=sensor_type)
        else:
            raise HTTPException(400, "Provide file or sample_name")
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/simulate-drift")
def simulate_drift(params: DriftRequest):
    from marineai_engine.drift_simulator import simulate_oil_drift
    return simulate_oil_drift(
        origin_lat=params.origin_lat, origin_lon=params.origin_lon,
        wind_speed_knots=params.wind_speed_knots, wind_direction_deg=params.wind_direction_deg,
        current_speed_knots=params.current_speed_knots, current_direction_deg=params.current_direction_deg,
        spill_area_km2=params.spill_area_km2, spill_volume_m3=params.spill_volume_m3,
        simulation_hours=params.simulation_hours
    )

@app.post("/api/generate-report", response_class=HTMLResponse)
async def legacy_generate_report(payload: ReportRequest):
    from marineai_engine.report_generator import generate_incident_report_html
    return generate_incident_report_html(payload.analysis_data, payload.location_name)

@app.get("/api/health")
def health_check():
    return {"status": "ONLINE", "version": "3.0.0", "system": "MarineAI Maritime Incident Intelligence"}
