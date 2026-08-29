from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class Incident:
    id: str
    title: str
    status: str
    severity: str
    lat: float
    lon: float
    location_name: str
    area_km2: float
    confidence: int
    detection_time: str
    last_updated: str
    bonn_code: int
    detection_method: str
    satellite_scene: str
    primary_vessel_mmsi: int
    attribution_scores: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, str]] = field(default_factory=list)
    response_actions: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""

class IncidentStore:
    def __init__(self):
        self._incidents: List[Incident] = []
        self._load_demo_data()

    def _load_demo_data(self):
        inc1 = Incident(
            id="INC-2025-05-20-01",
            title="Major Oil Spill Detected",
            status="INVESTIGATING",
            severity="HIGH",
            lat=10.820,
            lon=79.130,
            location_name="Bay of Bengal, 42km SE of Puducherry",
            area_km2=4.8,
            confidence=91,
            detection_time="2025-05-20T12:00:00Z",
            last_updated="2025-05-20T15:00:00Z",
            bonn_code=3,
            detection_method="SAR Satellite",
            satellite_scene="RISAT-2B-SCENE-8849",
            primary_vessel_mmsi=419001234,
            timeline=[
                {"time": "2025-05-20T12:00:00Z", "event": "Initial detection via SAR"},
                {"time": "2025-05-20T12:15:00Z", "event": "AI confidence upgraded to 91%"},
                {"time": "2025-05-20T12:30:00Z", "event": "AIS gap correlated with MT SHIVALIK"},
                {"time": "2025-05-20T13:00:00Z", "event": "Indian Coast Guard alerted"},
                {"time": "2025-05-20T14:00:00Z", "event": "Response recommendations generated"},
                {"time": "2025-05-20T15:00:00Z", "event": "Status updated to Under Investigation"}
            ]
        )
        inc2 = Incident(
            id="INC-2025-05-18-02", title="Minor Spill", status="CLOSED", severity="MEDIUM",
            lat=11.1, lon=80.1, location_name="Bay of Bengal", area_km2=1.2, confidence=80,
            detection_time="2025-05-18T10:00:00Z", last_updated="2025-05-18T20:00:00Z",
            bonn_code=1, detection_method="Optical Satellite", satellite_scene="S2A-SCENE",
            primary_vessel_mmsi=419002345
        )
        inc3 = Incident(
            id="INC-2025-05-15-03", title="Large Anomaly", status="INVESTIGATING", severity="HIGH",
            lat=12.1, lon=81.1, location_name="Bay of Bengal Deep Water", area_km2=8.5, confidence=88,
            detection_time="2025-05-15T08:00:00Z", last_updated="2025-05-16T12:00:00Z",
            bonn_code=4, detection_method="SAR Satellite", satellite_scene="RS2-SCENE",
            primary_vessel_mmsi=0
        )
        self._incidents.extend([inc1, inc2, inc3])

    def get_all(self) -> List[Incident]:
        return self._incidents

    def get(self, id: str) -> Incident:
        for inc in self._incidents:
            if inc.id == id:
                return inc
        return None

    def create(self, data: Dict[str, Any]) -> Incident:
        new_inc = Incident(
            id=f"INC-{datetime.utcnow().strftime('%Y-%m-%d')}-99",
            **data
        )
        self._incidents.append(new_inc)
        return new_inc

    def update(self, id: str, data: Dict[str, Any]) -> Incident:
        inc = self.get(id)
        if inc:
            for k, v in data.items():
                if hasattr(inc, k):
                    setattr(inc, k, v)
            inc.last_updated = datetime.utcnow().isoformat() + "Z"
        return inc

    def close(self, id: str) -> Incident:
        return self.update(id, {"status": "CLOSED"})

INCIDENT_STORE = IncidentStore()
