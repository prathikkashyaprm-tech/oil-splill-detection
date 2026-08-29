/**
 * MarineGuard AI - Incident Investigation Report Generator Module
 */
const ReportModule = {
  async generateReport(incidentId) {
    app.showNotification(`📄 Generating formal investigation report for ${incidentId}...`, 'info');
    try {
      const response = await fetch(`/api/report/${incidentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      const html = await response.text();
      const reportWindow = window.open('', '_blank');
      if (reportWindow) {
        reportWindow.document.open();
        reportWindow.document.write(html);
        reportWindow.document.close();
        app.showNotification('✅ Investigation Report opened in new window', 'success');
      } else {
        // Popups blocked fallback: download or inline view
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Investigation_Report_${incidentId}.html`;
        a.click();
        URL.revokeObjectURL(url);
        app.showNotification('✅ Investigation Report downloaded', 'success');
      }
    } catch(err) {
      console.error(err);
      app.showNotification('❌ Could not generate report. Check incident ID.', 'error');
    }
  }
};
