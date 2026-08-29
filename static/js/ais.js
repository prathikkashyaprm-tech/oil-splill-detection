const AISModule = {
  _pollingInterval: null,

  async init() {
    try {
      const data = await fetch('/api/ais/vessels').then(r => r.json());
      this.renderFleetTable(data);
    } catch (e) {
      // Use hardcoded demo data if API fails
      this.renderFleetTable(this._demoVessels());
    }
    this.startPositionPolling();
  },

  _demoVessels() {
    return [
      { mmsi: 419001234, name: 'MT SHIVALIK', type: 'Oil Tanker', flag: 'India', speed: 12.5, heading: 230, status: 'Underway', anomaly_score: 88 },
      { mmsi: 419002345, name: 'MV CHENNAI EXPRESS', type: 'Container Ship', flag: 'India', speed: 18.0, heading: 270, status: 'Underway', anomaly_score: 45 },
      { mmsi: 419003456, name: 'MV KAVERI', type: 'Bulk Carrier', flag: 'Singapore', speed: 14.0, heading: 0, status: 'Underway', anomaly_score: 22 },
      { mmsi: 419004567, name: 'FV MUTHUMARI', type: 'Fishing Vessel', flag: 'India', speed: 5.0, heading: 90, status: 'Fishing', anomaly_score: 31 },
      { mmsi: 419005678, name: 'ICGS SAURASHTRA', type: 'Coast Guard', flag: 'India', speed: 22.0, heading: 180, status: 'Patrol', anomaly_score: 5 },
      { mmsi: 419006789, name: 'MT DESH RAKSHAK', type: 'Oil Tanker', flag: 'India', speed: 11.2, heading: 45, status: 'Underway', anomaly_score: 18 },
      { mmsi: 419007890, name: 'MV VISHVA VIJAY', type: 'Cargo', flag: 'India', speed: 9.8, heading: 315, status: 'Underway', anomaly_score: 12 },
      { mmsi: 419008901, name: 'CMA CGM COLOMBO', type: 'Container Ship', flag: 'France', speed: 20.5, heading: 200, status: 'Underway', anomaly_score: 8 },
      { mmsi: 419009012, name: 'FV JALAPARI', type: 'Fishing Vessel', flag: 'India', speed: 3.2, heading: 60, status: 'Fishing', anomaly_score: 15 },
      { mmsi: 419010123, name: 'MV TIGER GULF', type: 'Bulk Carrier', flag: 'Panama', speed: 13.8, heading: 120, status: 'Underway', anomaly_score: 10 },
      { mmsi: 419011234, name: 'MT CORAL', type: 'Chemical Tanker', flag: 'Marshall Islands', speed: 10.0, heading: 240, status: 'Underway', anomaly_score: 7 },
      { mmsi: 419012345, name: 'MV ASIAN GLORY', type: 'Ro-Ro Cargo', flag: 'Liberia', speed: 15.5, heading: 80, status: 'Underway', anomaly_score: 9 },
    ];
  },

  formatAnomalyBadge(score) {
    if (score >= 70) return `<span class="badge high">HIGH (${score})</span>`;
    if (score >= 40) return `<span class="badge medium">MED (${score})</span>`;
    return `<span class="badge low">LOW (${score})</span>`;
  },

  renderFleetTable(vessels) {
    const tbody = document.getElementById('fleet-tbody');
    if (!tbody) return;
    tbody.innerHTML = vessels.map(v => `
      <tr style="cursor:pointer" onclick="AISModule.handleRowClick(${v.mmsi})">
        <td style="font-family:var(--font-mono);font-size:11px">${v.mmsi}</td>
        <td style="font-weight:600;color:var(--text-primary)">${v.name || v.vessel_name || '—'}</td>
        <td>${v.type || v.vessel_type || '—'}</td>
        <td><span style="font-size:11px">${v.flag || '—'}</span></td>
        <td style="font-family:var(--font-mono)">${(v.speed||0).toFixed(1)} kn</td>
        <td style="font-family:var(--font-mono)">${v.heading || 0}°</td>
        <td><span style="color:${v.status==='Underway'?'var(--accent-emerald)':v.status==='Fishing'?'var(--accent-amber)':'var(--text-muted)'};font-size:11px">${v.status||'—'}</span></td>
        <td>${this.formatAnomalyBadge(v.anomaly_score || 0)}</td>
        <td>
          <button class="btn btn-outline" style="padding:4px 10px;font-size:11px"
            onclick="event.stopPropagation();AISModule.handleRowClick(${v.mmsi})">View Track</button>
        </td>
      </tr>
    `).join('');
  },

  async handleRowClick(mmsi) {
    try {
      const data = await fetch(`/api/ais/track/${mmsi}`).then(r => r.json());
      if (data.positions && data.positions.length > 0 && window.MapModule) {
        const latlngs = data.positions.map(p => [p.lat, p.lon]);
        MapModule.renderTrackLine(mmsi, latlngs);
        MapModule.map.flyTo(latlngs[latlngs.length - 1], 10, { duration: 1.5 });
        app.switchTab('dashboard');
      }
    } catch(e) {
      console.log('Track preview for', mmsi);
    }
  },

  startPositionPolling() {
    if (this._pollingInterval) clearInterval(this._pollingInterval);
    this._pollingInterval = setInterval(async () => {
      try {
        const data = await fetch('/api/ais/vessels').then(r => r.json());
        this.renderFleetTable(data);
      } catch(e) {}
    }, 30000);
  },

  uploadPrompt() {
    const input = document.createElement('input');
    input.type = 'file'; input.accept = '.csv';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const text = await file.text();
      try {
        const result = await fetch('/api/ais/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ csv_content: text })
        }).then(r => r.json());
        app.showNotification(`✅ Ingested ${result.ingested_records} AIS records`, 'success');
        this.init();
      } catch(e) {
        app.showNotification('❌ Failed to ingest AIS feed', 'error');
      }
    };
    input.click();
  }
};
