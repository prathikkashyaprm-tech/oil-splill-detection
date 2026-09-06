/**
 * MarineGuard AI - Maritime Command Center Dashboard Controller
 * Smart India Hackathon 2026 (PS-1655)
 */

let activeScenarioData = null;
let mainMap = null;
let fullGisMap = null;
let mapLayers = {
  spill: null,
  vessels: null,
  drift: null,
  eco: null,
  risk: null
};
let weatheringChartInstance = null;
let fullWeatheringChartInstance = null;
let sstChartInstance = null;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initMaps();
  loadScenario("demo_gulf_of_mexico");
  startLiveClock();
});

// Live UTC Clock
function startLiveClock() {
  const clockEl = document.getElementById("liveClock");
  setInterval(() => {
    const now = new Date();
    clockEl.innerText = now.toISOString().replace("T", " ").substring(0, 19) + " UTC";
  }, 1000);
}

// Navigation Tabs
function initTabs() {
  const navBtns = document.querySelectorAll(".nav-btn");
  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      navBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const tabId = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
      const targetPane = document.getElementById(tabId);
      if (targetPane) {
        targetPane.classList.add("active");
      }

      // Invalidate map sizes upon tab switch
      setTimeout(() => {
        if (mainMap) mainMap.invalidateSize();
        if (fullGisMap) fullGisMap.invalidateSize();
      }, 100);
    });
  });
}

// Initialize Leaflet Maps
function initMaps() {
  const tileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const attribution = '&copy; OpenStreetMap contributors | Sentinel-1 SAR & AIS';
  // 1. Dashboard Overview Map
  mainMap = L.map("mainMap", { zoomControl: true }).setView([28.735, -88.382], 8);
  L.tileLayer(tileUrl, { attribution, maxZoom: 18 }).addTo(mainMap);

  // 2. Fullscreen GIS Map
  fullGisMap = L.map("fullGisMap", { zoomControl: true }).setView([28.735, -88.382], 8);
  L.tileLayer(tileUrl, { attribution, maxZoom: 18 }).addTo(fullGisMap);

  // Layer groups
  mapLayers.spill = L.layerGroup().addTo(mainMap);
  mapLayers.vessels = L.layerGroup().addTo(mainMap);
  mapLayers.drift = L.layerGroup().addTo(mainMap);
  mapLayers.eco = L.layerGroup().addTo(mainMap);
}

// Switch Scenario
function onScenarioChange(scenarioId) {
  loadScenario(scenarioId);
}

async function loadScenario(scenarioId) {
  try {
    const res = await fetch(`/api/demo/load-scenario?scenario_id=${scenarioId}`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to load scenario");
    const data = await res.json();
    activeScenarioData = data;
    renderScenario(data);
  } catch (err) {
    console.error("Error loading scenario:", err);
  }
}

// Main Render Method
function renderScenario(data) {
  renderKpis(data);
  renderMapLayers(data);
  renderCandidateVessels(data.candidate_vessels);
  renderIncidentSummary(data);
  renderWeatheringCharts(data.trajectories);
  renderSarStudio(data);
  renderTrajectoryTable(data.trajectories);
  renderEcologicalView(data.ecological_assessment);
  renderClimateView(data.environmental_record);
  renderRiskZonesView();
  renderEvidenceDossier(data.evidence_dossier);
  renderPrintableReport(data);
}

// Render Top KPI HUD
function renderKpis(data) {
  const spill = data.spill_detection || {};
  const eco = data.ecological_assessment || {};
  const candidates = data.candidate_vessels || [];
  const top = candidates[0] || {};
  const trajectories = data.trajectories || [];
  const lastStep = trajectories[trajectories.length - 1] || {};

  document.getElementById("kpiArea").innerText = `${spill.affected_area_km2?.toFixed(2) || "0.00"} km²`;
  document.getElementById("kpiVolume").innerText = `~${spill.estimated_volume_bbl?.toFixed(0) || 0} bbl (${spill.bonn_description || "Bonn Code 3"})`;
  document.getElementById("kpiConfidence").innerText = `${((spill.confidence_score || 0.9) * 100).toFixed(1)}%`;
  
  if (top.vessel) {
    document.getElementById("kpiTopVessel").innerText = top.vessel.vessel_name || `MMSI: ${top.vessel.mmsi}`;
    document.getElementById("kpiPriority").innerHTML = `Investigation Priority: <strong>${top.metrics?.investigation_priority_score?.toFixed(0) || 0}/100</strong>`;
  }

  document.getElementById("kpiEcoRisk").innerText = eco.ecological_risk_level || "HIGH";
  document.getElementById("kpiSpeciesCount").innerText = `${eco.exposed_species_count || 0} Sensitive Taxa in Drift Buffer`;
  document.getElementById("kpiDrift").innerText = `${lastStep.total_drift_km?.toFixed(1) || "0.0"} km`;
  document.getElementById("kpiEvap").innerText = `${lastStep.evaporated_fraction_pct?.toFixed(1) || 0}% Evaporative Decay`;
}

// Render Layers on Leaflet Map
function renderMapLayers(data) {
  if (!mainMap) return;

  mapLayers.spill.clearLayers();
  mapLayers.vessels.clearLayers();
  mapLayers.drift.clearLayers();
  mapLayers.eco.clearLayers();

  const spill = data.spill_detection;
  const center = [spill.center_latitude, spill.center_longitude];
  mainMap.setView(center, 9);
  if (fullGisMap) fullGisMap.setView(center, 9);

  // 1. Spill Polygon
  if (spill.spill_polygon_geojson && spill.spill_polygon_geojson.coordinates) {
    const coords = spill.spill_polygon_geojson.coordinates[0].map(pt => [pt[1], pt[0]]);
    const poly = L.polygon(coords, {
      color: "#ff3366",
      fillColor: "#ff3366",
      fillOpacity: 0.5,
      weight: 2
    }).bindPopup(`
      <div style="color:#000;">
        <strong>🚨 OIL SPILL SIGNATURE DETECTED</strong><br>
        Source: ${spill.source_satellite}<br>
        Area: ${spill.affected_area_km2} km²<br>
        Classification: ${spill.bonn_description}<br>
        Est. Volume: ~${spill.estimated_volume_bbl} bbl
      </div>
    `);
    mapLayers.spill.addLayer(poly);
  }

  // 2. AIS Candidate Vessels
  (data.candidate_vessels || []).forEach(cand => {
    const v = cand.vessel;
    const m = cand.metrics;
    const positions = v.positions || [];
    if (!positions.length) return;

    const latest = positions[positions.length - 1];
    const isTop = cand.rank === 1;

    // Track line
    const trackCoords = positions.map(p => [p.lat, p.lon]);
    const trackLine = L.polyline(trackCoords, {
      color: isTop ? "#ff3366" : "#00f0ff",
      weight: isTop ? 3 : 1.5,
      dashArray: isTop ? null : "4, 4",
      opacity: 0.8
    });
    mapLayers.vessels.addLayer(trackLine);

    // Vessel Marker
    const markerIcon = L.divIcon({
      className: "vessel-custom-marker",
      html: `<div style="background:${isTop ? '#ff3366' : '#00f0ff'}; width:12px; height:12px; border-radius:50%; border:2px solid #fff; box-shadow:0 0 8px ${isTop ? '#ff3366' : '#00f0ff'};"></div>`,
      iconSize: [12, 12]
    });

    const marker = L.marker([latest.lat, latest.lon], { icon: markerIcon }).bindPopup(`
      <div style="color:#000; font-family:sans-serif;">
        <strong>🚢 ${v.vessel_name}</strong> (${v.vessel_type})<br>
        MMSI: ${v.mmsi} | Flag: ${v.flag || "N/A"}<br>
        <strong>Investigation Priority: ${m.investigation_priority_score}/100</strong> (Rank #${cand.rank})<br>
        Speed: ${latest.sog_knots} kn | Course: ${latest.cog_deg}°<br>
        Closest Approach: ${m.min_distance_km} km<br>
        <em>Note: Association for maritime investigation priority only.</em>
      </div>
    `);
    mapLayers.vessels.addLayer(marker);
  });

  // 3. 72h Drift Trajectory Steps
  (data.trajectories || []).forEach(step => {
    const pCoords = step.predicted_polygon_geojson.coordinates[0].map(pt => [pt[1], pt[0]]);
    const driftPoly = L.polygon(pCoords, {
      color: "#ffaa00",
      fillColor: "#ff7700",
      fillOpacity: 0.2,
      weight: 1.5,
      dashArray: "3, 3"
    }).bindPopup(`
      <div style="color:#000;">
        <strong>🌊 Drift Forecast (+${step.forecast_hours}h)</strong><br>
        Total Drift: ${step.total_drift_km} km @ ${step.drift_bearing_deg}°<br>
        Evaporated: ${step.evaporated_fraction_pct}%<br>
        Emulsified: ${step.emulsified_water_pct}%<br>
        Coastal Threat: ${step.coastal_hit_warning ? '⚠️ IMMINENT' : 'None'}
      </div>
    `);
    mapLayers.drift.addLayer(driftPoly);
  });

  // 4. Protected Habitats (MPAs)
  (data.ecological_assessment?.nearby_mpas || []).forEach(mpa => {
    // Circle approximation
    const mpaMarker = L.circle([data.spill_detection.center_latitude + 0.3, data.spill_detection.center_longitude + 0.4], {
      color: "#00e676",
      fillColor: "#00e676",
      fillOpacity: 0.15,
      radius: 15000
    }).bindPopup(`
      <div style="color:#000;">
        <strong>🌿 ${mpa.name}</strong><br>
        Type: ${mpa.type}<br>
        Protection: ${mpa.protection_level}<br>
        Distance: ${mpa.distance_km} km
      </div>
    `);
    mapLayers.eco.addLayer(mpaMarker);
  });
}

function toggleLayer(layerName) {
  const chk = document.getElementById(`chk${layerName.charAt(0).toUpperCase() + layerName.slice(1)}`);
  if (!chk || !mapLayers[layerName]) return;
  if (chk.checked) {
    mainMap.addLayer(mapLayers[layerName]);
  } else {
    mainMap.removeLayer(mapLayers[layerName]);
  }
}

// Render Candidate Vessels Ranking Cards
function renderCandidateVessels(candidates) {
  const listEl = document.getElementById("candidateVesselsList");
  const fullGridEl = document.getElementById("fullVesselDetailsGrid");
  if (!listEl) return;

  listEl.innerHTML = "";
  if (fullGridEl) fullGridEl.innerHTML = "";

  (candidates || []).forEach(cand => {
    const v = cand.vessel || {};
    const m = cand.metrics || {};
    const score = m.investigation_priority_score || 0;
    const isTop = cand.rank === 1;

    const scoreColor = score >= 80 ? "var(--accent-red)" : score >= 50 ? "var(--accent-amber)" : "var(--accent-cyan)";

    const card = document.createElement("div");
    card.className = `candidate-card ${isTop ? 'top-ranked' : ''}`;
    card.innerHTML = `
      <div class="candidate-header">
        <span class="candidate-name">#${cand.rank} ${v.vessel_name || 'MMSI ' + v.mmsi} <small class="text-muted">(${v.vessel_type || 'Tanker'})</small></span>
        <div class="priority-gauge-wrapper">
          <span class="priority-score" style="color:${scoreColor}">${score.toFixed(0)}/100</span>
          <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:${score}%; background:${scoreColor};"></div>
          </div>
        </div>
      </div>
      <div class="candidate-metrics-row">
        <div class="metric-box">
          <span class="label">PROXIMITY</span>
          <span class="val">${m.min_distance_km} km</span>
        </div>
        <div class="metric-box">
          <span class="label">SPEED DROP</span>
          <span class="val">${m.speed_anomaly_drop_kn} kn</span>
        </div>
        <div class="metric-box">
          <span class="label">COURSE DEV</span>
          <span class="val">${m.route_deviation_deg}°</span>
        </div>
        <div class="metric-box">
          <span class="label">TIME IN ZONE</span>
          <span class="val">${m.time_in_spill_zone_min} min</span>
        </div>
      </div>
      ${(m.anomaly_flags || []).map(f => `<div class="anomaly-tag"><i class="fa-solid fa-triangle-exclamation"></i> ${f}</div>`).join('')}
    `;
    listEl.appendChild(card);

    if (fullGridEl) {
      const fullCard = card.cloneNode(true);
      fullGridEl.appendChild(fullCard);
    }
  });
}

// Render Executive Summary
function renderIncidentSummary(data) {
  const summaryEl = document.getElementById("incidentSummaryText");
  const quickRespEl = document.getElementById("quickResponseContainer");
  const dossier = data.evidence_dossier || {};

  if (summaryEl) {
    summaryEl.innerText = dossier.executive_summary || "Analyzing multi-sensor evidence...";
  }

  if (quickRespEl && dossier.recommended_response_actions) {
    quickRespEl.innerHTML = `
      <h4 class="mt-2 text-cyan"><i class="fa-solid fa-bell"></i> Recommended Response Action:</h4>
      <div class="alert-box-urgent">
        <strong>${dossier.recommended_response_actions[0]?.priority}:</strong> ${dossier.recommended_response_actions[0]?.action}
      </div>
    `;
  }
}

// Render Weathering Chart (Evaporation vs Emulsification)
function renderWeatheringCharts(trajectories) {
  if (!trajectories || !trajectories.length) return;

  const labels = trajectories.map(t => `+${t.forecast_hours}h`);
  const evapData = trajectories.map(t => t.evaporated_fraction_pct);
  const emulsData = trajectories.map(t => t.emulsified_water_pct);

  const ctx = document.getElementById("weatheringChart");
  if (!ctx) return;

  if (weatheringChartInstance) weatheringChartInstance.destroy();

  weatheringChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Evaporated Fraction (%)",
          data: evapData,
          borderColor: "#00f0ff",
          backgroundColor: "rgba(0, 240, 255, 0.1)",
          fill: true,
          tension: 0.3
        },
        {
          label: "Water Emulsification (%)",
          data: emulsData,
          borderColor: "#ffaa00",
          backgroundColor: "rgba(255, 170, 0, 0.1)",
          fill: true,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#e2edf8", font: { size: 10 } } }
      },
      scales: {
        x: { ticks: { color: "#8ba2be" }, grid: { color: "rgba(30, 70, 115, 0.2)" } },
        y: { ticks: { color: "#8ba2be" }, grid: { color: "rgba(30, 70, 115, 0.2)" }, min: 0, max: 100 }
      }
    }
  });

  // Full Weathering Chart in Trajectory tab
  const ctxFull = document.getElementById("weatheringFullChart");
  if (ctxFull) {
    if (fullWeatheringChartInstance) fullWeatheringChartInstance.destroy();
    fullWeatheringChartInstance = new Chart(ctxFull, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Volatile Evaporative Loss (%)",
            data: evapData,
            borderColor: "#00f0ff",
            backgroundColor: "rgba(0, 240, 255, 0.15)",
            fill: true
          },
          {
            label: "Mousse Emulsification Water Uptake (%)",
            data: emulsData,
            borderColor: "#ff7700",
            backgroundColor: "rgba(255, 119, 0, 0.15)",
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#fff" } } },
        scales: {
          x: { ticks: { color: "#8ba2be" }, grid: { color: "rgba(30, 70, 115, 0.2)" } },
          y: { ticks: { color: "#8ba2be" }, grid: { color: "rgba(30, 70, 115, 0.2)" } }
        }
      }
    });
  }
}

// Render SAR Studio
function renderSarStudio(data) {
  const spill = data.spill_detection || {};
  const rawImg = document.getElementById("rawSarImg");
  const maskImg = document.getElementById("maskSarImg");

  if (rawImg && spill.raw_image_url) rawImg.src = spill.raw_image_url;
  if (maskImg && (spill.overlay_image_url || spill.mask_image_url)) {
    maskImg.src = spill.overlay_image_url || spill.mask_image_url;
  }

  const badge = document.getElementById("bonnBadge");
  const title = document.getElementById("bonnTitle");
  const thick = document.getElementById("bonnThickness");

  if (badge) badge.innerText = `CODE ${spill.bonn_code || 3}`;
  if (title) title.innerText = spill.bonn_description || "Code 3: Metallic Sheen";
  if (thick) thick.innerText = `Nominal Thickness: ${spill.nominal_thickness_um || 25} µm | Volume: ~${spill.estimated_volume_bbl || 0} bbl (~${spill.estimated_volume_m3 || 0} m³)`;
}

// Benchmark preset testing
async function testBenchmarkSample(sampleId) {
  try {
    const formData = new FormData();
    formData.append("sample_id", sampleId);
    formData.append("center_lat", "28.7350");
    formData.append("center_lon", "-88.3820");

    const res = await fetch("/api/detect-spill", { method: "POST", body: formData });
    if (!res.ok) throw new Error("Detection failed");
    const result = await res.json();
    renderScenario(result);
  } catch (e) {
    console.error("Error in benchmark test:", e);
  }
}

// File Upload Handler
async function handleFileUpload(files) {
  if (!files || !files.length) return;
  const file = files[0];

  const formData = new FormData();
  formData.append("file", file);
  formData.append("center_lat", "28.7350");
  formData.append("center_lon", "-88.3820");

  try {
    const res = await fetch("/api/detect-spill", { method: "POST", body: formData });
    if (!res.ok) throw new Error("SAR file processing failed");
    const result = await res.json();
    renderScenario(result);
  } catch (e) {
    console.error("Error processing file:", e);
  }
}

// Render Trajectory Table
function renderTrajectoryTable(trajectories) {
  const tbody = document.querySelector("#trajectoryTable tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  (trajectories || []).forEach(t => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>+${t.forecast_hours} Hours</strong></td>
      <td>${t.forecast_timestamp.substring(11, 16)} UTC</td>
      <td>${t.total_drift_km} km @ ${t.drift_bearing_deg}°</td>
      <td class="text-cyan">${t.evaporated_fraction_pct}%</td>
      <td class="text-orange">${t.emulsified_water_pct}%</td>
      <td>${t.coastal_hit_warning ? '<span class="badge badge-critical">IMMINENT HIT</span>' : '<span class="badge badge-info">CLEAR</span>'}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Render Ecological Impact Tab
function renderEcologicalView(eco) {
  if (!eco) return;

  const speciesListEl = document.getElementById("ecoSpeciesList");
  const mpaListEl = document.getElementById("ecoMpaList");
  const badgeEl = document.getElementById("ecoRiskLevelBadge");

  if (badgeEl) badgeEl.innerText = `${eco.ecological_risk_level} IMPACT POTENTIAL`;

  if (speciesListEl) {
    speciesListEl.innerHTML = "<h4><i class='fa-solid fa-paw text-cyan'></i> Exposed Marine Species (OBIS)</h4>";
    (eco.exposed_species_records || []).forEach(sp => {
      const card = document.createElement("div");
      card.className = "species-card";
      card.innerHTML = `
        <div class="species-header">
          <strong>${sp.common_name}</strong>
          <span class="badge badge-critical">${sp.iucn_status}</span>
        </div>
        <p class="text-muted" style="font-size:11px;"><em>${sp.scientific_name}</em> | ${sp.taxon_group}</p>
        <p style="font-size:11px;"><strong>Proximity:</strong> ${sp.closest_distance_km} km | <strong>Exposure:</strong> ${sp.potential_exposure_level}</p>
        <p style="font-size:10px; color:var(--text-muted); margin-top:4px;"><strong>Sensitivity:</strong> ${sp.oil_sensitivity_factors}</p>
      `;
      speciesListEl.appendChild(card);
    });
  }

  if (mpaListEl) {
    mpaListEl.innerHTML = "<h4><i class='fa-solid fa-shield-cat text-amber'></i> Marine Protected Areas (MPAs)</h4>";
    (eco.nearby_mpas || []).forEach(mpa => {
      const card = document.createElement("div");
      card.className = "species-card";
      card.innerHTML = `
        <div class="species-header">
          <strong>${mpa.name}</strong>
          <span class="badge badge-warning">${mpa.protection_level}</span>
        </div>
        <p style="font-size:11px;"><strong>Type:</strong> ${mpa.type} | <strong>Distance:</strong> ${mpa.distance_km} km</p>
      `;
      mpaListEl.appendChild(card);
    });
  }
}

// Render Climate Tab
function renderClimateView(env) {
  if (!env) return;

  const statsGrid = document.getElementById("climateStatsGrid");
  const vectorHud = document.getElementById("vectorHud");
  const noteBox = document.getElementById("climatologyNoteBox");

  if (statsGrid) {
    statsGrid.innerHTML = `
      <div class="metric-box">
        <span class="label">SEA SURFACE TEMP</span>
        <span class="val text-red">${env.sea_surface_temp_c}°C</span>
      </div>
      <div class="metric-box">
        <span class="label">SST ANOMALY</span>
        <span class="val text-orange">+${env.sst_anomaly_c}°C</span>
      </div>
      <div class="metric-box">
        <span class="label">HEATWAVE STATUS</span>
        <span class="val text-amber">${env.marine_heatwave_category}</span>
      </div>
      <div class="metric-box">
        <span class="label">CHLOROPHYLL-A</span>
        <span class="val text-cyan">${env.chlorophyll_mg_m3 || 1.45} mg/m³</span>
      </div>
    `;
  }

  if (vectorHud) {
    vectorHud.innerHTML = `
      <div class="metric-box">
        <span class="label">10M WIND FORCING</span>
        <span class="val text-cyan">${env.wind_speed_knots} kn @ ${env.wind_direction_deg}° (${env.wind_cardinal || 'SE'})</span>
      </div>
      <div class="metric-box">
        <span class="label">SURFACE CURRENT</span>
        <span class="val text-purple">${env.current_speed_knots} kn @ ${env.current_direction_deg}° (${env.current_name || 'Regional Drift'})</span>
      </div>
      <div class="metric-box">
        <span class="label">SIGNIFICANT WAVE HEIGHT</span>
        <span class="val text-orange">${env.wave_height_m} m (${env.wave_period_s || 6.0}s)</span>
      </div>
    `;
  }

  if (noteBox) {
    noteBox.innerHTML = `<strong><i class="fa-solid fa-circle-info"></i> Climatological Context:</strong><br>${env.climatological_context}`;
  }
}

// Render Risk Zones
async function renderRiskZonesView() {
  const container = document.getElementById("riskCorridorsList");
  if (!container) return;

  try {
    const res = await fetch("/api/risk-zones");
    const zones = await res.json();

    container.innerHTML = "";
    zones.forEach(z => {
      const card = document.createElement("div");
      card.className = "candidate-card";
      card.innerHTML = `
        <div class="candidate-header">
          <strong>${z.zone_name}</strong>
          <span class="badge badge-critical">${z.risk_level} RISK (${z.composite_risk_score}/100)</span>
        </div>
        <p style="font-size:11px; color:var(--text-muted); margin-top:4px;">
          Traffic Density: <strong>${z.traffic_density_ships_per_day} ships/day</strong> | Tanker Share: <strong>${z.tanker_percentage}%</strong>
        </p>
        <p style="font-size:11px; margin-top:4px;"><strong>Recommended Patrol Action:</strong> ${z.recommended_patrol}</p>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error("Error loading risk zones:", e);
  }
}

// Render Evidence Dossier
function renderEvidenceDossier(dossier) {
  const container = document.getElementById("pillarsGrid");
  if (!container || !dossier) return;

  container.innerHTML = "";
  (dossier.pillars || []).forEach(p => {
    const card = document.createElement("div");
    card.className = "pillar-card";
    
    let rowsHtml = "";
    Object.keys(p).forEach(k => {
      if (k !== "pillar") {
        const val = Array.isArray(p[k]) ? p[k].join(", ") : p[k];
        rowsHtml += `
          <div class="pillar-row">
            <span class="text-muted">${k.replace(/_/g, ' ').toUpperCase()}:</span>
            <strong>${val}</strong>
          </div>
        `;
      }
    });

    card.innerHTML = `
      <h4>${p.pillar}</h4>
      ${rowsHtml}
    `;
    container.appendChild(card);
  });
}

// Render Printable IMO Incident Report
function renderPrintableReport(data) {
  const reportEl = document.getElementById("printableReport");
  if (!reportEl) return;

  const spill = data.spill_detection || {};
  const eco = data.ecological_assessment || {};
  const top = (data.candidate_vessels || [])[0] || {};
  const dossier = data.evidence_dossier || {};

  reportEl.innerHTML = `
    <div style="text-align:center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px;">
      <h2>INTERNATIONAL MARITIME POLLUTION INCIDENT REPORT</h2>
      <p style="font-size:12px;">Generated in accordance with IMO Bonn Agreement Standards | MarineGuard AI PS-1655</p>
      <p style="font-size:11px; color:#555;">Incident Reference: <strong>${data.incident_id || 'MG-2026-001'}</strong> | Date: <strong>${new Date().toUTCString()}</strong></p>
    </div>

    <h3>1. Satellite Detection Summary</h3>
    <table style="width:100%; border-collapse:collapse; margin-bottom:16px;" border="1" cellpadding="6">
      <tr><td><strong>Sensor:</strong></td><td>${spill.source_satellite}</td><td><strong>Confidence:</strong></td><td>${((spill.confidence_score||0.9)*100).toFixed(1)}%</td></tr>
      <tr><td><strong>Coordinates:</strong></td><td>${spill.center_latitude}° N, ${spill.center_longitude}° E</td><td><strong>Affected Area:</strong></td><td>${spill.affected_area_km2} km²</td></tr>
      <tr><td><strong>Bonn Classification:</strong></td><td>${spill.bonn_description}</td><td><strong>Est. Volume:</strong></td><td>${spill.estimated_volume_bbl} bbl (~${spill.estimated_volume_m3} m³)</td></tr>
    </table>

    <h3>2. AIS Vessel Correlation & Behavioral Attribution</h3>
    <p style="font-size:11px; color:#444; margin-bottom:8px;"><em>Disclaimer: Ranking signifies Investigation Priority based on spatio-temporal telemetry; does not establish legal liability.</em></p>
    <table style="width:100%; border-collapse:collapse; margin-bottom:16px;" border="1" cellpadding="6">
      <tr><td><strong>Primary Candidate:</strong></td><td>${top.vessel?.vessel_name || 'N/A'}</td><td><strong>MMSI:</strong></td><td>${top.vessel?.mmsi || 'N/A'}</td></tr>
      <tr><td><strong>Investigation Priority:</strong></td><td><strong>${top.metrics?.investigation_priority_score || 0} / 100</strong></td><td><strong>Closest Approach:</strong></td><td>${top.metrics?.min_distance_km || 0} km</td></tr>
      <tr><td><strong>Kinematic Anomalies:</strong></td><td colspan="3">${(top.metrics?.anomaly_flags || []).join('; ') || 'None'}</td></tr>
    </table>

    <h3>3. Marine Ecological & Environmental Sensitivity</h3>
    <table style="width:100%; border-collapse:collapse; margin-bottom:16px;" border="1" cellpadding="6">
      <tr><td><strong>Ecological Threat Level:</strong></td><td><strong>${eco.ecological_risk_level}</strong></td><td><strong>Exposed Taxa Count:</strong></td><td>${eco.exposed_species_count}</td></tr>
      <tr><td><strong>Protected Habitats:</strong></td><td colspan="3">${(eco.nearby_mpas || []).map(m => m.name).join(', ') || 'None within 50km'}</td></tr>
    </table>

    <h3>4. Recommended Operational Directives</h3>
    <ol style="padding-left:20px; font-size:12px;">
      ${(dossier.recommended_response_actions || []).map(a => `<li><strong>${a.priority}:</strong> ${a.action} <em>(Agency: ${a.agency})</em></li>`).join('')}
    </ol>
  `;
}

function printReport() {
  window.print();
}

function resetMapView() {
  if (mainMap && activeScenarioData) {
    const spill = activeScenarioData.spill_detection;
    mainMap.setView([spill.center_latitude, spill.center_longitude], 9);
  }
}
