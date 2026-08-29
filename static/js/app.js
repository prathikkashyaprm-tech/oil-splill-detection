/**
 * MarineGuard AI - Main Dashboard Application Controller
 */
const app = {
  activeTab: 'dashboard',

  async init() {
    this.initLiveTimeUpdater();
    this.createToastContainer();

    // Initialize modules
    if (window.MapModule) MapModule.initMap();
    if (window.AISModule) AISModule.init();
    if (window.AnomalyModule) AnomalyModule.init();
    if (window.IncidentModule) IncidentModule.init();

    await this.fetchDashboardStats();
    this.renderBottomCards();
    this.renderDetectionTimeline();

    // Tab switching event listeners
    document.querySelectorAll('.nav-menu li').forEach(li => {
      li.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-menu li').forEach(el => el.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const tabId = e.currentTarget.dataset.tab;
        if (tabId) this.switchTab(tabId);
      });
    });

    // Window resize handler for canvas rendering
    window.addEventListener('resize', () => {
      this.renderBottomCards();
      this.renderDetectionTimeline();
      if (window.MapModule && window.MapModule.map) {
        window.MapModule.map.invalidateSize();
      }
    });
  },

  switchTab(tabName) {
    this.activeTab = tabName;
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    const target = document.getElementById('tab-' + tabName);
    if (target) {
      target.classList.add('active');
      if (tabName === 'dashboard' && window.MapModule && window.MapModule.map) {
        setTimeout(() => window.MapModule.map.invalidateSize(), 100);
      }
    }
  },

  async fetchDashboardStats() {
    try {
      const stats = await fetch('/api/dashboard/stats').then(r => r.json());
      const activeEl = document.querySelector('.stat-chip:nth-child(1) span');
      const riskEl = document.querySelector('.stat-chip:nth-child(2) span');
      const spillEl = document.querySelector('.stat-chip:nth-child(3) span');
      const areaEl = document.querySelector('.stat-chip:nth-child(4) span');

      if (activeEl) activeEl.textContent = String(stats.active_incidents).padStart(2, '0');
      if (riskEl) riskEl.textContent = String(stats.high_risk_vessels).padStart(2, '0');
      if (spillEl) spillEl.textContent = String(stats.spills_detected).padStart(2, '0');
      if (areaEl) areaEl.textContent = `${stats.total_area_affected} km²`;
    } catch(err) {
      console.warn('Could not fetch stats, using default values.');
    }
  },

  initLiveTimeUpdater() {
    const el = document.getElementById('live-datetime');
    if (!el) return;
    const update = () => {
      const now = new Date();
      const day = now.getUTCDate();
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const month = months[now.getUTCMonth()];
      const year = now.getUTCFullYear();
      const hours = String(now.getUTCHours()).padStart(2, '0');
      const mins = String(now.getUTCMinutes()).padStart(2, '0');
      const secs = String(now.getUTCSeconds()).padStart(2, '0');
      el.textContent = `${day} ${month} ${year}, ${hours}:${mins}:${secs} UTC`;
    };
    update();
    setInterval(update, 1000);
  },

  renderBottomCards() {
    // 1. Vessel Anomaly Overview Donut (128 vessels)
    this.drawDonut('anomaly-donut', [
      { color: '#ff1744', val: 17 }, // High
      { color: '#ffab00', val: 35 }, // Med
      { color: '#00e676', val: 76 }  // Low
    ]);

    // 2. Risk Level Distribution Donut (68 vessels)
    this.drawDonut('risk-donut', [
      { color: '#ff1744', val: 7 },  // High
      { color: '#ffab00', val: 21 }, // Med
      { color: '#00e676', val: 40 }  // Low
    ]);
  },

  drawDonut(canvasId, segments) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const total = segments.reduce((acc, s) => acc + s.val, 0);

    // High-DPI crisp rendering
    const width = 120;
    const height = 120;
    canvas.width = width * 2;
    canvas.height = height * 2;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(2, 2);

    ctx.clearRect(0, 0, width, height);

    let startAngle = -Math.PI / 2;
    const x = width / 2;
    const y = height / 2;
    const radius = 42;
    const lineWidth = 10;

    segments.forEach(s => {
      const sliceAngle = (s.val / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.arc(x, y, radius, startAngle, startAngle + sliceAngle - 0.04);
      ctx.lineWidth = lineWidth;
      ctx.strokeStyle = s.color;
      ctx.lineCap = 'round';
      ctx.stroke();
      startAngle += sliceAngle;
    });
  },

  renderDetectionTimeline() {
    const canvas = document.getElementById('timeline-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const width = canvas.parentElement.clientWidth - 30 || 600;
    const height = 130;
    canvas.width = width * 2;
    canvas.height = height * 2;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(2, 2);

    ctx.clearRect(0, 0, width, height);

    const paddingLeft = 45;
    const paddingRight = 40;
    const paddingTop = 42;
    const paddingBottom = 26;
    const graphWidth = width - paddingLeft - paddingRight;
    const graphHeight = height - paddingTop - paddingBottom;

    // Y Axis Guidelines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#546e85';
    ctx.font = '10px "Inter", sans-serif';
    ctx.textAlign = 'right';

    [100, 75, 50, 25, 0].forEach(val => {
      const y = paddingTop + (1 - val / 100) * graphHeight;
      ctx.beginPath();
      ctx.moveTo(paddingLeft, y);
      ctx.lineTo(paddingLeft + graphWidth, y);
      ctx.stroke();
      ctx.fillText(`${val}`, paddingLeft - 8, y + 3);
    });

    // Time points
    const timeLabels = ['12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00'];
    ctx.textAlign = 'center';
    timeLabels.forEach((t, i) => {
      const x = paddingLeft + (i / (timeLabels.length - 1)) * graphWidth;
      ctx.fillText(t, x, height - 8);
    });

    // Data points (Confidence vs Time)
    const points = [
      { xIdx: 0, val: 12, label: null },
      { xIdx: 1.3, val: 32, label: 'Anomaly Detected', color: '#00e676' },
      { xIdx: 2.7, val: 42, label: 'Satellite Scan Tasked', color: '#00d4ff' },
      { xIdx: 4.0, val: 56, label: 'Oil Spill Detected', color: '#ff1744' },
      { xIdx: 5.0, val: 78, label: 'High Confidence', color: '#b388ff' },
      { xIdx: 6.0, val: 91, label: null }
    ];

    const coordPoints = points.map(p => ({
      x: paddingLeft + (p.xIdx / 6) * graphWidth,
      y: paddingTop + (1 - p.val / 100) * graphHeight,
      label: p.label,
      color: p.color,
      val: p.val
    }));

    // Draw Smooth Line
    ctx.beginPath();
    ctx.strokeStyle = '#00d4ff';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(0, 212, 255, 0.4)';
    ctx.shadowBlur = 8;

    coordPoints.forEach((p, idx) => {
      if (idx === 0) ctx.moveTo(p.x, p.y);
      else {
        const prev = coordPoints[idx - 1];
        const cx = (prev.x + p.x) / 2;
        ctx.bezierCurveTo(cx, prev.y, cx, p.y, p.x, p.y);
      }
    });
    ctx.stroke();
    ctx.shadowBlur = 0; // reset shadow

    // Draw Points and Badge Tags
    coordPoints.forEach(p => {
      // Glow dot
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#00d4ff';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Tag Label if milestone
      if (p.label) {
        ctx.font = '9px "Inter", sans-serif';
        const textWidth = ctx.measureText(p.label).width;
        const tagHeight = 16;
        const tagWidth = textWidth + 12;
        const tagX = p.x - tagWidth / 2;
        const tagY = p.y - 28;

        // Tag background
        ctx.fillStyle = 'rgba(13, 30, 53, 0.95)';
        ctx.strokeStyle = p.color || '#00d4ff';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(tagX, tagY, tagWidth, tagHeight, 3);
        ctx.fill();
        ctx.stroke();

        // Tag text
        ctx.fillStyle = p.color || '#00d4ff';
        ctx.textAlign = 'center';
        ctx.fillText(p.label, p.x, tagY + 11);

        // Little connector line from badge to point
        ctx.beginPath();
        ctx.strokeStyle = p.color || '#00d4ff';
        ctx.moveTo(p.x, tagY + tagHeight);
        ctx.lineTo(p.x, p.y - 4);
        ctx.stroke();
      }
    });
  },

  createToastContainer() {
    if (document.getElementById('toast-container')) return;
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
    `;
    document.body.appendChild(div);
  },

  showNotification(message, type = 'info') {
    this.createToastContainer();
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'success' ? '#00e676' : type === 'error' ? '#ff1744' : type === 'warning' ? '#ffab00' : '#00d4ff';
    
    toast.style.cssText = `
      background: #0d1e35;
      color: #e8f0fe;
      border-left: 4px solid ${bg};
      border-radius: 6px;
      padding: 12px 18px;
      font-size: 13px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.5);
      border: 1px solid rgba(255,255,255,0.08);
      border-left: 4px solid ${bg};
      opacity: 0;
      transform: translateY(-10px);
      transition: all 0.3s ease;
      pointer-events: auto;
      max-width: 380px;
    `;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

document.addEventListener('DOMContentLoaded', () => app.init());
