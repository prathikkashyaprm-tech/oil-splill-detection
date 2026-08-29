# 🌊 MarineAI: Multi-Modal Marine Oil Spill Detection & Environmental Monitoring System

An autonomous, state-of-the-art computer vision and geospatial platform for detecting, segmenting, and quantifying marine oil spills from **Synthetic Aperture Radar (SAR)** satellite imagery and **Drone / Satellite Optical RGB** feeds.

---

## 🌟 Key Features

1. **Multi-Modal AI Detection Engine**:
   - **SAR Dark-Spot Detection**: Adaptive Lee speckle noise filtering, hysteresis thresholding, morphological clustering, and Gray Level Co-occurrence Matrix (GLCM) textural descriptors (homogeneity, contrast, energy, entropy).
   - **Optical & Drone RGB Slick Analysis**: Hydrocarbon absorption indexing, iridescent sheen analysis, and multi-threshold chromatic deconvolution.
   - **Look-alike Discrimination**: Rejects natural false positives such as biogenic algal blooms (Sargassum/Red Tide), low-wind calm sea shadows, and vessel propulsive wakes.

2. **International Maritime Standards**:
   - **Bonn Agreement Oil Appearance Code (BAOAC)**: Classifies slick appearance from Code 1 (Sheen) to Code 5 (Continuous True Oil Color).
   - **Quantitative Sizing**: Computes affected area in $km^2$, estimated volume in cubic meters ($m^3$) and 42-gallon barrels ($bbl$), and nominal film thickness in micrometers ($\mu m$).

3. **72-Hour Lagrangian Ocean Drift & Weathering Simulator**:
   - Advection modeling factoring in 10m wind velocity (with Coriolis deflection angle) and surface current vectors.
   - Physical weathering curves: volatile evaporation decay % and emulsification water uptake % over 72 hours.
   - Shoreline collision threat trajectory plotted on interactive GIS maps.

4. **Geospatial Command & Control Dashboard**:
   - Real-time Leaflet GIS mapping with simulated Sentinel-1 SAR swaths, AIS live vessel traffic, and active slick markers.
   - Dual-view spectral comparison: Raw Source Image vs. AI Segmented Mask + Contour HUD + Split comparison slider.
   - 1-Click Printable/Downloadable Official IMO/Bonn Marine Incident Assessment Report.

---

## 🚀 Quick Start Guide

### 1. Requirements
Ensure Python 3.9+ is installed.

```bash
pip install -r requirements.txt
```

### 2. Launch the Application

Run the 1-click startup script (this starts the server and opens your browser at `http://127.0.0.1:8000`):

```bash
python run.py
```

Or start with Uvicorn directly:

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

---

## 🧪 Running Automated Tests

To run the complete automated test suite validating detection accuracy, SAR/optical algorithms, Bonn metrics, and drift physics:

```bash
python -m unittest tests/test_detector.py
```

---

## 📂 Project Architecture

```
os/
├── app.py                      # FastAPI web server and REST API endpoints
├── run.py                      # 1-click launcher with auto browser launch
├── requirements.txt            # Python dependencies
├── marineai_engine/            # AI Core Detection & Analysis Module
│   ├── __init__.py
│   ├── detector.py             # Main detection orchestrator & overlay generator
│   ├── sar_analyzer.py         # SAR speckle filtering (Lee filter), dark-spots, GLCM texture
│   ├── optical_analyzer.py     # Drone & Optical RGB multi-spectral proxy & slick segmentation
│   ├── classifier.py           # ML & Rule-based ensemble classifier (Spill vs Look-alikes)
│   ├── drift_simulator.py      # Lagrangian particle drift & coastline trajectory simulation
│   ├── bonn_scale.py           # Bonn Agreement oil thickness & volume estimation
│   ├── report_generator.py     # Automated marine incident PDF/HTML report generator
│   └── sample_generator.py     # Benchmark SAR / drone test dataset generator
├── static/                     # Web Frontend
│   ├── index.html              # Glassmorphic maritime command UI
│   ├── css/
│   │   └── style.css           # Responsive styles, dark ocean aesthetic, animations
│   ├── js/
│   │   ├── app.js              # UI controller, drag & drop, HUD updates
│   │   ├── map.js              # Leaflet GIS integration, satellite swaths, AIS ships
│   │   ├── charts.js           # Weathering decay canvas charts
│   │   └── api.js              # API communication layer
│   └── samples/                # Benchmark test satellite & drone images
└── tests/
    └── test_detector.py        # Automated test suite
```

---

## 📡 REST API Documentation

- `POST /api/detect`: Run detection on uploaded image or sample preset.
- `POST /api/simulate-drift`: Compute 72h Lagrangian particle drift trajectory and physical weathering.
- `GET /api/samples`: Retrieve available benchmark satellite & drone imagery.
- `GET /api/hotspots`: Retrieve global offshore monitoring zones and active telemetry.
- `POST /api/generate-report`: Produce formatted HTML incident assessment report.
- `GET /api/health`: Health status & active AI models.

---

## ⚖️ Standards Compliance
- **Bonn Agreement Oil Appearance Code (BAOAC)**
- **International Maritime Organization (IMO) Tier-1/2/3 Response Protocol**
- **Lagrangian Surface Advection Physical Model**
