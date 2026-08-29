/**
 * MarineGuard AI - Interactive Maritime GIS Map Module
 * Robust Leaflet engine with dual tile layers and interactive vector overlays.
 */
const MapModule = {
  map: null,
  satelliteLayer: null,
  darkLayer: null,
  layers: {
    grid: null,
    coastline: null,
    ports: null,
    spills: null,
    tracks: null,
    weather: null,
    vessels: null
  },

  initMap() {
    const mapEl = document.getElementById('leaflet-map');
    if (!mapEl) {
      console.error('leaflet-map element not found');
      return;
    }

    if (typeof L === 'undefined') {
      console.error('Leaflet library is not loaded');
      mapEl.innerHTML = '<div style="color:#ff1744;padding:30px;text-align:center;">Leaflet library loading failed.</div>';
      return;
    }

    // Destroy existing instance if any
    if (this.map) {
      try { this.map.remove(); } catch(e) {}
      this.map = null;
    }

    try {
      // Initialize Map with custom coordinates centered on Bay of Bengal
      this.map = L.map('leaflet-map', {
        center: [12.15, 80.50],
        zoom: 8,
        minZoom: 5,
        maxZoom: 16,
        zoomControl: false,
        attributionControl: false
      });

      // Zoom control on top-right
      L.control.zoom({ position: 'topright' }).addTo(this.map);

      // Dark Basemap (CartoDB Dark Matter)
      this.darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 19,
        opacity: 0.95
      }).addTo(this.map);

      // High-Resolution Satellite Basemap (Esri World Imagery)
      this.satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
      });

      // Initialize layer groups
      this.layers.grid = L.layerGroup().addTo(this.map);
      this.layers.coastline = L.layerGroup().addTo(this.map);
      this.layers.ports = L.layerGroup().addTo(this.map);
      this.layers.spills = L.layerGroup().addTo(this.map);
      this.layers.tracks = L.layerGroup().addTo(this.map);
      this.layers.weather = L.layerGroup().addTo(this.map);
      this.layers.vessels = L.layerGroup().addTo(this.map);

      // Render spatial assets
      this.renderOceanGrid();
      this.renderCoastlineAndPorts();
      this.renderOilSpill();
      this.renderTracks();
      this.renderVessels();
      this.renderWeather();
      this.renderScaleBar();
      this.bindLayerControls();

      // Ensure proper layout computation
      setTimeout(() => {
        if (this.map) this.map.invalidateSize();
      }, 100);
      setTimeout(() => {
        if (this.map) this.map.invalidateSize();
      }, 400);

      console.log('✓ MarineGuard Live Map initialized successfully');
    } catch(err) {
      console.error('Error initializing map:', err);
    }
  },

  renderOceanGrid() {
    this.layers.grid.clearLayers();
    // Sub-surface bathymetry / ocean surveillance grid lines
    for (let lat = 10.5; lat <= 13.5; lat += 0.5) {
      L.polyline([[lat, 79.5], [lat, 82.0]], {
        color: 'rgba(0, 212, 255, 0.05)',
        weight: 1,
        interactive: false
      }).addTo(this.layers.grid);
    }
    for (let lon = 79.5; lon <= 82.0; lon += 0.5) {
      L.polyline([[10.5, lon], [13.5, lon]], {
        color: 'rgba(0, 212, 255, 0.05)',
        weight: 1,
        interactive: false
      }).addTo(this.layers.grid);
    }
  },

  bindLayerControls() {
    // 1. Basemap toggle buttons
    const btnLive = document.getElementById('btn-live-map');
    const btnSat = document.getElementById('btn-satellite');

    if (btnLive && btnSat) {
      btnLive.onclick = (e) => {
        e.preventDefault();
        btnLive.classList.add('active');
        btnSat.classList.remove('active');
        if (this.map.hasLayer(this.satelliteLayer)) this.map.removeLayer(this.satelliteLayer);
        if (!this.map.hasLayer(this.darkLayer)) this.map.addLayer(this.darkLayer);
      };

      btnSat.onclick = (e) => {
        e.preventDefault();
        btnSat.classList.add('active');
        btnLive.classList.remove('active');
        if (this.map.hasLayer(this.darkLayer)) this.map.removeLayer(this.darkLayer);
        if (!this.map.hasLayer(this.satelliteLayer)) this.map.addLayer(this.satelliteLayer);
      };
    }

    // 2. Interactive Layer Checkboxes
    const toggleConfig = [
      { id: 'layer-vessels', layer: this.layers.vessels },
      { id: 'layer-spills', layer: this.layers.spills },
      { id: 'layer-weather', layer: this.layers.weather },
      { id: 'layer-coastline', layer: this.layers.coastline },
      { id: 'layer-ports', layer: this.layers.ports }
    ];

    toggleConfig.forEach(cfg => {
      const cb = document.getElementById(cfg.id);
      if (cb) {
        cb.onchange = (e) => {
          if (e.target.checked) {
            if (!this.map.hasLayer(cfg.layer)) this.map.addLayer(cfg.layer);
          } else {
            if (this.map.hasLayer(cfg.layer)) this.map.removeLayer(cfg.layer);
          }
        };
      }
    });
  },

  renderCoastlineAndPorts() {
    this.layers.ports.clearLayers();
    this.layers.coastline.clearLayers();

    // Coastline boundary polyline (Tamil Nadu coastal line)
    const coastBoundary = [
      [13.50, 80.33], [13.30, 80.30], [13.08, 80.27], [12.80, 80.24],
      [12.50, 80.17], [12.20, 80.00], [11.94, 79.81], [11.75, 79.77],
      [11.45, 79.78], [11.15, 79.85], [10.80, 79.85]
    ];

    L.polyline(coastBoundary, {
      color: 'rgba(0, 212, 255, 0.45)',
      weight: 2,
      dashArray: '4, 4',
      interactive: false
    }).addTo(this.layers.coastline);

    // Port & Coastal Cities
    const ports = [
      { name: 'Chennai', lat: 13.0827, lon: 80.2707 },
      { name: 'Puducherry', lat: 11.9416, lon: 79.8083 }
    ];

    ports.forEach(p => {
      const portIcon = L.divIcon({
        className: 'port-label-marker',
        html: `
          <div style="display:flex;align-items:center;gap:6px;transform:translate(-5px,-8px);">
            <div style="width:7px;height:7px;border-radius:50%;background:#8eaac8;box-shadow:0 0 8px rgba(142,170,200,0.9);border:1px solid #ffffff;"></div>
            <span style="font-size:12px;font-weight:700;color:#e8f0fe;letter-spacing:0.3px;text-shadow:0 1px 4px #000;">${p.name}</span>
          </div>
        `,
        iconSize: [120, 20]
      });
      L.marker([p.lat, p.lon], { icon: portIcon, interactive: false }).addTo(this.layers.ports);
    });
  },

  renderOilSpill() {
    this.layers.spills.clearLayers();

    // Organic oil slick multi-polygon in the Bay of Bengal
    const spillPolygonCoords = [
      [12.22, 80.25], [12.28, 80.35], [12.30, 80.48], [12.28, 80.62],
      [12.20, 80.70], [12.10, 80.68], [12.02, 80.58], [11.95, 80.55],
      [11.88, 80.52], [11.82, 80.45], [11.80, 80.35], [11.85, 80.26],
      [11.95, 80.22], [12.06, 80.20], [12.15, 80.21]
    ];

    // Layer 1: Outer glowing dispersion boundary
    L.polygon(spillPolygonCoords, {
      color: 'rgba(255, 60, 40, 0.5)',
      weight: 10,
      fillColor: 'transparent',
      interactive: false
    }).addTo(this.layers.spills);

    // Layer 2: Main slick emulsion zone
    L.polygon(spillPolygonCoords, {
      color: 'rgba(255, 80, 50, 0.95)',
      weight: 2,
      fillColor: 'rgba(140, 20, 20, 0.75)',
      fillOpacity: 0.8
    }).addTo(this.layers.spills);

    // Layer 3: Heavy crude core
    const coreCoords = [
      [12.18, 80.32], [12.22, 80.42], [12.18, 80.56],
      [12.08, 80.54], [11.96, 80.46], [11.92, 80.36],
      [12.02, 80.28], [12.10, 80.26]
    ];
    L.polygon(coreCoords, {
      color: 'rgba(255, 30, 30, 1.0)',
      weight: 1.5,
      fillColor: 'rgba(70, 5, 5, 0.92)',
      fillOpacity: 0.92,
      interactive: false
    }).addTo(this.layers.spills);

    // Permanent Spill HUD Callout Badge matching screenshot
    const badgeIcon = L.divIcon({
      className: 'spill-badge-marker',
      html: `
        <div style="background:rgba(13,26,48,0.95);border:1px solid rgba(255,50,50,0.8);border-radius:6px;padding:8px 12px;box-shadow:0 6px 25px rgba(0,0,0,0.8);backdrop-filter:blur(6px);transform:translate(-50%,-100%);min-width:140px;cursor:pointer;">
          <div style="color:#ff3b30;font-size:11px;font-weight:800;letter-spacing:0.4px;text-transform:uppercase;margin-bottom:3px;">🚨 Oil Spill Detected</div>
          <div style="color:#e8f0fe;font-size:11px;font-family:'JetBrains Mono',monospace;line-height:1.4;">
            Area: <b style="color:#ffffff;">4.8 km²</b><br>
            Confidence: <b style="color:#00e676;">91%</b>
          </div>
        </div>
      `,
      iconSize: [160, 55],
      iconAnchor: [80, 0]
    });

    const marker = L.marker([12.32, 80.48], { icon: badgeIcon }).addTo(this.layers.spills);
    marker.on('click', () => {
      if (window.IncidentModule) IncidentModule.selectIncident('INC-2025-05-20-01');
    });
  },

  renderTracks() {
    this.layers.tracks.clearLayers();

    // Vessel A Trajectory (Red Dashed Line from NE down towards the spill)
    const trackA = [
      [12.85, 81.35], [12.75, 81.15], [12.60, 80.95],
      [12.45, 80.75], [12.30, 80.60], [12.15, 80.45],
      [12.00, 80.35], [11.85, 80.25]
    ];
    L.polyline(trackA, {
      color: '#ff3344',
      weight: 2.5,
      dashArray: '6, 6',
      opacity: 0.95
    }).addTo(this.layers.tracks);

    // Vessel B Trajectory (Green Dashed Line heading NW)
    const trackB = [
      [11.45, 81.65], [11.60, 81.45], [11.75, 81.25], [11.90, 81.05]
    ];
    L.polyline(trackB, {
      color: '#00e676',
      weight: 2,
      dashArray: '5, 5',
      opacity: 0.85
    }).addTo(this.layers.tracks);

    // Vessel C Trajectory (Amber Dashed Line heading North)
    const trackC = [
      [10.95, 80.45], [11.15, 80.42], [11.35, 80.38],
      [11.55, 80.30], [11.75, 80.25]
    ];
    L.polyline(trackC, {
      color: '#ffab00',
      weight: 2,
      dashArray: '5, 5',
      opacity: 0.85
    }).addTo(this.layers.tracks);

    // Vessel D Trajectory (White/Grey Dashed Line)
    const trackD = [
      [11.00, 79.95], [11.20, 80.05], [11.40, 80.12], [11.60, 80.18]
    ];
    L.polyline(trackD, {
      color: '#cbd5e1',
      weight: 2,
      dashArray: '4, 4',
      opacity: 0.75
    }).addTo(this.layers.tracks);
  },

  renderVessels() {
    this.layers.vessels.clearLayers();

    const vessels = [
      {
        name: 'Vessel A',
        subtext: 'MT SHIVALIK (MMSI: 419001234)',
        type: 'Oil Tanker',
        lat: 12.60,
        lon: 80.95,
        color: '#ff1744',
        heading: 230,
        score: '91%'
      },
      {
        name: 'Vessel B',
        subtext: 'MV CHENNAI EXPRESS (419002345)',
        type: 'Container Ship',
        lat: 11.90,
        lon: 81.05,
        color: '#00e676',
        heading: 310,
        score: '31%'
      },
      {
        name: 'Vessel C',
        subtext: 'MV KAVERI (419003456)',
        type: 'Bulk Carrier',
        lat: 11.35,
        lon: 80.38,
        color: '#ffab00',
        heading: 350,
        score: '12%'
      },
      {
        name: 'Vessel D',
        subtext: 'FV MUTHUMARI (419004567)',
        type: 'Fishing Vessel',
        lat: 11.40,
        lon: 80.12,
        color: '#f8fafc',
        heading: 45,
        score: '08%'
      }
    ];

    vessels.forEach(v => {
      const shipSvg = `
        <svg width="22" height="22" viewBox="0 0 24 24" style="transform:rotate(${v.heading}deg);filter:drop-shadow(0 0 6px ${v.color});">
          <path d="M12 2L18 20L12 16L6 20L12 2Z" fill="${v.color}" stroke="#ffffff" stroke-width="1.5"/>
        </svg>
      `;

      const vesselHtml = `
        <div style="display:flex;align-items:center;gap:6px;transform:translate(-11px,-11px);cursor:pointer;">
          ${shipSvg}
          <div style="background:rgba(10,22,40,0.92);border:1px solid ${v.color};border-radius:4px;padding:2px 6px;white-space:nowrap;backdrop-filter:blur(4px);box-shadow:0 2px 8px rgba(0,0,0,0.6);">
            <div style="color:#fff;font-size:11px;font-weight:700;line-height:1.2;">${v.name}</div>
          </div>
        </div>
      `;

      const icon = L.divIcon({
        className: 'vessel-marker-custom',
        html: vesselHtml,
        iconSize: [120, 24]
      });

      const marker = L.marker([v.lat, v.lon], { icon }).addTo(this.layers.vessels);
      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif;padding:6px;color:#0f172a;min-width:160px;">
          <b style="color:${v.color};font-size:13px;">🚢 ${v.name}</b><br>
          <span style="font-size:11px;color:#475569;">${v.subtext}</span><br>
          <span style="font-size:11px;">Class: <b>${v.type}</b></span><br>
          <span style="font-size:11px;">Heading: <b>${v.heading}°</b></span><br>
          <span style="font-size:11px;">Attribution Score: <b style="color:#0284c7;">${v.score}</b></span>
        </div>
      `);
    });
  },

  renderWeather() {
    this.layers.weather.clearLayers();

    // Wind direction cluster matching reference screenshot
    const windHtml = `
      <div style="text-align:center;color:#8eaac8;font-size:11px;font-family:'Inter',sans-serif;pointer-events:none;">
        <div style="display:flex;justify-content:center;gap:4px;margin-bottom:2px;opacity:0.75;">
          <span>↗</span><span>↗</span><span>↗</span>
        </div>
        <div style="display:flex;justify-content:center;gap:6px;opacity:0.85;">
          <span>↗</span><span>↗</span><span>↗</span><span>↗</span>
        </div>
        <div style="margin-top:4px;font-weight:600;color:#a5c2e0;letter-spacing:0.3px;text-shadow:0 1px 4px #000;">
          Wind Direction<br><span style="color:#00d4ff;font-family:monospace;font-size:11.5px;">SW 12 kn</span>
        </div>
      </div>
    `;

    const windIcon = L.divIcon({
      className: 'weather-wind-marker',
      html: windHtml,
      iconSize: [120, 60]
    });

    L.marker([11.70, 80.85], { icon: windIcon, interactive: false }).addTo(this.layers.weather);
  },

  renderScaleBar() {
    const scaleControl = L.control.scale({ position: 'bottomleft', imperial: false, maxWidth: 80 });
    scaleControl.addTo(this.map);
  },

  renderTrackLine(mmsi, latlngs) {
    this.layers.tracks.clearLayers();
    L.polyline(latlngs, {
      color: '#00d4ff',
      weight: 3,
      dashArray: '6, 6',
      opacity: 0.95
    }).addTo(this.layers.tracks);
  },

  focusIncident(incident) {
    if (this.map && incident.lat && incident.lon) {
      this.map.flyTo([incident.lat + 0.1, incident.lon + 0.1], 9, { duration: 1.2 });
    }
  }
};
