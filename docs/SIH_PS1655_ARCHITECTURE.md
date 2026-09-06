# MarineGuard AI — Architectural Specification (SIH 2026 PS-1655)

## Problem Statement PS-1655: Intelligent Maritime Oil-Spill Detection, Vessel Attribution & Ecological Impact

MarineGuard AI is designed to solve the critical challenges in maritime environmental surveillance:
1. **Differentiating true mineral oil spills from look-alikes** (such as biogenic algal blooms, wind shadows, and internal waves).
2. **Attributing candidate vessels** without overclaiming definitive guilt, utilizing multi-factor spatio-temporal and kinematic anomaly analytics.
3. **Forecasting 72-hour Lagrangian ocean drift and physical weathering** (Mackay evaporation & emulsification).
4. **Quantifying exposure of endangered marine biodiversity (OBIS) and Marine Protected Areas (MPAs)**.
5. **Fusing multi-source intelligence into an explainable, audit-ready Incident Assessment Dossier**.

---

## High-Level Architecture Pipeline

```
[ Sentinel-1 SAR / NOAA NESDIS Imagery ]
                 │
                 ▼
[ Preprocessing: Lee Filter + Haralick GLCM Descriptors ]
                 │
                 ▼
[ Deep Attention U-Net Segmentation Engine (PyTorch) ]
                 │
                 ▼
[ Contour GeoJSON Polygonizer + Bonn Appearance Sizing ]
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
[ Dark Command-Center Dashboard (Leaflet + Chart.js + FastAPI) ]
```

---

## 1. SAR Preprocessing & Deep Learning Segmentation
- **Adaptive Lee Filter**: Removes multiplicative speckle noise while retaining sharp edge boundaries.
- **Attention U-Net**: Downsampling encoder with skip connections through attention gates that selectively weight dark hydrocarbon signatures over calm sea patches.
- **Look-alike Discrimination**: Computes GLCM textural homogeneity, contrast, energy, and entropy to distinguish low-wind sea slicks from viscous crude slicks.
- **Bonn Agreement Oil Appearance Code (BAOAC)**: Classifies slicks from Code 1 (Sheen: $0.04 - 0.30\ \mu m$) to Code 5 (Continuous True Oil: $>200\ \mu m$) and computes volumetric discharge in cubic meters and 42-gallon barrels.

---

## 2. AIS Spatio-Temporal Correlation & Behavioral Anomaly Engine
- Correlates all vessel positions within a 30 km spatial radius and $\pm 12$ hour temporal window of the detected slick.
- **Kinematic Anomaly Features**:
  - Distance of closest approach ($d_{min}$)
  - Course deviation off designated shipping corridors ($\Delta \theta$)
  - Abrupt speed deceleration ($\Delta v$) indicating loitering, engine halting, or illegal bilge discharge
  - Dwell time within spill bounding box
  - Vessel cargo hazard category (Crude tanker vs general cargo)
- Synthesizes an explainable **Investigation Priority Score** ($0 - 100$).
- **Ethical Directive**: Output explicitly states *"Investigation Priority"* and *"Candidate Vessel"*, preserving objective neutrality.

---

## 3. 72-Hour Lagrangian Drift & Weathering Forecasting
- **Advection Vector**:
  $$\vec{V}_{drift} = \vec{V}_{current} + 0.03 \cdot \vec{V}_{wind} \cdot \mathbf{R}(\theta_{Coriolis})$$
- **Physical Weathering (Mackay / ADIOS Formulation)**:
  - Volatile evaporative fraction: $F_{evap}(t) = \alpha \cdot \ln(1 + \beta \cdot t)$
  - Water-in-oil emulsification: $Y(t) = Y_{max} \cdot (1 - e^{-k \cdot t})$
- Generates future polygon bounding cones at $+6h, +12h, +24h, +48h, +72h$.

---

## 4. OBIS Marine Biodiversity & Ecological Risk Assessment
- Intersects spill coordinates and forecasted drift corridors with **OBIS (Ocean Biodiversity Information System)** occurrence records.
- Evaluates proximity to IUCN Red Listed species (Critically Endangered Kemp's Ridley Sea Turtle, Sperm Whale, Bluefin Tuna spawning grounds) and Marine Protected Areas (MPAs).
- Produces categorical risk rating: **LOW / MEDIUM / HIGH / CRITICAL**.

---

## 5. Pre-Incident Maritime Risk Assessment
- Proactive predictive layer modeling shipping lane traffic density, tanker percentages, and regional climatological hazards to identify high-risk corridors before incidents occur.
