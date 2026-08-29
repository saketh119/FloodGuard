import { useState } from 'react';
import styles from './Reports.module.css';
import { LOCATIONS, deriveDashboardData } from '../../data/locations';
import { FileText, Download, Filter } from 'lucide-react';

function buildReports(dash, location) {
  if (!dash) return [];
  return [
    {
      id: 'daily-weather',
      title: 'Daily Weather Summary',
      desc: `Current conditions at ${dash.stationName}`,
      date: new Date().toLocaleDateString('en-IN'),
      type: 'Weather',
      severity: 'brand',
      rows: [
        ['Location', `${location.label}, ${location.state}`],
        ['Temperature', `${dash.temp}°C`],
        ['Humidity', dash.humidity],
        ['Wind Speed', `${dash.windSpd} km/h`],
        ['Condition', dash.wxDesc],
        ['24h Rainfall', `${dash.rain24h.toFixed(1)} mm`],
      ],
    },
    {
      id: 'rainfall-report',
      title: 'District Rainfall Report',
      desc: `Actual vs normal rainfall statistics`,
      date: new Date().toLocaleDateString('en-IN'),
      type: 'Rainfall',
      severity: dash.rain24h > 64 ? 'danger' : 'success',
      rows: [
        ['District', location.label],
        ['Daily Actual', `${dash.dailyActual.toFixed(1)} mm`],
        ['Daily Normal', `${dash.dailyNormal.toFixed(1)} mm`],
        ['Daily Departure', `${dash.dailyDep.toFixed(1)}%`],
        ['Weekly Actual', `${dash.weeklyActual.toFixed(1)} mm`],
        ['Weekly Departure', `${dash.weeklyDep.toFixed(1)}%`],
        ['Category', dash.dailyCategory],
      ],
    },
    {
      id: 'flood-alert',
      title: 'Flood Alert Report',
      desc: `Active events and nowcast status`,
      date: new Date().toLocaleDateString('en-IN'),
      type: 'Alert',
      severity: dash.alertSeverity,
      rows: [
        ['Alert Level', dash.alertLabel],
        ['Active Events', String(dash.activeEvents)],
        ['Nowcast Station', dash.nowcastStation],
        ['Nowcast Message', dash.nowcastMsg || 'No active message'],
        ['Risk Trend', dash.trendLabel],
      ],
    },
    {
      id: 'prediction-report',
      title: '5-Day Risk Prediction Report',
      desc: `Basin QPF flood risk forecast`,
      date: new Date().toLocaleDateString('en-IN'),
      type: 'Prediction',
      severity: dash.trendUp ? 'danger' : 'success',
      rows: dash.predictions.map((p, i) => [`${p.day}`, `${p.label} (${p.pct}%) — QPF: ${p.qpfRange} mm`]),
    },
  ];
}

function downloadReport(report) {
  const lines = [
    `FloodGuard — ${report.title}`,
    `Generated: ${new Date().toLocaleString('en-IN')}`,
    '─'.repeat(50),
    ...report.rows.map(([k, v]) => `${k.padEnd(24)} ${v}`),
    '─'.repeat(50),
    'Source: IMD Mock API · FloodGuard Platform',
  ];
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `${report.id}-${new Date().toISOString().slice(0,10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

const FILTER_TYPES = ['All','Weather','Rainfall','Alert','Prediction'];

export default function Reports({ locationKey, apiData }) {
  const [filter, setFilter] = useState('All');
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, location);
  const allReports = buildReports(dash, location);
  const visible = filter === 'All' ? allReports : allReports.filter(r => r.type === filter);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><FileText size={22} /> Reports</h1>
        <p className={styles.subtitle}>Auto-generated reports from live IMD data for {location.label}</p>
      </div>

      <div className={styles.filterRow}>
        <Filter size={15} style={{ color: 'var(--text-secondary)' }} />
        {FILTER_TYPES.map(f => (
          <button key={f} className={`${styles.filterBtn} ${filter === f ? styles.active : ''}`} onClick={() => setFilter(f)}>{f}</button>
        ))}
      </div>

      {!dash ? (
        <div className={styles.noData}>Connect to the IMD server to generate reports.</div>
      ) : (
        <div className={styles.reportGrid}>
          {visible.map(report => (
            <div key={report.id} className={styles.reportCard}>
              <div className={styles.cardTop}>
                <div>
                  <span className={`${styles.typeBadge} ${styles[report.severity]}`}>{report.type}</span>
                  <h3 className={styles.cardTitle}>{report.title}</h3>
                  <p className={styles.cardDesc}>{report.desc}</p>
                  <p className={styles.cardDate}>Generated: {report.date}</p>
                </div>
              </div>
              <div className={styles.dataPreview}>
                {report.rows.slice(0, 4).map(([k, v]) => (
                  <div key={k} className={styles.previewRow}>
                    <span className={styles.previewKey}>{k}</span>
                    <span className={styles.previewVal}>{v}</span>
                  </div>
                ))}
                {report.rows.length > 4 && <p className={styles.more}>+{report.rows.length - 4} more fields</p>}
              </div>
              <button className={styles.downloadBtn} onClick={() => downloadReport(report)}>
                <Download size={14} /> Download .txt
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
