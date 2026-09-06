# 🌊 MarineGuard AI — Autonomous Maritime Oil-Spill Intelligence & Decision Support System
### 🏆 Smart India Hackathon 2026 | Problem Statement PS-1655

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![PyTorch U-Net](https://img.shields.io/badge/PyTorch-U--Net%20Attention-EE4C2C.svg)](https://pytorch.org/)
[![PostGIS & GeoPandas](https://img.shields.io/badge/GeoSpatial-PostGIS%20%7C%20Leaflet-3388ff.svg)](https://postgis.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Summary

**MarineGuard AI** is a production-grade maritime intelligence platform built for **Smart India Hackathon 2026 (Problem Statement PS-1655)**. The platform integrates:
1. **Sentinel-1 SAR C-Band & NOAA Satellite Image Processing** with adaptive Lee speckle filtering and GLCM Haralick texture analysis.
2. **Deep Attention U-Net PyTorch Segmentation** to isolate oil slicks from natural look-alikes (calm water shadows, biogenic algal blooms).
3. **Bonn Agreement Oil Appearance Code (BAOAC)** quantification ($km^2$ area, volume in $m^3$ and barrels $bbl$, nominal thickness in $\mu m$).
4. **Spatio-Temporal AIS Vessel Correlation & Behavioral Anomaly Engine** computing explainable **Investigation Priority Scores (0–100)** without overclaiming legal culpability.
5. **72-Hour Lagrangian Ocean Drift & Weathering Forecasting** (advection from wind, current vectors, Coriolis deflection, and Mackay volatile evaporation / emulsification curves).
6. **OBIS Marine Biodiversity & Marine Protected Area (MPA) Sensitivity Assessment** (IUCN Red Listed taxa exposure and habitat vulnerability ratings: *LOW / MEDIUM / HIGH / CRITICAL*).
7. **Climate & Oceanographic Context** (Sea Surface Temperature, SST anomalies, marine heatwaves, wind rose, surface current vectors).
8. **Pre-Incident Maritime Risk Assessment Layer** modeling shipping density, tanker congestion, and weather hazards.
9. **Multi-Source Evidence Fusion Dossier** and **1-Click Printable IMO/Bonn Incident Assessment Reports**.
10. **Dark Cyber-Maritime Command Center UI** with interactive Leaflet GIS mapping, split spectral comparison, and preloaded NOAA / Sentinel-1 demo scenarios.

---

## 🏗️ System Architecture & Workflow Pipeline

```
[ Sentinel-1 SAR / NOAA Imagery ]
                │
                ▼
[ Preprocessing: Lee Filter + Haralick GLCM Texture ]
                │
                ▼
[ Attention U-Net Segmentation (PyTorch) ]
                │
                ▼
[ Contour Polygonizer + Bonn Scale Quantification ]
                │
                ├────────────────────────────────────────┐
                ▼                                        ▼
[ Spatio-Temporal AIS Spatial Queries ]   [ MetOcean Forcing: Wind, Currents, Waves ]
                │                                        │
                ▼                                        ▼
[ Kinematic Anomaly & Priority Scorer ]   [ 72h Lagrangian Particle Drift & Weathering ]
                │                                        │
                ├────────────────────────────────────────┘
                ▼
[ OBIS Marine Biodiversity & MPA Sensitivity Assessment ]
                │
                ▼
[ Multi-Source Evidence Fusion & Response Playbook ]
                │
                ▼
[ Dark Maritime Command-Center Dashboard (FastAPI + Leaflet + Chart.js) ]
```

---

## 📂 Project Directory Structure

```
marineguard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py              # REST API endpoints (incidents, spills, vessels, attribution, etc.)
│   │   ├── core/
│   │   │   ├── config.py                 # Environment and system settings
│   │   │   └── database.py               # SQLAlchemy 2.0 & database session manager
│   │   ├── models/
│   │   │   └── schema.py                 # 12 SQLAlchemy/PostGIS database models
│   │   ├── schemas/
│   │   │   └── pydantic_models.py        # Pydantic request and response schemas
│   │   └── services/
│   │       ├── sar_detection.py          # SAR preprocessing, Lee filter, U-Net inference, Bonn metrics
│   │       ├── ais_service.py            # AIS ingestion & spatio-temporal spatial queries
│   │       ├── vessel_behavior.py        # Anomaly scoring & explainable 0-100 Investigation Priority
│   │       ├── trajectory_simulator.py   # 72h Lagrangian drift & physical weathering decay
│   │       ├── ecological_service.py     # OBIS marine species & MPA vulnerability assessment
│   │       ├── environmental_service.py  # SST, SST anomalies, heatwaves, MetOcean vectors
│   │       ├── risk_assessment.py        # Pre-incident predictive shipping risk layer
│   │       ├── evidence_fusion.py        # Multi-pillar incident dossier synthesizer
│   │       └── demo_scenarios.py         # Preloaded NOAA & Sentinel-1 incident replays
│   ├── main.py                           # FastAPI application entrypoint
│   └── requirements.txt                  # Backend dependencies
├── ml/
│   ├── models/
│   │   └── unet.py                       # Attention U-Net PyTorch architecture
│   ├── dataset/
│   │   └── noaa_loader.py                # NOAA NESDIS & Sentinel-1 dataset loader and synthetic generator
│   ├── train.py                          # PyTorch training pipeline with Dice + BCE Loss
│   ├── evaluate.py                       # Quantitative benchmark evaluation (IoU, Dice, Precision, Recall)
│   └── inference.py                      # Production SAR inference engine
├── data/
│   ├── sar/                              # NOAA SAR imagery & ground-truth masks
│   ├── ais/                              # Multi-scenario AIS vessel tracks & telemetry
│   ├── biodiversity/                     # OBIS species records & Marine Protected Areas
│   └── environmental/                    # SST, wind, wave, and surface current vector presets
├── notebooks/
│   └── marineguard_eda_and_model_training.ipynb  # Interactive EDA & ML training notebook
├── static/
│   ├── index.html                        # Glassmorphic cyber-maritime command UI
│   ├── css/
│   │   └── style.css                     # Responsive dark maritime stylesheet
│   └── js/
│       └── app.js                        # Frontend controller, Leaflet GIS, Chart.js analytics
├── docs/
│   ├── SIH_PS1655_ARCHITECTURE.md        # Technical architecture document
│   ├── API_DOCUMENTATION.md              # REST API specification
│   └── USER_GUIDE.md                     # Jury demonstration walkthrough guide
├── tests/
│   └── test_marineguard.py               # Automated unit & integration test suite
├── docker-compose.yml                    # PostGIS 15 + Backend orchestration
├── Dockerfile.backend
├── requirements.txt
├── run.py                                # 1-Click launcher
└── app.py                                # Root ASGI app bridge
```

---

## 🚀 Quick Start Guide

### 1. Installation
Ensure Python 3.10+ is installed. Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. 1-Click Launch
Start the application and automatically open the command center in your browser:

```bash
python run.py
```
Or run directly via Uvicorn:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to **`http://127.0.0.1:8000`** in your browser.

---

## 🧪 Running Automated Tests

Run the complete test suite verifying SAR U-Net detection, Bonn quantification, AIS behavioral priority ranking, Lagrangian drift, OBIS ecological scoring, and REST API endpoints:

```bash
python -m unittest tests/test_marineguard.py
```

---

## 📊 Machine Learning Model Training & Benchmarking

### Train U-Net on NOAA SAR Benchmark Dataset
```bash
python ml/train.py --epochs 10 --batch-size 8 --data data/sar --save models/unet_sar_oilspill.pth
```

### Evaluate Model Performance
```bash
python ml/evaluate.py --data data/sar --model models/unet_sar_oilspill.pth
```

---

## 🐳 Docker Deployment

To launch the full production environment with **PostgreSQL 15 + PostGIS 3.3** and FastAPI backend:

```bash
docker-compose up --build
```

---

## ⚖️ Ethical AI & Surveillance Notice
MarineGuard AI strictly enforces objective terminology. Candidate vessel associations are designated as **"Investigation Priority"** and **"Association Confidence"** ($0 - 100$), and ecological metrics represent **"Potential Ecological Exposure"**. The platform acts as an explainable decision support tool for coast guards and maritime regulatory bodies.
