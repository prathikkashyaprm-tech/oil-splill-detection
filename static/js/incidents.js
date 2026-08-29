/**
 * MarineGuard AI - Incident Intelligence Module
 */
const IncidentModule = {
  currentIncident: null,
  _incidents: [],

  async init() {
    try {
      const data = await fetch('/api/incidents').then(r => r.json());
      if (Array.isArray(data) && data.length > 0) {
        this._incidents = data;
      } else {
        this._incidents = this._demoIncidents();
      }
    } catch(e) {
      this._incidents = this._demoIncidents();
    }

    this.renderIncidentList(this._incidents);
    // Auto-load primary incident
    const primary = this._incidents.find(i => i.id === 'INC-2025-05-20-01') || this._incidents[0];
    if (primary) this.renderIncidentPanel(primary);
  },

  _demoIncidents() {
    return [
      {
        id: 'INC-2025-05-20-01',
        title: 'Major Oil Spill — Bay of Bengal',
        status: 'INVESTIGATING',
        severity: 'HIGH',
        lat: 10.820,
        lon: 79.130,
        location_name: 'Bay of Bengal, 42km SE of Puducherry',
        area_km2: 4.8,
        confidence: 91,
        detection_time: '2025-05-20T14:32:00Z',
        bonn_code: 3,
        detection_method: 'SAR Satellite',
        satellite_scene: 'RISAT-2B-SCENE-8849',
        primary_vessel_mmsi: 419001234,
        timeline: [
          { time: '2025-05-20T12:00:00Z', event: 'Initial SAR satellite scan pass' },
          { time: '2025-05-20T12:15:00Z', event: 'Anomaly flagged by AIS monitoring — MT SHIVALIK dark' },
          { time: '2025-05-20T13:00:00Z', event: 'Second satellite pass requested — Sentinel-1A tasked' },
          { time: '2025-05-20T14:00:00Z', event: 'Oil spill patch confirmed — AI confidence 87%' },
          { time: '2025-05-20T14:32:00Z', event: 'AI confidence upgraded to 91% — CONFIRMED' },
          { time: '2025-05-20T15:00:00Z', event: 'Indian Coast Guard notification dispatched' }
        ]
      },
      {
        id: 'INC-2025-05-18-02',
        title: 'Minor Discharge — Palk Strait',
        status: 'CLOSED',
        severity: 'MEDIUM',
        lat: 11.1,
        lon: 80.1,
        location_name: 'Palk Strait',
        area_km2: 1.2,
        confidence: 80,
        detection_time: '2025-05-18T10:00:00Z',
        bonn_code: 1,
        detection_method: 'Optical Satellite',
        satellite_scene: 'S2A-SCENE-1122'
      },
      {
        id: 'INC-2025-05-15-03',
        title: 'Large Anomaly — Deep Water',
        status: 'INVESTIGATING',
        severity: 'HIGH',
        lat: 12.1,
        lon: 81.1,
        location_name: 'Bay of Bengal Deep Water Zone',
        area_km2: 8.5,
        confidence: 88,
        detection_time: '2025-05-15T08:00:00Z',
        bonn_code: 4,
        detection_method: 'SAR Satellite',
        satellite_scene: 'RS2-SCENE-7733'
      }
    ];
  },

  selectIncident(id) {
    const inc = this._incidents.find(i => i.id === id);
    if (inc) {
      this.renderIncidentPanel(inc);
      if (window.MapModule) MapModule.focusIncident(inc);
      app.switchTab('dashboard');
    }
  },

  renderIncidentList(incidents) {
    const grid = document.getElementById('incidents-grid');
    if (!grid) return;
    grid.innerHTML = incidents.map(inc => `
      <div onclick="IncidentModule.selectIncident('${inc.id}')"
        style="background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:8px;padding:16px;cursor:pointer;
               transition:all 0.2s;border-left:4px solid ${inc.severity==='HIGH'?'var(--accent-crimson)':inc.severity==='MEDIUM'?'var(--accent-amber)':'var(--accent-cyan)'}"
        onmouseover="this.style.borderColor='var(--accent-cyan)'" 
        onmouseout="this.style.borderLeftColor='${inc.severity==='HIGH'?'var(--accent-crimson)':inc.severity==='MEDIUM'?'var(--accent-amber)':'var(--accent-cyan)'}';this.style.borderColor='var(--border-subtle)'">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent-cyan)">${inc.id}</div>
          <span class="badge ${inc.severity.toLowerCase()}">${inc.status}</span>
        </div>
        <div style="font-weight:700;font-size:13px;color:var(--text-primary);margin-bottom:6px">${inc.title}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:10px">${inc.location_name}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div style="background:var(--bg-surface);padding:8px;border-radius:4px;text-align:center">
            <div style="font-size:10px;color:var(--text-muted)">Spill Area</div>
            <div style="font-weight:700;font-size:15px;color:var(--text-primary)">${inc.area_km2} km²</div>
          </div>
          <div style="background:var(--bg-surface);padding:8px;border-radius:4px;text-align:center">
            <div style="font-size:10px;color:var(--text-muted)">AI Confidence</div>
            <div style="font-weight:700;font-size:15px;color:var(--accent-cyan)">${inc.confidence}%</div>
          </div>
        </div>
        <div style="margin-top:10px;font-size:11px;color:var(--text-muted)">
          🛰️ ${inc.detection_method} &nbsp;|&nbsp; Bonn Code ${inc.bonn_code} &nbsp;|&nbsp; ${inc.detection_time?.slice(0,16).replace('T',' ')} UTC
        </div>
        <div style="display:flex;gap:8px;margin-top:12px">
          <button onclick="event.stopPropagation();ReportModule.generateReport('${inc.id}')" class="btn btn-primary" style="flex:1;font-size:11px;padding:6px">📄 Report</button>
          ${inc.status !== 'CLOSED' ? `<button onclick="event.stopPropagation();IncidentModule.closeIncident('${inc.id}')" class="btn btn-outline" style="flex:1;font-size:11px;padding:6px">✓ Close</button>` : ''}
        </div>
      </div>
    `).join('');
  },

  renderIncidentPanel(incident) {
    this.currentIncident = incident;
    const header = document.querySelector('.panel-header h2');
    if (header) header.textContent = `Incident: #${incident.id}`;

    const content = document.querySelector('.panel-content');
    if (!content) return;

    const attributions = [
      { vessel_name: 'Vessel A (MT SHIVALIK)', mmsi: 419001234, combined_score: 91, vessel_type: 'Oil Tanker', dist: '1.8 km', time: '37 min', anom: '88%' },
      { vessel_name: 'Vessel B', mmsi: 419002345, combined_score: 31, vessel_type: 'Container Ship', dist: '14.2 km', time: '12 min', anom: '45%' },
      { vessel_name: 'Vessel C', mmsi: 419003456, combined_score: 12, vessel_type: 'Bulk Carrier', dist: '28.6 km', time: '05 min', anom: '22%' },
      { vessel_name: 'Vessel D', mmsi: 419004567, combined_score: 8, vessel_type: 'Fishing Vessel', dist: '34.1 km', time: '18 min', anom: '31%' },
    ];
    const primary = attributions[0];
    const others = attributions.slice(1);

    content.innerHTML = `
      <div class="status-banner">
        <h4>🚨 ${incident.severity === 'HIGH' ? 'CONFIRMED' : 'SUSPECTED'} OIL SPILL</h4>
        <p>Detected: ${incident.detection_time ? incident.detection_time.slice(0,16).replace('T',' ') : '20 May 2025, 14:32'} UTC<br>Status: <b style="color:var(--text-primary)">${incident.status === 'INVESTIGATING' ? 'Under Investigation' : incident.status}</b></p>
      </div>

      <div class="metrics-grid">
        <div class="metric-box" style="grid-column: 1 / -1;">
          <div class="label">Location</div>
          <div class="val" style="font-size:12px">${incident.lat || 10.820}° N, ${incident.lon || 79.130}° E<br><span style="color:var(--text-muted);font-size:10px">${incident.location_name || 'Bay of Bengal'}</span></div>
        </div>
        <div class="metric-box">
          <div class="label">Affected Area</div>
          <div class="val">${incident.area_km2 || 4.8} km²</div>
        </div>
        <div class="metric-box">
          <div class="label">Confidence</div>
          <div class="val" style="color:var(--accent-emerald)">${incident.confidence || 91}%</div>
        </div>
      </div>

      <div class="section-title">Most Probable Source</div>
      <div class="probable-source">
        <div class="source-header">
          <div class="source-title">🚢 ${primary.vessel_name}</div>
          <div class="score-large">${primary.combined_score}%</div>
        </div>
        <div class="source-details">
          MMSI: <span>${primary.mmsi}</span><br>
          Vessel Type: <span>${primary.vessel_type}</span><br>
          Distance from Spill: <span>${primary.dist}</span><br>
          Time in Area: <span>${primary.time}</span><br>
          Behavior Anomaly Score: <span style="color:var(--accent-crimson)">${primary.anom}</span>
        </div>
      </div>

      <div class="section-title">Other Nearby Vessels</div>
      ${others.map(v => `
        <div class="nearby-vessel">
          <div>
            <div style="font-weight:600;font-size:12px">${v.vessel_name}</div>
            <div style="font-size:10px;color:var(--text-muted)">MMSI: ${v.mmsi}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:12.5px;font-weight:700;color:${v.combined_score>50?'var(--accent-crimson)':v.combined_score>20?'var(--accent-amber)':'var(--accent-cyan)'}">Score: ${String(v.combined_score).padStart(2,'0')}%</div>
          </div>
        </div>`).join('')}

      <div class="section-title">Recommended Actions</div>
      <ul class="checklist">
        <li><span style="color:var(--accent-emerald)">✔</span> Alert Coastal Authorities</li>
        <li><span style="color:var(--accent-emerald)">✔</span> Notify Nearby Vessels</li>
        <li><span style="color:var(--accent-cyan)">✔</span> Task High Resolution Satellite</li>
        <li><span style="color:var(--accent-amber)">○</span> Prepare Response Units</li>
      </ul>

      <div class="action-buttons">
        <button class="btn btn-primary" onclick="ReportModule.generateReport('${incident.id}')">📄 Generate Report</button>
        <button class="btn btn-outline" onclick="IncidentModule.closeIncident('${incident.id}')">Mark as Closed</button>
      </div>
    `;
  },

  async closeIncident(id) {
    try {
      await fetch(`/api/incidents/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'CLOSED' })
      });
      app.showNotification(`✅ Incident ${id} marked as closed`, 'success');
      this.init();
    } catch(e) {
      app.showNotification('❌ Failed to update incident', 'error');
    }
  }
};
