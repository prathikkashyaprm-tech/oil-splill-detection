# MarineGuard AI — SIH 2026 Jury Demonstration & User Guide

Welcome to the **MarineGuard AI** Maritime Surveillance and Environmental Decision Support Command Center.

---

## 1. Quick Start Guide

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start MarineGuard AI
```bash
python run.py
```
*The command will start the FastAPI backend on `http://127.0.0.1:8000` and automatically open the dark maritime command-center dashboard in your default browser.*

---

## 2. Walkthrough of SIH 2026 Presentation Flow

During your Smart India Hackathon presentation, follow this 6-step flow:

### 1. Geospatial Maritime Overview (Dashboard Tab)
- Point out the real-time GIS map showing the **Sentinel-1 SAR swath overlay**, **segmented oil slick boundary (red)**, and **AIS vessel trajectories (cyan/magenta)**.
- Highlight the **Top Metrics HUD** displaying the affected spill area ($42.50\ km^2$), estimated volume in barrels ($\sim 6,683\ bbl$), detection confidence ($94.0\%$), and the top candidate vessel (*MT PACIFIC GLORY*).

### 2. SAR Oil Spill Detection Studio (Detection Tab)
- Demonstrate the **Dual Spectral View**: Raw SAR backscatter vs U-Net segmented mask overlay.
- Explain the **Adaptive Lee speckle filtering** and **GLCM Haralick texture analysis** (homogeneity, contrast, energy, entropy) that rejects calm sea shadows and natural biogenic slicks.
- Point out the **Bonn Agreement (BAOAC)** classification card (*Code 3: Metallic Sheen*).
- Click one of the benchmark preset buttons (*e.g., "NOAA Gulf Slick #1"* or *"Calm Sea Look-alike"*) to demonstrate real-time inference.

### 3. AIS Vessel Behavioral Anomaly & Attribution (Vessels Tab)
- Show the **Candidate Vessel Priority Ranking**.
- Emphasize that *MT PACIFIC GLORY* is ranked #1 with an **Investigation Priority Score of 91/100** because:
  - It passed within **$0.45\ km$** of the slick center.
  - It exhibited an **abrupt speed deceleration of $12.4\ knots$**.
  - It performed an **erratic heading deviation of $62.0^\circ$**.
  - It loitered in the bounding box for **$42\ minutes$**.
- Point to the **Ethical AI Disclaimer** confirming that MarineGuard AI uses objective language (*"Investigation Priority"*) rather than accusing vessels of definitive legal guilt.

### 4. 72-Hour Lagrangian Drift & Physical Weathering (Drift Forecast Tab)
- Review the interactive forecast table displaying $+6h, +12h, +24h, +48h, +72h$ drift intervals.
- Point to the **Evaporation vs Emulsification curves** based on Mackay/ADIOS physics, showing $38.5\%$ volatile evaporation and $52.0\%$ water uptake ("chocolate mousse" formation).

### 5. Marine Biodiversity & Habitat Vulnerability (Ecological Tab)
- Show the **OBIS marine species occurrence records** within the 50 km threat buffer (including the Critically Endangered *Kemp's Ridley Sea Turtle* and *Sperm Whale*).
- Highlight proximity to Marine Protected Areas (MPAs).

### 6. Evidence Fusion Dossier & 1-Click Printable IMO Report (Reports Tab)
- Switch to the **Evidence Fusion** tab to show the 5-pillar synthesized incident dossier.
- Switch to the **IMO Incident Report** tab and click **"Download / Print PDF"** to demonstrate instant export for Coast Guard and Port State Control authorities.
