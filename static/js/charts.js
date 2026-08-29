/**
 * MarineAI Telemetry & Weathering Charts (Lightweight Canvas Engine)
 */

function renderWeatheringChart(canvasId, weatheringData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !weatheringData || weatheringData.length === 0) return;
  
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  
  ctx.clearRect(0, 0, w, h);
  
  const padding = { top: 25, right: 30, bottom: 35, left: 45 };
  const plotW = w - padding.left - padding.right;
  const plotH = h - padding.top - padding.bottom;
  
  // Background grid
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (plotH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(w - padding.right, y);
    ctx.stroke();
    
    // Y-axis label (Percentage 0 to 100%)
    ctx.fillStyle = '#64748b';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';
    ctx.fillText(`${100 - i * 25}%`, padding.left - 8, y + 3);
  }
  
  const hours = weatheringData.map(d => d.hour);
  const maxHour = Math.max(...hours, 72);
  
  // 1. Draw Evaporation Curve (Cyan #00f0ff)
  ctx.beginPath();
  ctx.strokeStyle = '#00f0ff';
  ctx.lineWidth = 2.5;
  weatheringData.forEach((d, idx) => {
    const x = padding.left + (d.hour / maxHour) * plotW;
    const y = padding.top + plotH - (d.evaporated_percent / 100.0) * plotH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  
  // 2. Draw Emulsification Water Content Curve (Amber #f59e0b)
  ctx.beginPath();
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 4]);
  weatheringData.forEach((d, idx) => {
    const x = padding.left + (d.hour / maxHour) * plotW;
    const y = padding.top + plotH - (d.water_emulsification_percent / 100.0) * plotH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.setLineDash([]);
  
  // X-axis time labels (T+0h, T+24h, T+48h, T+72h)
  weatheringData.forEach(d => {
    const x = padding.left + (d.hour / maxHour) * plotW;
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`T+${d.hour}h`, x, h - 12);
  });
}
