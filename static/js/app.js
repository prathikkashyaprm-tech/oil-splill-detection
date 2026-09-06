/**
 * MARINEGUARD AI - Maritime Incident Intelligence System
 * High-Fidelity Prototype GIS Engine (Prominent Spill & Tactical Vessels)
 */

// Global State
let tacticalMap = null;
let extendedMap = null;
let currentMapMode = 'live';
let activeScenarioId = 'INC-01';
let isIncidentClosed = false;

// Charts
let timelineChart = null;
let anomalyDonutChart = null;
let riskDonutChart = null;
let weatheringAnalyticsChart = null;
let sstAnalyticsChart = null;

// Map Layers
const mapLayers = {
  vessels: null,
  oil_spills: null,
  weather: null,
  coastline: null,
  ports: null,
  baseTile: null
};

// 100% Free Open-Source Tile Endpoints (Zero API Key required)
const OPEN_TILE_URLS = {
  live: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
};

// ==========================================================================
// MULTI-LOCATION DISASTER SCENARIOS DATABASE
// ==========================================================================
const DISASTER_SCENARIOS = {
  'INC-01': {
    id: 'INC-01',
    code: '#INC-2025-05-20-01',
    title: 'Bay of Bengal (Chennai Corridor)',
    region: 'Bay of Bengal',
    coordsStr: '10.820° N, 79.130° E',
    mapCenter: [12.45, 80.60],
    zoom: 8,
    affectedArea: '4.8 km²',
    confidence: '91%',
    detectedTime: '20 May 2025, 14:32 UTC',
    status: 'Under Investigation',
    statusClass: 'text-amber',
    bannerBg: 'rgba(45, 12, 22, 0.7)',
    bannerBorder: 'rgba(255, 51, 102, 0.4)',
    landmarks: [
      { name: 'Chennai', lat: 13.0827, lng: 80.2707 },
      { name: 'Puducherry', lat: 11.9416, lng: 79.8083 }
    ],
    ports: [
      { name: 'Chennai Port', lat: 13.0844, lng: 80.2975 },
      { name: 'Puducherry Port', lat: 11.9333, lng: 79.8333 }
    ],
    wind: {
      coords: [[12.25, 81.05], [12.20, 81.12], [12.15, 81.18], [12.10, 81.24]],
      labelPos: [12.22, 81.15],
      label: 'SW 12 kn',
      deg: 45
    },
    spillPolygon: [
      [12.72, 80.45],
      [12.78, 80.60],
      [12.74, 80.78],
      [12.65, 80.92],
      [12.48, 80.98],
      [12.30, 80.90],
      [12.18, 80.72],
      [12.22, 80.55],
      [12.38, 80.40],
      [12.55, 80.48],
      [12.72, 80.45]
    ],
    spillCore: [
      [12.62, 80.55],
      [12.66, 80.70],
      [12.52, 80.82],
      [12.35, 80.75],
      [12.40, 80.58],
      [12.62, 80.55]
    ],
    calloutAnchor: [12.78, 80.60],
    vessels: [
      {
        id: 'vesselA',
        name: 'Vessel A',
        fullName: 'Vessel A (MT PACIFIC GLORY)',
        mmsi: '419001234',
        type: 'Oil Tanker',
        spd: '12.4 kn / 140°',
        dist: '1.8 km',
        time: '37 min',
        anomaly: '88%',
        attr: '91%',
        priorityBadge: 'badge-red',
        color: '#ff3366',
        pos: [12.92, 80.88],
        heading: 140,
        trail: [[13.08, 80.72], [12.92, 80.88], [12.75, 81.02], [12.50, 81.18]]
      },
      {
        id: 'vesselB',
        name: 'Vessel B',
        fullName: 'Vessel B (MV OCEAN LEADER)',
        mmsi: '419002345',
        type: 'Cargo',
        spd: '14.1 kn / 120°',
        dist: '6.2 km',
        time: '18 min',
        anomaly: '35%',
        attr: '31%',
        priorityBadge: 'badge-green',
        color: '#00e676',
        pos: [12.48, 81.25],
        heading: 120,
        trail: [[12.68, 81.05], [12.48, 81.25], [12.28, 81.45]]
      },
      {
        id: 'vesselC',
        name: 'Vessel C',
        fullName: 'Vessel C (SS BHARAT STAR)',
        mmsi: '419003456',
        type: 'Bulk Carrier',
        spd: '10.8 kn / 210°',
        dist: '9.5 km',
        time: '45 min',
        anomaly: '18%',
        attr: '12%',
        priorityBadge: 'badge-amber',
        color: '#ff9900',
        pos: [12.02, 80.78],
        heading: 210,
        trail: [[12.30, 80.65], [12.15, 80.72], [12.02, 80.78]]
      },
      {
        id: 'vesselD',
        name: 'Vessel D',
        fullName: 'Vessel D (MT ARABIAN TIDE)',
        mmsi: '419004567',
        type: 'Chemical Tanker',
        spd: '16.5 kn / 315°',
        dist: '14.1 km',
        time: '12 min',
        anomaly: '08%',
        attr: '08%',
        priorityBadge: 'badge-gray',
        color: '#ffffff',
        pos: [12.06, 80.35],
        heading: 315,
        trail: [[11.88, 80.20], [11.98, 80.28], [12.06, 80.35]]
      }
    ],
    timelinePoints: [12, 26, 32, 40, 48, 64, 91],
    sarHomo: '0.824',
    sarContrast: '0.142',
    sarBonn: 'Code 3 (Metallic Sheen)'
  },

  'INC-02': {
    id: 'INC-02',
    code: '#INC-2025-05-18-02',
    title: 'Gulf of Mannar (Rameswaram)',
    region: 'Gulf of Mannar Biosphere Reserve',
    coordsStr: '09.145° N, 79.210° E',
    mapCenter: [9.15, 79.20],
    zoom: 9,
    affectedArea: '3.2 km²',
    confidence: '88%',
    detectedTime: '18 May 2025, 08:15 UTC',
    status: 'Containment Deployed',
    statusClass: 'text-amber',
    bannerBg: 'rgba(45, 25, 10, 0.7)',
    bannerBorder: 'rgba(255, 153, 0, 0.4)',
    landmarks: [
      { name: 'Rameswaram', lat: 9.2876, lng: 79.3129 },
      { name: 'Tuticorin', lat: 8.7642, lng: 78.1348 }
    ],
    ports: [
      { name: 'V.O.C. Port', lat: 8.7523, lng: 78.1884 }
    ],
    wind: {
      coords: [[9.08, 79.35], [9.02, 79.40], [8.98, 79.45]],
      labelPos: [9.05, 79.40],
      label: 'SE 10 kn',
      deg: 135
    },
    spillPolygon: [
      [9.25, 79.10], [9.28, 79.22], [9.22, 79.34], [9.12, 79.35],
      [9.05, 79.28], [9.04, 79.15], [9.12, 79.08], [9.25, 79.10]
    ],
    spillCore: [
      [9.20, 79.15], [9.22, 79.24], [9.16, 79.26], [9.12, 79.18], [9.20, 79.15]
    ],
    calloutAnchor: [9.28, 79.22],
    vessels: [
      {
        id: 'vesselA',
        name: 'Vessel A',
        fullName: 'MV CORAL PRINCESS',
        mmsi: '419008912',
        type: 'Chemical Tanker',
        spd: '8.2 kn / 095°',
        dist: '2.1 km',
        time: '52 min',
        anomaly: '79%',
        attr: '88%',
        priorityBadge: 'badge-red',
        color: '#ff3366',
        pos: [9.32, 79.38],
        heading: 95,
        trail: [[9.10, 79.12], [9.20, 79.24], [9.32, 79.38]]
      },
      {
        id: 'vesselB',
        name: 'Vessel B',
        fullName: 'SS PEARL DIVER',
        mmsi: '419007654',
        type: 'General Cargo',
        spd: '11.5 kn / 180°',
        dist: '5.8 km',
        time: '24 min',
        anomaly: '28%',
        attr: '24%',
        priorityBadge: 'badge-green',
        color: '#00e676',
        pos: [8.98, 79.22],
        heading: 180,
        trail: [[9.25, 79.22], [9.12, 79.22], [8.98, 79.22]]
      },
      {
        id: 'vesselC',
        name: 'Vessel C',
        fullName: 'MV LANKAN STAR',
        mmsi: '419003321',
        type: 'Container Carrier',
        spd: '15.0 kn / 220°',
        dist: '8.4 km',
        time: '15 min',
        anomaly: '12%',
        attr: '15%',
        priorityBadge: 'badge-amber',
        color: '#ff9900',
        pos: [9.02, 79.05],
        heading: 220,
        trail: [[9.20, 79.15], [9.02, 79.05]]
      },
      {
        id: 'vesselD',
        name: 'Vessel D',
        fullName: 'FV DHANUSH PATROL',
        mmsi: '419009988',
        type: 'Trawler',
        spd: '6.0 kn / 045°',
        dist: '12.0 km',
        time: '60 min',
        anomaly: '05%',
        attr: '06%',
        priorityBadge: 'badge-gray',
        color: '#ffffff',
        pos: [9.38, 79.10],
        heading: 45,
        trail: [[9.28, 79.02], [9.38, 79.10]]
      }
    ],
    timelinePoints: [10, 15, 28, 42, 60, 78, 88],
    sarHomo: '0.795',
    sarContrast: '0.168',
    sarBonn: 'Code 2 (Rainbow Sheen)'
  },

  'INC-03': {
    id: 'INC-03',
    code: '#INC-2025-05-15-03',
    title: 'Mumbai High (Arabian Sea)',
    region: 'Arabian Sea (West Coast Basin)',
    coordsStr: '19.420° N, 71.350° E',
    mapCenter: [19.42, 71.35],
    zoom: 8,
    affectedArea: '6.4 km²',
    confidence: '94%',
    detectedTime: '15 May 2025, 21:10 UTC',
    status: 'Critical Alert',
    statusClass: 'text-red',
    bannerBg: 'rgba(50, 10, 20, 0.8)',
    bannerBorder: 'rgba(255, 51, 102, 0.6)',
    landmarks: [
      { name: 'Mumbai Coast', lat: 18.9220, lng: 72.8347 },
      { name: 'Alibaug', lat: 18.6414, lng: 72.8722 }
    ],
    ports: [
      { name: 'Mumbai Port (MBPT)', lat: 18.9400, lng: 72.8500 }
    ],
    wind: {
      coords: [[19.35, 71.55], [19.28, 71.60], [19.22, 71.65]],
      labelPos: [19.30, 71.60],
      label: 'NW 16 kn',
      deg: 315
    },
    spillPolygon: [
      [19.58, 71.18], [19.64, 71.35], [19.55, 71.55], [19.38, 71.58],
      [19.28, 71.42], [19.30, 71.22], [19.42, 71.12], [19.58, 71.18]
    ],
    spillCore: [
      [19.50, 71.28], [19.54, 71.40], [19.44, 71.45], [19.36, 71.32], [19.50, 71.28]
    ],
    calloutAnchor: [19.64, 71.35],
    vessels: [
      {
        id: 'vesselA',
        name: 'Vessel A',
        fullName: 'MT ARABIAN EXPLORER',
        mmsi: '419009876',
        type: 'Crude Oil Carrier',
        spd: '11.0 kn / 160°',
        dist: '1.2 km',
        time: '75 min',
        anomaly: '92%',
        attr: '94%',
        priorityBadge: 'badge-red',
        color: '#ff3366',
        pos: [19.72, 71.45],
        heading: 160,
        trail: [[19.20, 71.25], [19.45, 71.35], [19.72, 71.45]]
      },
      {
        id: 'vesselB',
        name: 'Vessel B',
        fullName: 'MV KONKAN TIDE',
        mmsi: '419005544',
        type: 'Offshore Supply Vessel',
        spd: '10.2 kn / 080°',
        dist: '4.5 km',
        time: '30 min',
        anomaly: '32%',
        attr: '28%',
        priorityBadge: 'badge-green',
        color: '#00e676',
        pos: [19.40, 71.65],
        heading: 80,
        trail: [[19.35, 71.30], [19.40, 71.65]]
      },
      {
        id: 'vesselC',
        name: 'Vessel C',
        fullName: 'SS SAGAR RATNA',
        mmsi: '419002211',
        type: 'Drillship Tender',
        spd: '4.5 kn / 000°',
        dist: '7.8 km',
        time: '90 min',
        anomaly: '16%',
        attr: '19%',
        priorityBadge: 'badge-amber',
        color: '#ff9900',
        pos: [19.22, 71.35],
        heading: 0,
        trail: [[19.10, 71.35], [19.22, 71.35]]
      },
      {
        id: 'vesselD',
        name: 'Vessel D',
        fullName: 'MV MARATHA PRIDE',
        mmsi: '419001199',
        type: 'Bulk Carrier',
        spd: '16.2 kn / 330°',
        dist: '15.0 km',
        time: '10 min',
        anomaly: '07%',
        attr: '09%',
        priorityBadge: 'badge-gray',
        color: '#ffffff',
        pos: [19.15, 71.10],
        heading: 330,
        trail: [[19.00, 71.00], [19.15, 71.10]]
      }
    ],
    timelinePoints: [20, 35, 48, 62, 75, 88, 94],
    sarHomo: '0.860',
    sarContrast: '0.115',
    sarBonn: 'Code 4 (Discontinuous True Oil Color)'
  },

  'INC-04': {
    id: 'INC-04',
    code: '#INC-2025-05-12-04',
    title: 'Palk Strait (Point Calimere)',
    region: 'Palk Strait (Point Calimere)',
    coordsStr: '10.150° N, 79.850° E',
    mapCenter: [10.15, 79.85],
    zoom: 9,
    affectedArea: '1.4 km²',
    confidence: '82%',
    detectedTime: '12 May 2025, 04:20 UTC',
    status: 'Closed / Sanctioned',
    statusClass: 'text-green',
    bannerBg: 'rgba(10, 45, 25, 0.7)',
    bannerBorder: 'rgba(0, 230, 118, 0.4)',
    landmarks: [
      { name: 'Point Calimere', lat: 10.2986, lng: 79.8661 },
      { name: 'Nagapattinam', lat: 10.7672, lng: 79.8449 }
    ],
    ports: [
      { name: 'Karaikal Port', lat: 10.8350, lng: 79.8450 }
    ],
    wind: {
      coords: [[10.10, 79.95], [10.05, 80.00]],
      labelPos: [10.08, 79.98],
      label: 'NE 09 kn',
      deg: 225
    },
    spillPolygon: [
      [10.24, 79.78], [10.28, 79.88], [10.20, 79.96], [10.08, 79.92],
      [10.06, 79.80], [10.14, 79.72], [10.24, 79.78]
    ],
    spillCore: [
      [10.18, 79.82], [10.22, 79.88], [10.14, 79.90], [10.12, 79.83], [10.18, 79.82]
    ],
    calloutAnchor: [10.28, 79.88],
    vessels: [
      {
        id: 'vesselA',
        name: 'Vessel A',
        fullName: 'SS SOUTHERN PEARL',
        mmsi: '419005432',
        type: 'Product Tanker',
        spd: '9.0 kn / 210°',
        dist: '1.5 km',
        time: '40 min',
        anomaly: '76%',
        attr: '82%',
        priorityBadge: 'badge-red',
        color: '#ff3366',
        pos: [10.30, 79.92],
        heading: 210,
        trail: [[10.10, 79.75], [10.20, 79.85], [10.30, 79.92]]
      },
      {
        id: 'vesselB',
        name: 'Vessel B',
        fullName: 'MV DELTA STREAM',
        mmsi: '419004411',
        type: 'Coastal Feeder',
        spd: '12.0 kn / 040°',
        dist: '6.0 km',
        time: '20 min',
        anomaly: '22%',
        attr: '22%',
        priorityBadge: 'badge-green',
        color: '#00e676',
        pos: [10.02, 79.75],
        heading: 40,
        trail: [[9.90, 79.65], [10.02, 79.75]]
      },
      {
        id: 'vesselC',
        name: 'Vessel C',
        fullName: 'FV CAUVERY HARVEST',
        mmsi: '419006677',
        type: 'Fishing Trawler',
        spd: '5.5 kn / 150°',
        dist: '8.2 km',
        time: '50 min',
        anomaly: '10%',
        attr: '11%',
        priorityBadge: 'badge-amber',
        color: '#ff9900',
        pos: [10.35, 79.85],
        heading: 150,
        trail: [[10.40, 79.80], [10.35, 79.85]]
      },
      {
        id: 'vesselD',
        name: 'Vessel D',
        fullName: 'SS CHOLA CARRIER',
        mmsi: '419008822',
        type: 'Container',
        spd: '17.0 kn / 020°',
        dist: '14.5 km',
        time: '08 min',
        anomaly: '04%',
        attr: '05%',
        priorityBadge: 'badge-gray',
        color: '#ffffff',
        pos: [10.00, 80.05],
        heading: 20,
        trail: [[9.85, 80.00], [10.00, 80.05]]
      }
    ],
    timelinePoints: [15, 22, 38, 55, 68, 76, 82],
    sarHomo: '0.760',
    sarContrast: '0.190',
    sarBonn: 'Code 1 (Sheen / Silvery)'
  },

  'INC-05': {
    id: 'INC-05',
    code: '#INC-2025-05-08-05',
    title: 'Andaman Sea (Port Blair)',
    region: 'Andaman Sea (Port Blair Basin)',
    coordsStr: '11.650° N, 92.750° E',
    mapCenter: [11.65, 92.75],
    zoom: 8.5,
    affectedArea: '5.1 km²',
    confidence: '96%',
    detectedTime: '08 May 2025, 17:45 UTC',
    status: 'Under Investigation',
    statusClass: 'text-amber',
    bannerBg: 'rgba(45, 12, 22, 0.7)',
    bannerBorder: 'rgba(255, 51, 102, 0.4)',
    landmarks: [
      { name: 'Port Blair', lat: 11.6234, lng: 92.7265 },
      { name: 'Havelock Island', lat: 11.9761, lng: 92.9876 }
    ],
    ports: [
      { name: 'Haddo Wharf', lat: 11.6700, lng: 92.7200 }
    ],
    wind: {
      coords: [[11.58, 92.88], [11.52, 92.92], [11.48, 92.98]],
      labelPos: [11.55, 92.90],
      label: 'SW 18 kn',
      deg: 45
    },
    spillPolygon: [
      [11.82, 92.65], [11.86, 92.78], [11.78, 92.92], [11.62, 92.92],
      [11.50, 92.82], [11.52, 92.68], [11.65, 92.58], [11.82, 92.65]
    ],
    spillCore: [
      [11.75, 92.72], [11.78, 92.82], [11.68, 92.85], [11.60, 92.75], [11.75, 92.72]
    ],
    calloutAnchor: [11.86, 92.78],
    vessels: [
      {
        id: 'vesselA',
        name: 'Vessel A',
        fullName: 'MT GLOBAL VOYAGER',
        mmsi: '419006789',
        type: 'VLCC Supertanker',
        spd: '13.5 kn / 110°',
        dist: '1.4 km',
        time: '65 min',
        anomaly: '95%',
        attr: '96%',
        priorityBadge: 'badge-red',
        color: '#ff3366',
        pos: [11.90, 92.88],
        heading: 110,
        trail: [[11.45, 92.60], [11.70, 92.75], [11.90, 92.88]]
      },
      {
        id: 'vesselB',
        name: 'Vessel B',
        fullName: 'MV ISLAND QUEEN',
        mmsi: '419003344',
        type: 'Passenger Ferry',
        spd: '16.0 kn / 010°',
        dist: '5.2 km',
        time: '18 min',
        anomaly: '20%',
        attr: '18%',
        priorityBadge: 'badge-green',
        color: '#00e676',
        pos: [11.55, 92.70],
        heading: 10,
        trail: [[11.40, 92.68], [11.55, 92.70]]
      },
      {
        id: 'vesselC',
        name: 'Vessel C',
        fullName: 'SS ANDAMAN PRIDE',
        mmsi: '419001188',
        type: 'Timber Carrier',
        spd: '10.0 kn / 240°',
        dist: '8.8 km',
        time: '35 min',
        anomaly: '15%',
        attr: '14%',
        priorityBadge: 'badge-amber',
        color: '#ff9900',
        pos: [11.60, 92.98],
        heading: 240,
        trail: [[11.75, 93.05], [11.60, 92.98]]
      },
      {
        id: 'vesselD',
        name: 'Vessel D',
        fullName: 'MT MONSOON BREEZE',
        mmsi: '419009911',
        type: 'Bunker Barge',
        spd: '7.5 kn / 180°',
        dist: '13.0 km',
        time: '45 min',
        anomaly: '06%',
        attr: '07%',
        priorityBadge: 'badge-gray',
        color: '#ffffff',
        pos: [11.42, 92.82],
        heading: 180,
        trail: [[11.58, 92.82], [11.42, 92.82]]
      }
    ],
    timelinePoints: [25, 40, 58, 72, 85, 92, 96],
    sarHomo: '0.880',
    sarContrast: '0.098',
    sarBonn: 'Code 5 (Continuous True Oil Color)'
  }
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initLiveClock();
  initTacticalMap();
  initTimelineChart();
  initDonutCharts();
  loadIncidentScenario('INC-01', false);
  populateIncidentRegistry();
  populateAlertFeed();
  initReportLivePreview();

  // Close dropdowns on outer click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.notification-wrapper')) {
      document.getElementById('notifDropdown')?.classList.remove('show');
    }
    if (!e.target.closest('.profile-wrapper')) {
      document.getElementById('profileDropdown')?.classList.remove('show');
    }
  });
});

/* ==========================================================================
   1. LIVE UTC CLOCK
   ========================================================================== */
function initLiveClock() {
  const clockEl = document.getElementById('headerUtcClock');
  if (!clockEl) return;

  function updateClock() {
    const now = new Date();
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const day = String(now.getUTCDate()).padStart(2, '0');
    const month = months[now.getUTCMonth()];
    const year = now.getUTCFullYear();
    const hours = String(now.getUTCHours()).padStart(2, '0');
    const mins = String(now.getUTCMinutes()).padStart(2, '0');
    const secs = String(now.getUTCSeconds()).padStart(2, '0');
    
    clockEl.innerText = `${day} ${month} ${year}, ${hours}:${mins}:${secs} UTC`;
  }

  updateClock();
  setInterval(updateClock, 1000);
}

/* ==========================================================================
   2. SCENARIO / DISASTER LOCATION SWITCHER
   ========================================================================== */
function loadIncidentScenario(scenarioId, shouldFly = true) {
  const scenario = DISASTER_SCENARIOS[scenarioId];
  if (!scenario) return;

  activeScenarioId = scenarioId;

  // Sync disaster selector dropdown
  const selector = document.getElementById('disasterSelector');
  if (selector && selector.value !== scenarioId) {
    selector.value = scenarioId;
  }

  // 1. Move Tactical Map
  if (tacticalMap) {
    if (shouldFly) {
      tacticalMap.flyTo(scenario.mapCenter, scenario.zoom, { duration: 1.2 });
    } else {
      tacticalMap.setView(scenario.mapCenter, scenario.zoom);
    }

    // Clear and redraw all location-specific map layers
    clearMapLayers();
    renderCoastlineLabels(scenario.landmarks);
    renderPorts(scenario.ports);
    renderOilSpill(scenario);
    renderVesselsAndTrails(scenario.vessels);
    renderWindVectors(scenario.wind);

    setTimeout(() => {
      tacticalMap.invalidateSize();
    }, 100);
  }

  // 2. Update Right Incident Details Panel
  document.getElementById('incHeaderId').innerText = scenario.code;
  document.getElementById('incHeadline').innerText = `CONFIRMED OIL SPILL (${scenario.title.split('(')[0].trim().toUpperCase()})`;
  document.getElementById('incTime').innerText = `Detected: ${scenario.detectedTime}`;
  document.getElementById('incStatusText').innerText = scenario.status;
  document.getElementById('incStatusText').className = scenario.statusClass;
  document.getElementById('incAlertBanner').style.background = scenario.bannerBg;
  document.getElementById('incAlertBanner').style.borderColor = scenario.bannerBorder;

  document.getElementById('incCoords').innerText = scenario.coordsStr;
  document.getElementById('incRegionName').innerText = scenario.region;
  document.getElementById('incArea').innerText = scenario.affectedArea;
  document.getElementById('incConfidence').innerText = scenario.confidence;

  // Update Most Probable Source Card
  const topVessel = scenario.vessels[0];
  document.getElementById('primarySourceCard').innerHTML = `
    <div class="source-card-main">
      <div class="ship-icon-badge" style="color: ${topVessel.color}; border-color: ${topVessel.color};">
        <i class="fa-solid fa-ship"></i>
      </div>
      <div class="source-info">
        <div class="vessel-title">${topVessel.name}</div>
        <div class="vessel-spec">MMSI: <span class="font-mono">${topVessel.mmsi}</span></div>
        <div class="vessel-spec">Vessel Type: <span class="text-white">${topVessel.type}</span></div>
        <div class="vessel-spec">Distance from Spill: <span class="text-white">${topVessel.dist}</span></div>
        <div class="vessel-spec">Time in Area: <span class="text-white">${topVessel.time}</span></div>
        <div class="vessel-spec">Behavior Anomaly Score: <span class="text-white">${topVessel.anomaly}</span></div>
      </div>
      <div class="attribution-score-wrap">
        <div class="attr-label">Attribution Score</div>
        <div class="attr-score" style="color: ${topVessel.color};">${topVessel.attr}</div>
      </div>
    </div>
  `;

  // Update Other Nearby Vessels
  const otherVessels = scenario.vessels.slice(1);
  document.getElementById('otherNearbyVesselsList').innerHTML = otherVessels.map(v => `
    <div class="nearby-vessel-row interactive" onclick="selectVesselById('${v.id}')">
      <div class="nv-left">
        <i class="fa-solid fa-ship" style="color:${v.color};"></i>
        <div>
          <div class="nv-name">${v.name}</div>
          <div class="nv-mmsi">MMSI: ${v.mmsi}</div>
        </div>
      </div>
      <div class="nv-score">Score: <strong style="color:${v.color};">${v.attr}</strong></div>
    </div>
  `).join('');

  // Update Subviews
  document.getElementById('subviewVesselsCardList').innerHTML = scenario.vessels.map((v, i) => `
    <div class="subview-vessel-card ${i === 0 ? 'active-card' : ''}" onclick="selectVesselById('${v.id}')">
      <div class="svc-top">
        <strong>${v.fullName}</strong>
        <span class="${v.priorityBadge} font-mono">${v.attr} PRIORITY</span>
      </div>
      <div class="svc-meta">MMSI: ${v.mmsi} | ${v.type} | Speed: ${v.spd}</div>
      <p>Telemetry anomaly score ${v.anomaly}. Distance to slick center: ${v.dist}.</p>
    </div>
  `).join('');

  document.getElementById('sarHomoVal').innerText = scenario.sarHomo;
  document.getElementById('sarContrastVal').innerText = scenario.sarContrast;
  document.getElementById('sarBonnVal').innerText = scenario.sarBonn;

  document.getElementById('incTemporalLogList').innerHTML = `
    <div class="tl-item">
      <span class="tl-time">02h Prior</span>
      <div class="tl-desc">AIS Kinematic deviation flagged on ${topVessel.fullName} (Speed dropped abruptly).</div>
    </div>
    <div class="tl-item">
      <span class="tl-time">01h Prior</span>
      <div class="tl-desc">Automated Copernicus SAR satellite pass tasking triggered over ${scenario.region}.</div>
    </div>
    <div class="tl-item">
      <span class="tl-time">Detection Pass</span>
      <div class="tl-desc">Deep U-Net segmentation identified ${scenario.affectedArea} slick with ${scenario.confidence} confidence.</div>
    </div>
    <div class="tl-item">
      <span class="tl-time">Current</span>
      <div class="tl-desc">Active Incident ${scenario.code} declared in ${scenario.region}.</div>
    </div>
  `;

  // 3. Update Timeline Chart
  document.getElementById('timelineLocationTitle').innerText = `Oil Spill Detection Timeline (${scenario.title.split('(')[0].trim()})`;
  if (timelineChart) {
    timelineChart.data.datasets[0].data = scenario.timelinePoints;
    timelineChart.update();
  }

  // Update table in Vessels Tab
  populateVesselsTable(scenario.vessels);

  showToast(`Switched Disaster Zone: ${scenario.title}`);
}

function cycleIncident(delta) {
  const keys = Object.keys(DISASTER_SCENARIOS);
  let currentIndex = keys.indexOf(activeScenarioId);
  currentIndex = (currentIndex + delta + keys.length) % keys.length;
  loadIncidentScenario(keys[currentIndex], true);
}

/* ==========================================================================
   3. NAVIGATION TAB SWITCHER
   ========================================================================== */
function switchNavTab(tabId) {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    if (link.getAttribute('data-tab') === tabId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));
  const targetView = document.getElementById(`view-${tabId}`);
  if (targetView) {
    targetView.classList.add('active');
  } else {
    document.getElementById('view-dashboard').classList.add('active');
  }

  setTimeout(() => {
    if (tabId === 'dashboard' && tacticalMap) {
      tacticalMap.invalidateSize();
    } else if (tabId === 'map') {
      if (!extendedMap) {
        initExtendedMap();
      } else {
        extendedMap.invalidateSize();
        const sc = DISASTER_SCENARIOS[activeScenarioId];
        if (sc) extendedMap.setView(sc.mapCenter, sc.zoom);
      }
    } else if (tabId === 'analytics') {
      initAnalyticsCharts();
    }
  }, 120);
}

/* ==========================================================================
   4. GEOSPATIAL TACTICAL MAP (PROMINENT OIL SLICK & VESSELS)
   ========================================================================== */
function initTacticalMap() {
  const sc = DISASTER_SCENARIOS['INC-01'];
  tacticalMap = L.map('tacticalMap', {
    zoomControl: false,
    attributionControl: false
  }).setView(sc.mapCenter, sc.zoom);

  mapLayers.baseTile = L.tileLayer(OPEN_TILE_URLS.live, {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(tacticalMap);

  mapLayers.oil_spills = L.layerGroup().addTo(tacticalMap);
  mapLayers.vessels = L.layerGroup().addTo(tacticalMap);
  mapLayers.coastline = L.layerGroup().addTo(tacticalMap);
  mapLayers.weather = L.layerGroup().addTo(tacticalMap);
  mapLayers.ports = L.layerGroup().addTo(tacticalMap);

  // Sync layers with initial checkbox states
  ['vessels', 'oil_spills', 'weather', 'coastline', 'ports'].forEach(name => {
    const chk = document.getElementById(`layer${name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('')}`);
    if (chk && !chk.checked && mapLayers[name]) {
      tacticalMap.removeLayer(mapLayers[name]);
    }
  });

  setTimeout(() => {
    if (tacticalMap) tacticalMap.invalidateSize();
  }, 100);
}

function clearMapLayers() {
  if (mapLayers.oil_spills) mapLayers.oil_spills.clearLayers();
  if (mapLayers.vessels) mapLayers.vessels.clearLayers();
  if (mapLayers.coastline) mapLayers.coastline.clearLayers();
  if (mapLayers.weather) mapLayers.weather.clearLayers();
  if (mapLayers.ports) mapLayers.ports.clearLayers();
}

function renderCoastlineLabels(landmarks) {
  if (!landmarks) return;
  landmarks.forEach(pt => {
    const icon = L.divIcon({
      className: 'coast-label-marker-wrap',
      html: `<div class="coast-label-marker"><span class="coast-dot"></span><span>${pt.name}</span></div>`,
      iconSize: [110, 20],
      iconAnchor: [5, 10]
    });
    L.marker([pt.lat, pt.lng], { icon }).addTo(mapLayers.coastline);
  });
}

function renderPorts(ports) {
  if (!ports) return;
  ports.forEach(p => {
    const portIcon = L.divIcon({
      className: 'port-marker-wrap',
      html: `<div style="color:#00d2ff; font-size:10px; font-weight:600; text-shadow:0 0 5px #000; white-space:nowrap;"><i class="fa-solid fa-anchor"></i> ${p.name}</div>`,
      iconSize: [130, 20],
      iconAnchor: [10, 10]
    });
    L.marker([p.lat, p.lng], { icon: portIcon }).addTo(mapLayers.ports);
  });
}

function renderOilSpill(scenario) {
  if (!scenario.spillPolygon) return;

  // 1. Outer Slick Polygon (Dark maroon slick with glowing red dashed perimeter)
  L.polygon(scenario.spillPolygon, {
    className: 'spill-slick-glowing',
    color: '#ff3366',
    weight: 2.8,
    opacity: 0.95,
    fillColor: '#5c0a1e',
    fillOpacity: 0.65,
    dashArray: '5, 5'
  }).addTo(mapLayers.oil_spills);

  // 2. Dense Inner Core (Black/Dark Maroon Emulsification)
  if (scenario.spillCore) {
    L.polygon(scenario.spillCore, {
      className: 'spill-core-dense',
      color: '#ff1744',
      weight: 1.8,
      opacity: 0.9,
      fillColor: '#1a0006',
      fillOpacity: 0.88
    }).addTo(mapLayers.oil_spills);
  }

  // 3. Spill Centroid Pulsing Sonar Ring
  L.circle(scenario.mapCenter, {
    radius: 1000,
    color: '#ff3366',
    fillColor: '#ff3366',
    fillOpacity: 0.25,
    weight: 1.2,
    dashArray: '4, 4'
  }).addTo(mapLayers.oil_spills);

  // 4. Prominent Info Callout Overlay Badge exactly as shown in prototype
  const calloutIcon = L.divIcon({
    className: 'spill-callout-marker-wrapper',
    html: `
      <div class="spill-callout-overlay">
        <div class="spill-callout-title">Oil Spill Detected</div>
        <div>Area: <strong>${scenario.affectedArea}</strong></div>
        <div>Confidence: <strong style="color:#00e676;">${scenario.confidence}</strong></div>
      </div>
    `,
    iconSize: [135, 58],
    iconAnchor: [67, 65]
  });

  L.marker(scenario.calloutAnchor, { icon: calloutIcon }).addTo(mapLayers.oil_spills);
}

function renderVesselsAndTrails(vessels) {
  if (!vessels) return;
  vessels.forEach(v => {
    // 1. High Visibility Dashed Polyline Trajectory
    if (v.trail && v.trail.length > 0) {
      L.polyline(v.trail, {
        color: v.color,
        weight: 2.4,
        dashArray: '6, 6',
        opacity: 0.95
      }).addTo(mapLayers.vessels);
    }

    // 2. High-Visibility Tactical Vessel Marker Node
    const vesselIcon = L.divIcon({
      className: 'tactical-vessel-marker-wrapper',
      html: `
        <div class="tactical-vessel-node" style="--v-color: ${v.color};">
          <div class="vessel-label-badge">${v.name}</div>
          <div class="vessel-radar-pulse"></div>
          <div class="vessel-icon-body" style="transform: rotate(${v.heading}deg);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2 C15 6 16.5 12 16.5 18 L14 21.5 L10 21.5 L7.5 18 C7.5 12 9 6 12 2 Z" fill="${v.color}" stroke="#ffffff" stroke-width="0.8" style="filter: drop-shadow(0 0 6px ${v.color});"/>
              <circle cx="12" cy="13" r="2.2" fill="#000000" opacity="0.6"/>
            </svg>
          </div>
        </div>
      `,
      iconSize: [60, 48],
      iconAnchor: [30, 24]
    });

    const marker = L.marker(v.pos, { icon: vesselIcon }).addTo(mapLayers.vessels);
    marker.on('click', () => selectVesselById(v.id));
  });
}

function renderWindVectors(wind) {
  if (!wind || !wind.coords) return;
  wind.coords.forEach(pos => {
    const arrowIcon = L.divIcon({
      className: 'wind-arrow-wrap',
      html: `<i class="fa-solid fa-arrow-up" style="transform: rotate(${wind.deg}deg); color: #5a7394; font-size: 13px; opacity: 0.9;"></i>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });
    L.marker(pos, { icon: arrowIcon }).addTo(mapLayers.weather);
  });

  const windLabelIcon = L.divIcon({
    className: 'wind-vector-label-wrap',
    html: `<div class="wind-vector-label"><span>Wind Direction<br><strong>${wind.label}</strong></span></div>`,
    iconSize: [90, 30],
    iconAnchor: [45, 15]
  });
  L.marker(wind.labelPos, { icon: windLabelIcon }).addTo(mapLayers.weather);
}

function switchMapMode(mode) {
  currentMapMode = mode;
  document.getElementById('btnLiveMap').classList.toggle('active', mode === 'live');
  document.getElementById('btnSatView').classList.toggle('active', mode === 'satellite');

  if (mode === 'satellite') {
    document.body.classList.add('satellite-mode');
  } else {
    document.body.classList.remove('satellite-mode');
  }

  if (mapLayers.baseTile) {
    tacticalMap.removeLayer(mapLayers.baseTile);
  }
  mapLayers.baseTile = L.tileLayer(OPEN_TILE_URLS[mode], {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap / ESRI Open GIS'
  }).addTo(tacticalMap);

  showToast(`Switched to ${mode.toUpperCase()} Map View`);
}

function toggleMapLayer(layerName) {
  const chk = document.getElementById(`layer${layerName.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('')}`);
  if (!chk || !mapLayers[layerName]) return;

  if (chk.checked) {
    tacticalMap.addLayer(mapLayers[layerName]);
    showToast(`Layer [${layerName.replace('_', ' ').toUpperCase()}] enabled`);
  } else {
    tacticalMap.removeLayer(mapLayers[layerName]);
    showToast(`Layer [${layerName.replace('_', ' ').toUpperCase()}] disabled`);
  }
}

function zoomInMap() { if (tacticalMap) tacticalMap.zoomIn(); }
function zoomOutMap() { if (tacticalMap) tacticalMap.zoomOut(); }
function recenterMap() {
  const sc = DISASTER_SCENARIOS[activeScenarioId];
  if (tacticalMap && sc) {
    tacticalMap.flyTo(sc.mapCenter, sc.zoom, { duration: 1.0 });
    showToast(`Recentered on ${sc.title}`);
  }
}
function recenterTacticalToActive() { recenterMap(); }

function toggleLayerStack() {
  const chks = ['layerVessels', 'layerOilSpills', 'layerWeather', 'layerCoastline', 'layerPorts'];
  const allActive = chks.every(id => document.getElementById(id)?.checked);
  chks.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.checked = !allActive;
  });
  ['vessels', 'oil_spills', 'weather', 'coastline', 'ports'].forEach(toggleMapLayer);
}

/* ==========================================================================
   5. EXTENDED GIS MAP (TAB 2)
   ========================================================================== */
function initExtendedMap() {
  const sc = DISASTER_SCENARIOS[activeScenarioId] || DISASTER_SCENARIOS['INC-01'];
  extendedMap = L.map('extendedFullMap', {
    zoomControl: true,
    attributionControl: false
  }).setView(sc.mapCenter, sc.zoom);

  L.tileLayer(OPEN_TILE_URLS.live, {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap'
  }).addTo(extendedMap);
}

function simulateNewSpillDetection() {
  showToast("Scanning Copernicus SAR constellation... Ingesting new swath scene");
  const sc = DISASTER_SCENARIOS[activeScenarioId];
  if (tacticalMap && sc) {
    const offsetLat = sc.mapCenter[0] + 0.35;
    const offsetLng = sc.mapCenter[1] + 0.35;
    const newSlick = L.circle([offsetLat, offsetLng], {
      radius: 3000,
      color: '#ff9900',
      fillColor: '#ff9900',
      fillOpacity: 0.45
    }).addTo(mapLayers.oil_spills);
    newSlick.bindPopup(`<strong>New Anomaly Sheen Detected</strong><br>Region: ${sc.region}<br>Area: 2.3 km²<br>Confidence: 78%`).openPopup();
    tacticalMap.flyTo([offsetLat, offsetLng], sc.zoom);
  }
}

/* ==========================================================================
   6. DETECTION TIMELINE LINE CHART
   ========================================================================== */
function initTimelineChart() {
  const ctx = document.getElementById('detectionTimelineChart');
  if (!ctx) return;

  const labels = ['12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00'];
  const data = [12, 26, 32, 40, 48, 64, 91];

  timelineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Confidence Score',
        data: data,
        borderColor: '#0088ff',
        backgroundColor: 'rgba(0, 136, 255, 0.08)',
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointBackgroundColor: ['#0088ff', '#00e676', '#00d2ff', '#0088ff', '#ff3366', '#9d4edd', '#0088ff'],
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1.5,
        pointRadius: [3, 5, 5, 3, 5, 5, 4],
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0c1527',
          borderColor: '#1e3355',
          borderWidth: 1,
          callbacks: {
            label: (item) => ` Confidence: ${item.parsed.y}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)', borderColor: '#192b47' },
          ticks: { color: '#6882a3', font: { family: 'JetBrains Mono', size: 9.5 } }
        },
        y: {
          min: 0,
          max: 100,
          ticks: {
            stepSize: 25,
            color: '#6882a3',
            font: { family: 'JetBrains Mono', size: 9.5 }
          },
          grid: { color: 'rgba(255, 255, 255, 0.04)', borderColor: '#192b47' }
        }
      }
    }
  });
}

/* ==========================================================================
   7. DONUT CHARTS & ANALYTICS
   ========================================================================== */
function initDonutCharts() {
  const ctxAnomaly = document.getElementById('vesselAnomalyDonut');
  if (ctxAnomaly) {
    anomalyDonutChart = new Chart(ctxAnomaly, {
      type: 'doughnut',
      data: {
        labels: ['High Risk', 'Medium Risk', 'Low Risk'],
        datasets: [{
          data: [17, 35, 76],
          backgroundColor: ['#ff3366', '#ff9900', '#00e676'],
          borderWidth: 0,
          hoverOffset: 3
        }]
      },
      options: {
        cutout: '72%',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  }

  const ctxRisk = document.getElementById('riskDistributionDonut');
  if (ctxRisk) {
    riskDonutChart = new Chart(ctxRisk, {
      type: 'doughnut',
      data: {
        labels: ['High', 'Medium', 'Low'],
        datasets: [{
          data: [7, 21, 40],
          backgroundColor: ['#ff3366', '#ff9900', '#00e676'],
          borderWidth: 0,
          hoverOffset: 3
        }]
      },
      options: {
        cutout: '72%',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  }
}

function initAnalyticsCharts() {
  const ctxWeather = document.getElementById('weatheringAnalyticsChart');
  if (ctxWeather && !weatheringAnalyticsChart) {
    weatheringAnalyticsChart = new Chart(ctxWeather, {
      type: 'line',
      data: {
        labels: ['0h', '12h', '24h', '36h', '48h', '60h', '72h'],
        datasets: [
          {
            label: 'Evaporation Loss (%)',
            data: [0, 18, 28, 34, 38, 41, 43],
            borderColor: '#ff9900',
            backgroundColor: 'rgba(255, 153, 0, 0.1)',
            fill: true
          },
          {
            label: 'Emulsification Water Cut (%)',
            data: [0, 10, 25, 45, 60, 68, 72],
            borderColor: '#00d2ff',
            backgroundColor: 'rgba(0, 210, 255, 0.1)',
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#e2edf8', font: { size: 10 } } } }
      }
    });
  }

  const ctxSst = document.getElementById('sstAnalyticsChart');
  if (ctxSst && !sstAnalyticsChart) {
    sstAnalyticsChart = new Chart(ctxSst, {
      type: 'line',
      data: {
        labels: ['May 15', 'May 16', 'May 17', 'May 18', 'May 19', 'May 20'],
        datasets: [{
          label: 'Sea Surface Temp (°C)',
          data: [28.4, 28.7, 29.1, 29.3, 29.6, 29.8],
          borderColor: '#ff3366',
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#e2edf8', font: { size: 10 } } } }
      }
    });
  }
}

/* ==========================================================================
   8. RIGHT INCIDENT DETAILS & SUBTABS
   ========================================================================== */
function switchIncidentTab(subtabId) {
  const incTabs = document.querySelectorAll('.inc-tab-btn');
  incTabs.forEach(btn => {
    if (btn.innerText.toLowerCase().includes(subtabId.toLowerCase())) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  document.querySelectorAll('.inc-subview').forEach(v => v.classList.remove('active'));
  const target = document.getElementById(`inc-subview-${subtabId}`);
  if (target) {
    target.classList.add('active');
  }
}

function selectVesselById(vesselId) {
  const sc = DISASTER_SCENARIOS[activeScenarioId];
  if (!sc) return;

  const vessel = sc.vessels.find(v => v.id === vesselId) || sc.vessels[0];
  const primaryCard = document.getElementById('primarySourceCard');
  if (primaryCard) {
    primaryCard.innerHTML = `
      <div class="source-card-main">
        <div class="ship-icon-badge" style="color: ${vessel.color}; border-color: ${vessel.color};">
          <i class="fa-solid fa-ship"></i>
        </div>
        <div class="source-info">
          <div class="vessel-title">${vessel.name}</div>
          <div class="vessel-spec">MMSI: <span class="font-mono">${vessel.mmsi}</span></div>
          <div class="vessel-spec">Vessel Type: <span class="text-white">${vessel.type}</span></div>
          <div class="vessel-spec">Distance from Spill: <span class="text-white">${vessel.dist}</span></div>
          <div class="vessel-spec">Time in Area: <span class="text-white">${vessel.time}</span></div>
          <div class="vessel-spec">Behavior Anomaly Score: <span class="text-white">${vessel.anomaly}</span></div>
        </div>
        <div class="attribution-score-wrap">
          <div class="attr-label">Attribution Score</div>
          <div class="attr-score" style="color: ${vessel.color};">${vessel.attr}</div>
        </div>
      </div>
    `;
  }

  showToast(`Selected ${vessel.name} for Attribution Breakdown`);
  switchIncidentTab('overview');
}

function toggleIncidentStatus() {
  isIncidentClosed = !isIncidentClosed;
  const btn = document.getElementById('btnToggleClose');
  const statusText = document.getElementById('incStatusText');
  const alertBanner = document.getElementById('incAlertBanner');
  const sc = DISASTER_SCENARIOS[activeScenarioId];

  if (isIncidentClosed) {
    btn.innerHTML = `<i class="fa-solid fa-arrow-rotate-left"></i> Reopen Incident`;
    statusText.innerText = "Closed & Resolved";
    statusText.className = "text-green";
    alertBanner.style.background = "rgba(10, 45, 25, 0.7)";
    alertBanner.style.borderColor = "rgba(0, 230, 118, 0.4)";
    showToast(`Incident ${sc.code} marked as CLOSED & ARCHIVED`);
  } else {
    btn.innerHTML = `<i class="fa-regular fa-folder-closed"></i> Mark as Closed`;
    statusText.innerText = sc.status;
    statusText.className = sc.statusClass;
    alertBanner.style.background = sc.bannerBg;
    alertBanner.style.borderColor = sc.bannerBorder;
    showToast(`Incident ${sc.code} reopened for active investigation`);
  }
}

function toggleIncidentPanel() {
  const grid = document.getElementById('commandGrid');
  if (grid) {
    grid.classList.toggle('incident-closed');
    setTimeout(() => {
      if (tacticalMap) tacticalMap.invalidateSize();
    }, 300);
  }
}

function toggleActionItem(labelEl) {
  const isPending = labelEl.classList.contains('pending');
  labelEl.classList.toggle('completed', isPending);
  labelEl.classList.toggle('pending', !isPending);
  const actionText = labelEl.querySelector('.action-text')?.innerText;
  showToast(`Action '${actionText}' updated`);
}

function dispatchDirectAction(actionName) {
  showToast(`Dispatched: ${actionName}`);
}

function copyCoordinates() {
  const coords = document.getElementById('incCoords')?.innerText || '10.820 N, 79.130 E';
  navigator.clipboard.writeText(coords).then(() => {
    showToast(`Coordinates [${coords}] copied to clipboard`);
  }).catch(() => {
    showToast(`Coordinates copied: ${coords}`);
  });
}

/* ==========================================================================
   9. DATA TABLES & REGISTRIES (SHOW DISASTER AT DIFFERENT LOCATIONS)
   ========================================================================== */
function populateVesselsTable(customVessels) {
  const tbody = document.getElementById('vesselTableBody');
  if (!tbody) return;

  const vessels = customVessels || DISASTER_SCENARIOS[activeScenarioId].vessels;

  tbody.innerHTML = vessels.map(v => `
    <tr>
      <td><strong style="color:#fff;">${v.fullName || v.name}</strong></td>
      <td style="font-family:JetBrains Mono;">${v.mmsi}</td>
      <td>${v.type}</td>
      <td>${v.spd}</td>
      <td>${v.dist}</td>
      <td>${v.time}</td>
      <td><span class="text-amber font-mono">${v.anomaly}</span></td>
      <td><span class="${v.priorityBadge} font-mono">${v.attr}</span></td>
      <td>
        <button class="btn-action-secondary" style="padding:4px 8px; font-size:10.5px;" onclick="selectVesselById('${v.id}')">
          Inspect
        </button>
      </td>
    </tr>
  `).join('');
}

function filterVesselsTable(query) {
  const q = query.toLowerCase();
  const rows = document.querySelectorAll('#vesselTableBody tr');
  rows.forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

function populateIncidentRegistry() {
  const list = document.getElementById('incidentRegistryList');
  if (!list) return;

  const scenariosList = Object.values(DISASTER_SCENARIOS);

  list.innerHTML = scenariosList.map(sc => `
    <div class="inc-card-item">
      <div>
        <div style="font-size:13.5px; font-weight:700; color:#fff;">
          ${sc.title} <span class="font-mono text-cyan">(${sc.code})</span>
        </div>
        <div style="font-size:11px; color:#7e94b0; margin-top:4px;">
          Location: <strong class="text-white">${sc.coordsStr}</strong> | 
          Area: <strong class="text-white">${sc.affectedArea}</strong> | 
          Confidence: <strong class="text-green">${sc.confidence}</strong>
        </div>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <span class="${sc.vessels[0].priorityBadge} inc-badge-status">${sc.status}</span>
        <button class="btn-action-primary" style="padding:6px 12px; font-size:11px;" onclick="showDisasterLocation('${sc.id}')">
          <i class="fa-solid fa-map-location-dot"></i> Show On Map
        </button>
      </div>
    </div>
  `).join('');
}

function showDisasterLocation(scenarioId) {
  switchNavTab('dashboard');
  loadIncidentScenario(scenarioId, true);
  showToast(`Flying to Disaster Location: ${DISASTER_SCENARIOS[scenarioId].title}`);
}

function populateAlertFeed() {
  const container = document.getElementById('alertFeedContainer');
  if (!container) return;

  const alerts = [
    { type: 'danger', title: 'Critical Spill Slick Confirmed (Bay of Bengal)', desc: 'Sentinel-1 C-Band U-Net segmented 4.8 km² slick off Chennai corridor (10.820°N, 79.130°E).', time: '14:32 UTC' },
    { type: 'warning', title: 'Gulf of Mannar Ecological Alert', desc: 'Slick trajectory heading towards Mandapam Coral Reef Sanctuary (09.145°N, 79.210°E).', time: '12:10 UTC' },
    { type: 'danger', title: 'Mumbai High Offshore Sump Overflow', desc: 'Crude carrier MT Arabian Explorer loitering anomaly flagged at 19.420°N, 71.350°E.', time: '09:40 UTC' },
    { type: 'info', title: 'Andaman Sea Radar Pass Complete', desc: 'Sentinel-1 swath ingested over Port Blair navigation channel (11.650°N, 92.750°E).', time: '06:15 UTC' }
  ];

  container.innerHTML = alerts.map(a => `
    <div class="alert-feed-row ${a.type}">
      <div>
        <strong style="color:#fff;">${a.title}</strong>
        <p style="color:#7e94b0; font-size:11px; margin:2px 0;">${a.desc}</p>
      </div>
      <span class="font-mono text-cyan" style="font-size:11px;">${a.time}</span>
    </div>
  `).join('');
}

function acknowledgeAllAlerts() {
  showToast("All threat alerts acknowledged and logged to audit trail");
}

function deployCountermeasures() {
  const sc = DISASTER_SCENARIOS[activeScenarioId];
  showToast(`Countermeasures deployed to ${sc.title}: High-Seas Boom & Skimmer fleet dispatched`);
}

function saveSystemSettings() {
  showToast("MarineGuard AI configuration parameters saved successfully");
}

function initReportLivePreview() {
  const preview = document.getElementById('reportLivePreview');
  if (!preview) return;

  const sc = DISASTER_SCENARIOS[activeScenarioId] || DISASTER_SCENARIOS['INC-01'];

  preview.innerHTML = `
    <div style="border-bottom: 2px solid #00d2ff; padding-bottom: 12px; margin-bottom: 14px;">
      <h3 style="color:#fff; font-size:16px;">INTERNATIONAL MARITIME ORGANIZATION (IMO) SPILL REPORT</h3>
      <p style="color:#7e94b0; font-size:11.5px;">Incident Reference: <strong>${sc.code}</strong> | Region: <strong>${sc.region}</strong></p>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:14px;">
      <div>
        <strong>Geospatial Coordinates:</strong> ${sc.coordsStr}<br>
        <strong>Detected Surface Area:</strong> ${sc.affectedArea}<br>
        <strong>Estimated Slick Volume:</strong> ~750 bbl (Bonn Metallic Sheen)
      </div>
      <div>
        <strong>Attributed Vessel:</strong> ${sc.vessels[0].fullName}<br>
        <strong>Attribution Probability Score:</strong> ${sc.vessels[0].attr} (Critical)<br>
        <strong>Trajectory Back-Track:</strong> Intersects Transponder Deviation
      </div>
    </div>
  `;
}

function generateIncidentReport() {
  const modal = document.getElementById('reportModal');
  const content = document.getElementById('modalReportContent');
  const sc = DISASTER_SCENARIOS[activeScenarioId];
  if (!modal || !content || !sc) return;

  content.innerHTML = `
    <div style="border-bottom: 1px solid #1f3659; padding-bottom: 12px; margin-bottom: 12px;">
      <h2 style="color:#00d2ff; font-size:16px;">INTERNATIONAL MARITIME ORGANIZATION (IMO) INCIDENT DOSSIER</h2>
      <p style="color:#7e94b0; font-size:11px;">Ref: <strong>${sc.code}</strong> | Region: <strong>${sc.region}</strong> | Status: <strong>${sc.status.toUpperCase()}</strong></p>
    </div>
    
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px;">
      <div style="background:#091222; padding:10px; border-radius:4px; border:1px solid #16243b;">
        <strong style="color:#fff;">Incident Coordinates:</strong> ${sc.coordsStr}<br>
        <strong style="color:#fff;">Affected Slick Area:</strong> ${sc.affectedArea}<br>
        <strong style="color:#fff;">Confidence Score:</strong> ${sc.confidence}
      </div>
      <div style="background:#091222; padding:10px; border-radius:4px; border:1px solid #16243b;">
        <strong style="color:#ff3366;">Primary Candidate Vessel:</strong> ${sc.vessels[0].fullName}<br>
        <strong style="color:#fff;">MMSI:</strong> ${sc.vessels[0].mmsi}<br>
        <strong style="color:#fff;">Attribution Confidence:</strong> ${sc.vessels[0].attr} (High Probability)
      </div>
    </div>

    <p style="color:#e2edf8;"><strong>Multi-Sensor Evidence Summary:</strong></p>
    <ul style="color:#7e94b0; padding-left:18px; margin-top:4px;">
      <li>Copernicus Sentinel-1 C-Band SAR detected prominent negative backscatter signature in ${sc.region}.</li>
      <li>Spatial-temporal back-trajectory aligns directly with ${sc.vessels[0].name}'s kinematic deviation track.</li>
      <li>Local wind forcing: ${sc.wind.label}.</li>
      <li>Regional Maritime Authorities and Response units placed on primary alert.</li>
    </ul>
  `;

  modal.classList.add('show');
}

function closeReportModal() {
  const modal = document.getElementById('reportModal');
  if (modal) modal.classList.remove('show');
}

/* ==========================================================================
   10. HEADER DROPDOWNS & TOAST
   ========================================================================== */
function toggleNotifDropdown() {
  document.getElementById('notifDropdown')?.classList.toggle('show');
}
function clearNotifications() {
  const list = document.getElementById('notifList');
  if (list) list.innerHTML = '<p style="padding:12px; color:#7e94b0; text-align:center;">No pending alerts</p>';
  const badge = document.getElementById('notifBadge');
  if (badge) badge.innerText = '0';
}
function toggleProfileDropdown() {
  document.getElementById('profileDropdown')?.classList.toggle('show');
}
function toggleTheme() {
  document.body.classList.toggle('high-contrast-theme');
  showToast("Display contrast theme toggled");
}
function showToast(msg) {
  const toast = document.getElementById('toastPopup');
  const toastMsg = document.getElementById('toastMsg');
  if (!toast || !toastMsg) return;

  toastMsg.innerText = msg;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}
