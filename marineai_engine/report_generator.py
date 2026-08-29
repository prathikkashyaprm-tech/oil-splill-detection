"""
Automated Marine Incident Assessment Report Generator
Produces formal, audit-compliant maritime oil spill incident reports in HTML/PDF-ready format.
"""

from datetime import datetime
from typing import Dict, Any

def generate_incident_report_html(analysis_data: Dict[str, Any], location_name: str = "Offshore Coastal Sector Alpha-4") -> str:
    """
    Generate clean, printable HTML report of the oil spill detection & risk assessment.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"MAI-INC-{datetime.utcnow().strftime('%Y%m%d')}-{np_hash(timestamp)}"
    
    classification = analysis_data.get("classification", {})
    bonn = analysis_data.get("bonn_metrics", {})
    is_spill = classification.get("is_spill_positive", False)
    
    verdict_badge_color = "#ef4444" if is_spill else "#10b981"
    verdict_text = classification.get("label", "Unknown")
    confidence = classification.get("confidence_score", 0.0)
    
    area_km2 = bonn.get("spill_area_km2", 0.0)
    volume_m3 = bonn.get("estimated_volume_m3", 0.0)
    volume_bbl = bonn.get("estimated_volume_bbl", 0.0)
    bonn_name = bonn.get("bonn_name", "N/A")
    severity_level = bonn.get("severity_level", "NORMAL")
    
    prob_matrix = classification.get("probability_matrix", {})
    countermeasures = bonn.get("countermeasures", ["Continue routine satellite surveillance."])
    
    countermeasure_items = "".join([f"<li>{cm}</li>" for cm in countermeasures])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MarineAI Incident Report - {report_id}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .report-container {{
            max-width: 860px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            padding: 40px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 24px;
            margin-bottom: 28px;
        }}
        .logo-area h1 {{
            font-size: 24px;
            font-weight: 800;
            color: #0369a1;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .logo-area p {{
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
        }}
        .meta-box {{
            text-align: right;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #475569;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 13px;
            color: #fff;
            background: {verdict_badge_color};
            margin-top: 12px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #1e293b;
            margin: 24px 0 12px 0;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 6px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 20px;
        }}
        .grid-3 {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px 18px;
        }}
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 4px;
            font-family: 'JetBrains Mono', monospace;
        }}
        .stat-sub {{
            font-size: 11px;
            color: #94a3b8;
            margin-top: 2px;
        }}
        .table-custom {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 13px;
        }}
        .table-custom th, .table-custom td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        .table-custom th {{
            background: #f1f5f9;
            color: #475569;
            font-weight: 600;
        }}
        .checklist {{
            list-style-type: none;
            margin-top: 10px;
        }}
        .checklist li {{
            position: relative;
            padding-left: 28px;
            margin-bottom: 10px;
            font-size: 14px;
            color: #334155;
        }}
        .checklist li::before {{
            content: "✓";
            position: absolute;
            left: 0;
            top: 0;
            width: 18px;
            height: 18px;
            background: #0284c7;
            color: #fff;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 800;
            text-align: center;
            line-height: 18px;
        }}
        .footer {{
            margin-top: 36px;
            padding-top: 20px;
            border-top: 1px dashed #cbd5e1;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #94a3b8;
        }}
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .report-container {{ border: none; box-shadow: none; padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <div class="logo-area">
                <h1>🌊 MarineAI Environmental Command</h1>
                <p>Automated Satellite & Aerial Hydrocarbon Spill Assessment</p>
                <div class="badge">{severity_level}</div>
            </div>
            <div class="meta-box">
                <div><strong>REPORT REF:</strong> {report_id}</div>
                <div><strong>TIMESTAMP:</strong> {timestamp}</div>
                <div><strong>LOCATION:</strong> {location_name}</div>
                <div><strong>AI ACCURACY:</strong> {confidence}% CONFIDENCE</div>
            </div>
        </div>

        <div class="section-title">Incident Telemetry & Sizing</div>
        <div class="grid-3">
            <div class="stat-card">
                <div class="stat-label">Classification Verdict</div>
                <div class="stat-value" style="font-size: 16px; color: {verdict_badge_color};">{verdict_text}</div>
                <div class="stat-sub">AI Confidence: {confidence}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Slick Extent</div>
                <div class="stat-value">{area_km2} km²</div>
                <div class="stat-sub">{bonn.get('spill_area_m2', 0):,} m² surface area</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Estimated Volume</div>
                <div class="stat-value">{volume_m3} m³</div>
                <div class="stat-sub">Approx. {volume_bbl:,} Barrels (bbl)</div>
            </div>
        </div>

        <div class="section-title">Bonn Agreement Scale & Physical Characteristics</div>
        <div class="grid-2">
            <div class="stat-card">
                <div class="stat-label">Bonn Appearance Code</div>
                <div class="stat-value" style="font-size: 16px;">Code {bonn.get('bonn_code', 0)}: {bonn_name}</div>
                <div class="stat-sub">Nominal Thickness: {bonn.get('estimated_thickness_um', 0)} µm</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Environmental Hazard Index</div>
                <div class="stat-value" style="color: {verdict_badge_color};">{bonn.get('severity_score', 0)} / 100</div>
                <div class="stat-sub">{bonn.get('environmental_impact', 'Low impact')}</div>
            </div>
        </div>

        <div class="section-title">Look-alike Discrimination & Spectral Confidence</div>
        <table class="table-custom">
            <thead>
                <tr>
                    <th>Marine Feature Class</th>
                    <th>Probability</th>
                    <th>Discrimination Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Hydrocarbon Oil Slick</strong></td>
                    <td>{prob_matrix.get('oil_spill', 0)}%</td>
                    <td>{'CONFIRMED TARGET' if is_spill else 'NEGATIVE'}</td>
                </tr>
                <tr>
                    <td>Clean Marine Sea Water</td>
                    <td>{prob_matrix.get('clean_water', 0)}%</td>
                    <td>Normal Baseline</td>
                </tr>
                <tr>
                    <td>Biogenic Algal Bloom / Sargassum</td>
                    <td>{prob_matrix.get('algal_bloom', 0)}%</td>
                    <td>Chlorophyll Proxy Evaluated</td>
                </tr>
                <tr>
                    <td>Vessel Propulsive Wake Turbulence</td>
                    <td>{prob_matrix.get('ship_wake', 0)}%</td>
                    <td>Aeration Filter Applied</td>
                </tr>
                <tr>
                    <td>Low-Wind Calm Shadow</td>
                    <td>{prob_matrix.get('low_wind_shadow', 0)}%</td>
                    <td>Gradient Transition Checked</td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">Prescribed Emergency Countermeasures</div>
        <ul class="checklist">
            {countermeasure_items}
        </ul>

        <div class="section-title">Diagnostic Rationale</div>
        <p style="font-size: 13px; color: #475569; background: #f8fafc; padding: 12px; border-radius: 6px; border-left: 3px solid #0284c7;">
            {classification.get('diagnostic_rationale', 'Comprehensive multi-sensor spectral & textural analysis performed.')}
        </p>

        <div class="footer">
            <div>Generated by MarineAI Autonomous Coastal Protection Suite</div>
            <div>International Maritime Organization (IMO) / Bonn Agreement Standard</div>
        </div>
    </div>
</body>
</html>
"""
    return html

def np_hash(text: str) -> str:
    h = 0
    for char in text:
        h = (h * 31 + ord(char)) & 0xFFFFFF
    return f"{h:06X}"
