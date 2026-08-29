from enum import Enum
from dataclasses import dataclass, field
from typing import TypedDict, List
from datetime import datetime
import uuid

class AlertType(Enum):
    SPILL_DETECTED = "SPILL_DETECTED"
    HIGH_CONFIDENCE_ATTRIBUTION = "HIGH_CONFIDENCE_ATTRIBUTION"
    VESSEL_APPROACHING_SPILL = "VESSEL_APPROACHING_SPILL"
    AUTHORITY_NOTIFICATION = "AUTHORITY_NOTIFICATION"
    RESPONSE_DISPATCHED = "RESPONSE_DISPATCHED"

@dataclass
class Alert:
    id: str
    type: str
    severity: str
    title: str
    message: str
    incident_id: str
    target_mmsi: int
    created_at: str
    acknowledged: bool = False

class ResponseAction(TypedDict):
    action: str
    priority: str
    agency: str
    estimated_response_time_hours: float
    status: str

AUTHORITIES = [
    "Indian Coast Guard", 
    "Chennai Port Trust", 
    "Ministry of Shipping", 
    "INCOIS (Indian National Centre for Ocean Information Services)"
]

def generate_response_recommendations(incident) -> List[ResponseAction]:
    return [
        {"action": "Alert Indian Coast Guard", "priority": "HIGH", "agency": "Indian Coast Guard", "estimated_response_time_hours": 0.5, "status": "PENDING"},
        {"action": "Notify Chennai Port Authority", "priority": "HIGH", "agency": "Chennai Port Trust", "estimated_response_time_hours": 1.0, "status": "PENDING"},
        {"action": "Task RISAT-2B High Resolution Satellite", "priority": "MEDIUM", "agency": "INCOIS", "estimated_response_time_hours": 2.0, "status": "PENDING"},
        {"action": "Deploy Oil Skimmer ICGS SAMUDRA PAHEREDAR", "priority": "HIGH", "agency": "Indian Coast Guard", "estimated_response_time_hours": 4.0, "status": "PENDING"},
        {"action": "Issue NAVTEX Maritime Warning", "priority": "HIGH", "agency": "Ministry of Shipping", "estimated_response_time_hours": 0.5, "status": "PENDING"},
        {"action": "Prepare Dispersant Aircraft OSR-101", "priority": "MEDIUM", "agency": "Indian Coast Guard", "estimated_response_time_hours": 6.0, "status": "PENDING"}
    ]

class AlertStore:
    def __init__(self):
        self.alerts: List[Alert] = []
        self._load_demo_data()

    def _load_demo_data(self):
        a1 = Alert(str(uuid.uuid4()), AlertType.SPILL_DETECTED.value, "HIGH", "Spill Detected", "Major oil spill detected.", "INC-2025-05-20-01", 0, datetime.utcnow().isoformat())
        a2 = Alert(str(uuid.uuid4()), AlertType.HIGH_CONFIDENCE_ATTRIBUTION.value, "HIGH", "High Confidence Attribution", "MT SHIVALIK associated with spill.", "INC-2025-05-20-01", 419001234, datetime.utcnow().isoformat())
        self.alerts.extend([a1, a2])

    def get_all(self):
        return self.alerts

    def add(self, alert: Alert):
        self.alerts.append(alert)

    def acknowledge(self, id: str):
        for a in self.alerts:
            if a.id == id:
                a.acknowledged = True
                return a
        return None

ALERT_STORE = AlertStore()

def broadcast_alert(incident_id: str, alert_type: str, severity: str):
    new_alert = Alert(
        id=str(uuid.uuid4()),
        type=alert_type,
        severity=severity,
        title=f"Alert: {alert_type}",
        message=f"Broadcasted alert for {incident_id}",
        incident_id=incident_id,
        target_mmsi=0,
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    ALERT_STORE.add(new_alert)
    return new_alert
