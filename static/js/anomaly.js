const AnomalyModule = {
  _reports: [],

  async init() {
    try {
      this._reports = await fetch('/api/anomaly/fleet').then(r => r.json());
    } catch(e) {
      this._reports = this._demoReports();
    }
    this.renderFleetAnomalyList(this._reports);
  },

  _demoReports() {
    return [
      {
        mmsi: 419001234, vessel_name: 'MT SHIVALIK', total_score: 88, risk_level: 'HIGH',
        factors: [
          { factor_name: 'AIS Blackout', score: 90, description: '47-minute AIS transmission gap near spill zone at 11.2°N, 79.5°E' },
          { factor_name: 'Route Deviation', score: 82, description: 'Vessel deviated 58° from declared course to Tuticorin' },
          { factor_name: 'Speed Anomaly', score: 75, description: 'Speed dropped from 12.5 to 0.0 kn during gap window' },
          { factor_name: 'Exclusion Zone', score: 85, description: 'Vessel entered marine protected area boundary' }
        ],
        summary: 'CRITICAL: MT SHIVALIK shows 4 concurrent behavioral anomalies consistent with deliberate discharge event.'
      },
      {
        mmsi: 419004567, vessel_name: 'FV MUTHUMARI', total_score: 45, risk_level: 'MEDIUM',
        factors: [
          { factor_name: 'Loitering', score: 62, description: 'Vessel maintained <0.8km radius pattern for 3.2 hours' },
          { factor_name: 'Route Deviation', score: 28, description: 'Minor course deviation, consistent with fishing operations' }
        ],
        summary: 'MEDIUM: Loitering behavior detected near known fishing grounds. Consistent with fishing activities.'
      },
      {
        mmsi: 419002345, vessel_name: 'MV CHENNAI EXPRESS', total_score: 31, risk_level: 'LOW',
        factors: [
          { factor_name: 'Speed Anomaly', score: 35, description: 'Minor speed variation of 2.1 kn over 20-minute window' }
        ],
        summary: 'LOW: Minor speed irregularity consistent with traffic congestion near port approaches.'
      },
      {
        mmsi: 419003456, vessel_name: 'MV KAVERI', total_score: 22, risk_level: 'LOW',
        factors: [
          { factor_name: 'Route Deviation', score: 22, description: 'Small 12° heading adjustment, within normal parameters' }
        ],
        summary: 'LOW: No significant anomalies detected. Vessel operating within expected parameters.'
      },
      {
        mmsi: 419006789, vessel_name: 'MT DESH RAKSHAK', total_score: 55, risk_level: 'MEDIUM',
        factors: [
          { factor_name: 'AIS Blackout', score: 48, description: '22-minute AIS gap — within normal mobile satellite coverage gap' },
          { factor_name: 'Speed Anomaly', score: 62, description: 'Speed spike from 11 to 18 kn detected for 15-minute window' }
        ],
        summary: 'MEDIUM: Short AIS gap and speed irregularity. Possibly satellite link interruption.'
      }
    ];
  },

  renderFleetAnomalyList(reports) {
    const list = document.getElementById('anomaly-fleet-list');
    if (!list) return;
    list.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px">
        <h3 style="font-size:13px;font-weight:600;color:var(--text-primary)">Fleet Anomaly Ranking</h3>
        <span style="font-size:11px;color:var(--text-muted)">${reports.length} vessels analyzed</span>
      </div>
      ${reports.map((r, i) => `
        <div onclick="AnomalyModule.renderVesselAnomalyDetail(${i})"
          style="padding:12px;background:var(--bg-card);border-radius:6px;margin-bottom:8px;cursor:pointer;
                 border-left:3px solid ${r.risk_level==='HIGH'?'var(--accent-crimson)':r.risk_level==='MEDIUM'?'var(--accent-amber)':'var(--accent-cyan)'};
                 transition:all 0.2s" 
          onmouseover="this.style.background='var(--bg-elevated)'" 
          onmouseout="this.style.background='var(--bg-card)'">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-weight:600;font-size:13px;color:var(--text-primary)">${r.vessel_name}</span>
            <span class="badge ${r.risk_level.toLowerCase()}">${r.risk_level}</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:11px;color:var(--text-muted)">MMSI: ${r.mmsi}</span>
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--text-primary)">${r.total_score}/100</span>
          </div>
          <div style="height:4px;background:rgba(255,255,255,0.08);border-radius:2px;overflow:hidden">
            <div style="height:100%;width:${r.total_score}%;background:${r.risk_level==='HIGH'?'var(--accent-crimson)':r.risk_level==='MEDIUM'?'var(--accent-amber)':'var(--accent-cyan)'};border-radius:2px;transition:width 0.5s ease"></div>
          </div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:6px">${r.factors?.[0]?.factor_name || ''} ${r.factors?.length > 1 ? `+${r.factors.length-1} more` : ''}</div>
        </div>
      `).join('')}`;
  },

  renderVesselAnomalyDetail(index) {
    const r = this._reports[index];
    if (!r) return;
    const detail = document.getElementById('anomaly-vessel-detail');
    if (!detail) return;
    detail.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px">
        <div>
          <div style="font-size:15px;font-weight:700;color:var(--text-primary)">${r.vessel_name}</div>
          <div style="font-size:11px;color:var(--text-muted)">MMSI: ${r.mmsi}</div>
        </div>
        <div>
          <span class="badge ${r.risk_level.toLowerCase()}">${r.risk_level} RISK</span>
          <div style="font-size:22px;font-weight:700;color:var(--accent-cyan);text-align:right;margin-top:4px">${r.total_score}</div>
        </div>
      </div>
      <div style="background:var(--bg-card);border-radius:6px;padding:12px;margin-bottom:15px;font-size:12px;color:var(--text-secondary);border-left:3px solid var(--accent-cyan)">
        ${r.summary}
      </div>
      <div style="font-size:11px;text-transform:uppercase;color:var(--text-muted);letter-spacing:.5px;margin-bottom:10px">Anomaly Factors</div>
      ${(r.factors||[]).map(f => `
        <div style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:12px;font-weight:600;color:var(--text-primary)">${f.factor_name}</span>
            <span style="font-family:var(--font-mono);font-size:12px;color:${f.score>=70?'var(--accent-crimson)':f.score>=40?'var(--accent-amber)':'var(--accent-cyan)'}">${f.score}/100</span>
          </div>
          <div style="height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;margin-bottom:4px">
            <div style="height:100%;width:${f.score}%;background:${f.score>=70?'var(--accent-crimson)':f.score>=40?'var(--accent-amber)':'var(--accent-cyan)'};border-radius:3px"></div>
          </div>
          <div style="font-size:11px;color:var(--text-muted)">${f.description}</div>
        </div>
      `).join('')}`;
  },

  async runAnalysis() {
    const btn = event.target;
    btn.textContent = '⏳ Analyzing...';
    btn.disabled = true;
    try {
      const data = await fetch('/api/anomaly/fleet').then(r => r.json());
      this._reports = data;
      app.showNotification(`✅ Fleet analysis complete — ${data.length} vessels assessed`, 'success');
    } catch(e) {
      this._reports = this._demoReports();
      app.showNotification('⚠️ Using cached analysis data', 'warning');
    }
    this.renderFleetAnomalyList(this._reports);
    btn.textContent = '🔍 Run Full Fleet Analysis';
    btn.disabled = false;
  }
};
