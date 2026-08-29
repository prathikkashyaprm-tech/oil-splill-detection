/**
 * MarineAI API Client Layer
 */
const MarineAPI = {
  async getSamples() {
    const res = await fetch('/api/samples');
    if (!res.ok) throw new Error('Failed to fetch benchmark samples');
    return await res.json();
  },

  async getHotspots() {
    const res = await fetch('/api/hotspots');
    if (!res.ok) throw new Error('Failed to fetch marine hotspots');
    return await res.json();
  },

  async detectImage({ file = null, sampleName = null, sensorType = 'AUTO', kmPerPixel = null }) {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    if (sampleName) {
      formData.append('sample_name', sampleName);
    }
    formData.append('sensor_type', sensorType);
    if (kmPerPixel) {
      formData.append('km_per_pixel', kmPerPixel);
    }

    const res = await fetch('/api/detect', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Detection failed');
    }
    return await res.json();
  },

  async simulateDrift(params) {
    const res = await fetch('/api/simulate-drift', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error('Simulation failed');
    return await res.json();
  },

  async generateReport(analysisData, locationName) {
    const res = await fetch('/api/generate-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis_data: analysisData,
        location_name: locationName
      })
    });
    if (!res.ok) throw new Error('Report generation failed');
    return await res.text();
  }
};
