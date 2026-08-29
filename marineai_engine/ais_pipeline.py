import math
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any

VESSEL_REGISTRY = {
    419001234: {"mmsi": 419001234, "name": "MT SHIVALIK", "type": "Oil Tanker", "flag": "India", "length": 250, "beam": 42, "draft": 14.2, "owner": "ONGC Shipping Ltd", "gross_tonnage": 85000},
    419002345: {"mmsi": 419002345, "name": "MV CHENNAI EXPRESS", "type": "Container Ship", "flag": "India", "length": 180, "beam": 28},
    419003456: {"mmsi": 419003456, "name": "MV KAVERI", "type": "Bulk Carrier", "flag": "Singapore", "length": 190, "beam": 32},
    419004567: {"mmsi": 419004567, "name": "FV MUTHUMARI", "type": "Fishing Vessel", "flag": "India", "length": 35, "beam": 8},
    419005678: {"mmsi": 419005678, "name": "ICGS SAURASHTRA", "type": "Coast Guard", "flag": "India", "length": 105, "beam": 13},
    419006789: {"mmsi": 419006789, "name": "MT DESH RAKSHAK", "type": "Oil Tanker", "flag": "India", "length": 220, "beam": 38},
    419007890: {"mmsi": 419007890, "name": "MV VISHVA VIJAY", "type": "Cargo", "flag": "India", "length": 160, "beam": 25},
    419008901: {"mmsi": 419008901, "name": "CMA CGM COLOMBO", "type": "Container Ship", "flag": "France", "length": 300, "beam": 40},
    419009012: {"mmsi": 419009012, "name": "FV JALAPARI", "type": "Fishing Vessel", "flag": "India", "length": 28, "beam": 7},
    419010123: {"mmsi": 419010123, "name": "MV TIGER GULF", "type": "Bulk Carrier", "flag": "Panama", "length": 210, "beam": 34},
    419011234: {"mmsi": 419011234, "name": "MT CORAL", "type": "Chemical Tanker", "flag": "Marshall Islands", "length": 140, "beam": 22},
    419012345: {"mmsi": 419012345, "name": "MV ASIAN GLORY", "type": "Ro-Ro Cargo", "flag": "Liberia", "length": 195, "beam": 30},
}

def generate_vessel_tracks() -> Dict[int, List[Dict[str, Any]]]:
    tracks = {}
    base_time = datetime.utcnow()
    
    # Vessel A (MT SHIVALIK)
    vessel_a_track = []
    current_time = base_time - timedelta(hours=24)
    lat, lon = 13.5, 80.5
    for i in range(48):
        pos_time = current_time + timedelta(minutes=i*30)
        # Simulate gap
        if 20 <= i <= 21: # ~11.2N, 79.5E
            lat -= 0.05
            lon -= 0.05
            continue
        vessel_a_track.append({
            "mmsi": 419001234, "lat": lat, "lon": lon, 
            "speed": 12.5, "heading": 230, "course": 230, 
            "timestamp": pos_time.isoformat() + "Z", 
            "status": "Underway", "destination": "Tuticorin"
        })
        lat -= 0.05
        lon -= 0.05
    tracks[419001234] = vessel_a_track
    
    # Vessel B
    vessel_b_track = []
    lat, lon = 11.5, 80.5
    for i in range(30):
        pos_time = base_time - timedelta(minutes=(30-i)*30)
        vessel_b_track.append({
            "mmsi": 419002345, "lat": lat, "lon": lon,
            "speed": 18.0, "heading": 270, "course": 270,
            "timestamp": pos_time.isoformat() + "Z",
            "status": "Underway", "destination": "Chennai"
        })
        lon -= 0.08
    tracks[419002345] = vessel_b_track

    # Vessel C
    vessel_c_track = []
    lat, lon = 10.5, 79.8
    for i in range(25):
        pos_time = base_time - timedelta(minutes=(25-i)*30)
        vessel_c_track.append({
            "mmsi": 419003456, "lat": lat, "lon": lon,
            "speed": 14.0, "heading": 0, "course": 0,
            "timestamp": pos_time.isoformat() + "Z",
            "status": "Underway", "destination": "Visakhapatnam"
        })
        lat += 0.06
    tracks[419003456] = vessel_c_track

    # Vessel D
    vessel_d_track = []
    lat, lon = 11.0, 79.2
    for i in range(20):
        pos_time = base_time - timedelta(minutes=(20-i)*30)
        vessel_d_track.append({
            "mmsi": 419004567, "lat": lat + math.sin(i)*0.01, "lon": lon + math.cos(i)*0.01,
            "speed": 5.0, "heading": (i*18) % 360, "course": (i*18) % 360,
            "timestamp": pos_time.isoformat() + "Z",
            "status": "Fishing", "destination": "Local"
        })
    tracks[419004567] = vessel_d_track

    # Add mock data for others
    for mmsi in VESSEL_REGISTRY:
        if mmsi not in tracks:
            tracks[mmsi] = [{
                "mmsi": mmsi, "lat": 12.0, "lon": 80.0,
                "speed": 10.0, "heading": 90, "course": 90,
                "timestamp": base_time.isoformat() + "Z",
                "status": "Underway", "destination": "Unknown"
            }]

    return tracks

# Global tracks cache
_GLOBAL_TRACKS = generate_vessel_tracks()

def get_current_positions() -> List[Dict[str, Any]]:
    positions = []
    for mmsi, track in _GLOBAL_TRACKS.items():
        if not track: continue
        latest = track[-1].copy()
        latest.update(VESSEL_REGISTRY.get(mmsi, {}))
        # Mock anomaly score
        if mmsi == 419001234: latest["anomaly_score"] = 88
        elif mmsi == 419002345: latest["anomaly_score"] = 45
        elif mmsi == 419003456: latest["anomaly_score"] = 22
        elif mmsi == 419004567: latest["anomaly_score"] = 31
        else: latest["anomaly_score"] = 10
        positions.append(latest)
    return positions

def get_vessel_track(mmsi: int) -> List[Dict[str, Any]]:
    return _GLOBAL_TRACKS.get(mmsi, [])

def analyze_ais_gaps(mmsi: int) -> List[Dict[str, Any]]:
    if mmsi == 419001234:
        return [{"duration_minutes": 47, "start_lat": 11.25, "start_lon": 79.55, "end_lat": 11.15, "end_lon": 79.45}]
    return []

def ingest_ais_csv(csv_content: str) -> int:
    lines = csv_content.strip().split('\n')
    if not lines: return 0
    return len(lines) - 1 # Assuming header
