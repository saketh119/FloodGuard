'use client';

import { useFloodGuard } from '@/context/FloodGuardContext';
import styles from './RiversReservoirs.module.css';
import { Droplets, Waves, Info } from 'lucide-react';

function LevelBar({ label, value, max, unit, severity }) {
  const pct = Math.min(Math.round((parseFloat(value || 0) / max) * 100), 100);
  return (
    <div className={styles.levelRow}>
      <div className={styles.levelLabel}>{label}</div>
      <div className={styles.levelTrack}>
        <div className={`${styles.levelFill} ${styles[`fill_${severity}`]}`} style={{ width: `${pct}%` }} />
      </div>
      <div className={styles.levelMeta}>
        <span className={styles.levelVal}>{value ?? '—'} {unit}</span>
        <span className={styles.levelPct}>{pct}%</span>
      </div>
    </div>
  );
}

export default function RiversReservoirs() {
  const { dash, loading, location, payload } = useFloodGuard();
  const aws = (payload?.observations?.aws ? [payload.observations.aws.raw] : []);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><Waves size={22} /> Rivers & Reservoirs</h1>
        <p className={styles.subtitle}>AWS station readings and rainfall-derived level estimates for {location.district}</p>
      </div>

      {/* River status card */}
      <div className={styles.riverCard}>
        <div className={`${styles.riverStatus} ${styles[dash?.riverSeverity ?? 'success']}`}>
          <Droplets size={32} />
          <div>
            <div className={styles.riverName}>{(location.basin ? `${location.basin} basin` : 'river basin')}</div>
            <div className={styles.riverLevel}>{dash?.riverLevelValue ?? '—'}</div>
            <div className={styles.riverStatus2}>{dash?.riverLevelProxy ?? '—'}</div>
          </div>
        </div>
        <div className={styles.riverNote}>
          <Info size={13} />
          <span>River depth is rainfall-derived (24h actuals) — CWC gauge integration pending. Values are estimates.</span>
        </div>
      </div>

      {/* Level indicators from rainfall data */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Rainfall Level Indicators</h2>
        <div className={styles.levelPanel}>
          <LevelBar label="Daily Rainfall" value={dash?.dailyActual} max={200} unit="mm" severity={dash?.dailyActual > 64 ? 'danger' : dash?.dailyActual > 15 ? 'warning' : 'success'} />
          <LevelBar label="Weekly Rainfall" value={dash?.weeklyActual} max={500} unit="mm" severity={dash?.weeklyActual > 200 ? 'danger' : dash?.weeklyActual > 75 ? 'warning' : 'success'} />
          <LevelBar label="Monthly Accumulated" value={dash?.monthlyActual} max={1000} unit="mm" severity={dash?.monthlyActual > 400 ? 'danger' : 'success'} />
          <LevelBar label="Est. Reservoir Storage" value={dash ? Math.round(dash.reservoirRatio * 60) : 0} max={100} unit="%" severity={dash?.reservoirSeverity ?? 'success'} />
        </div>
      </section>

      {/* AWS Station cards */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>AWS Stations — Live Readings</h2>
        <p className={styles.sectionSub}>Source: IMD AWS network · State ID {location.awsStateId}</p>
        {loading && !payload ? (
          <div className={styles.skeletonGrid}>
            {[0,1,2].map(i => <div key={i} className={styles.skeleton} />)}
          </div>
        ) : aws.length === 0 ? (
          <p className={styles.noData}>No AWS station data available.</p>
        ) : (
          <div className={styles.stationGrid}>
            {aws.slice(0, 9).map((s, i) => (
              <div key={i} className={styles.stationCard}>
                <div className={styles.stationName}>{s.STATION ?? `Station ${i+1}`}</div>
                <div className={styles.stationDist}>{s.DISTRICT} · {s.STATE}</div>
                <div className={styles.stationMetrics}>
                  <div className={styles.stMetric}>
                    <span className={styles.stVal}>{s.CURR_TEMP ?? '—'}°C</span>
                    <span className={styles.stLbl}>Temp</span>
                  </div>
                  <div className={styles.stMetric}>
                    <span className={styles.stVal}>{s.RH ?? '—'}%</span>
                    <span className={styles.stLbl}>Humidity</span>
                  </div>
                  <div className={styles.stMetric}>
                    <span className={styles.stVal}>{s.WIND_SPEED ?? '—'}</span>
                    <span className={styles.stLbl}>Wind km/h</span>
                  </div>
                  <div className={styles.stMetric}>
                    <span className={styles.stVal}>{s.MSLP ?? '—'}</span>
                    <span className={styles.stLbl}>hPa</span>
                  </div>
                </div>
                <div className={styles.stTime}>{s.TIME} · {s.DATE}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
