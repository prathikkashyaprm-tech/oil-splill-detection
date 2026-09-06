# MarineGuard AI — REST API Documentation

Base URL: `http://localhost:8000/api`

Interactive Swagger UI: `http://localhost:8000/docs`  
Interactive ReDoc UI: `http://localhost:8000/redoc`

---

## Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/demo/scenarios` | List available preloaded NOAA/Sentinel-1 demo incident scenarios |
| `POST` | `/api/demo/load-scenario` | Load a specific demo scenario and retrieve complete intelligence dossier |
| `GET` | `/api/incidents` | Retrieve list of active and historical maritime incidents |
| `GET` | `/api/incidents/{id}` | Retrieve complete multi-pillar evidence fusion dossier for an incident |
| `GET` | `/api/spills` | List all detected oil spill events |
| `GET` | `/api/spills/{id}` | Get specific spill detection, polygon, and Bonn quantification details |
| `GET` | `/api/vessels` | List active AIS vessels in surveillance box |
| `GET` | `/api/vessels/{mmsi}` | Get vessel specifications and voyage details |
| `GET` | `/api/vessels/{mmsi}/trajectory` | Retrieve historical AIS trajectory positions |
| `GET` | `/api/vessels/nearby` | Spatial query for vessels near a geographic point |
| `GET` | `/api/attribution/{incident_id}` | Get candidate vessel rankings and explainable investigation priority scores |
| `GET` | `/api/trajectory/{spill_id}` | Get 72-hour Lagrangian drift forecast and weathering curves |
| `GET` | `/api/ecological-impact/{spill_id}` | Retrieve OBIS marine species vulnerability assessment |
| `GET` | `/api/environment/{spill_id}` | Get Sea Surface Temperature, anomalies, and MetOcean vectors |
| `GET` | `/api/risk-zones` | Retrieve pre-incident maritime risk map layers |
| `POST` | `/api/detect-spill` | Upload SAR image / pass sample ID to execute real-time U-Net segmentation |

---

## Key Payload Examples

### `POST /api/detect-spill`
**Parameters (Form-Data)**:
- `file`: (Binary image file, optional)
- `sample_id`: `"noaa_gulf_slick_01_001"` (Optional preset ID)
- `center_lat`: `28.7350`
- `center_lon`: `-88.3820`
- `pixel_res_m`: `10.0`

**Response (Sample)**:
```json
{
  "scenario_id": "live_upload_MG-LIVE-104500",
  "incident_id": "MG-LIVE-104500",
  "spill_detection": {
    "id": "SPILL_MG-LIVE-104500",
    "affected_area_km2": 42.50,
    "confidence_score": 0.94,
    "bonn_code": 3,
    "bonn_description": "Code 3: Metallic",
    "estimated_volume_bbl": 6683.0,
    "spill_polygon_geojson": { "type": "Polygon", "coordinates": [...] },
    "raw_image_url": "data:image/png;base64,...",
    "overlay_image_url": "data:image/png;base64,..."
  },
  "candidate_vessels": [
    {
      "rank": 1,
      "vessel": { "mmsi": "356891000", "vessel_name": "MT PACIFIC GLORY", "vessel_type": "Crude Oil Tanker" },
      "metrics": {
        "investigation_priority_score": 91.0,
        "min_distance_km": 0.45,
        "speed_anomaly_drop_kn": 12.4,
        "route_deviation_deg": 62.0,
        "temporal_overlap_rating": "HIGH",
        "anomaly_flags": [
          "Immediate Proximity: Passed within 0.45 km of slick center",
          "Abrupt Speed Drop: Decelerated by 12.4 knots inside surveillance box"
        ]
      }
    }
  ]
}
```
