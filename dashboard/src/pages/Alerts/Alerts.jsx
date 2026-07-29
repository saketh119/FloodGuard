import styles from './Alerts.module.css';
import { deriveDashboardData, LOCATIONS, COLOR_SEVERITY } from '../../data/locations';
import { Bell, Info } from 'lucide-react';

const COLOR_LABEL = { 1:'Green', 2:'Yellow', 3:'Orange', 4:'Red' };
const WARNING_CODE_FULL = {
  1:'No Warning', 2:'Heavy Rain', 3:'Very Heavy Rain', 4:'Thunderstorm & Lightning',
  5:'Strong Wind', 6:'Cold Wave', 7:'Dense Fog', 8:'Frost', 9:'Heat Wave',
  10:'Dust Storm', 11:'Snow', 12:'Hailstorm', 13:'Hot & Humid',
};
const DAY_LABELS = ['Today','Tomorrow','Day 3','Day 4','Day 5'];

export default function Alerts({ locationKey, apiData, loading, error }) {
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, location);

  const dayColors  = dash?.dayColors  ?? [1,1,1,1,1];
  const dayCodes   = dash?.dayCodes   ?? [[1],[1],[1],[1],[1]];
  const warn       = dash?.warn       ?? {};

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><Bell size={22} /> Alerts</h1>
        <p className={styles.subtitle}>5-day IMD district warnings for {location.label}, {location.state}</p>
      </div>

      {/* Nowcast warning banner */}
      {dash?.alertColor >= 3 && (
        <div className={`${styles.alertBanner} ${styles[dash.alertSeverity]}`}>
          <Bell size={18} />
          <div>
            <strong>Active Alert: {dash.alertLabel} ({COLOR_LABEL[dash.alertColor]})</strong>
            <p>{dash.nowcastMsg || `Significant weather activity detected in ${location.label}.`}</p>
          </div>
        </div>
      )}

      {/* 5-day warning calendar */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>District Warning Calendar</h2>
        <p className={styles.sectionSub}>Issued by IMD for {warn.District ?? location.label} · {warn.Date ?? new Date().toLocaleDateString('en-IN')}</p>

        {loading && !dash ? (
          <div className={styles.skeletonGrid}>
            {[0,1,2,3,4].map(i => <div key={i} className={styles.skeleton} />)}
          </div>
        ) : (
          <div className={styles.calendarGrid}>
            {[0,1,2,3,4].map(d => {
              const col = dayColors[d] ?? 1;
              const sev = COLOR_SEVERITY[col] ?? 'success';
              const codes = dayCodes[d] ?? [1];
              return (
                <div key={d} className={`${styles.dayCard} ${styles[sev]}`}>
                  <div className={styles.dayLabel}>{DAY_LABELS[d]}</div>
                  <div className={`${styles.colorDot} ${styles[`dot_${sev}`]}`} />
                  <div className={styles.colorName}>{COLOR_LABEL[col]} Alert</div>
                  <ul className={styles.codeList}>
                    {codes.filter(c => c > 1).map(c => (
                      <li key={c}>{WARNING_CODE_FULL[c] ?? `Warning ${c}`}</li>
                    ))}
                    {codes.every(c => c <= 1) && <li className={styles.noWarn}>No active warnings</li>}
                  </ul>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Station nowcast detail */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Current Nowcast Detail</h2>
        <div className={styles.nowcastDetail}>
          <div className={styles.ndRow}>
            <span className={styles.ndLabel}>Station</span>
            <span className={styles.ndVal}>{dash?.nowcastStation ?? '—'}</span>
          </div>
          <div className={styles.ndRow}>
            <span className={styles.ndLabel}>Alert Color</span>
            <span className={`${styles.ndVal} ${styles[dash?.alertSeverity ?? 'success']}`}>
              {COLOR_LABEL[dash?.alertColor ?? 1]} ({dash?.alertLabel ?? 'Low'})
            </span>
          </div>
          <div className={styles.ndRow}>
            <span className={styles.ndLabel}>Date</span>
            <span className={styles.ndVal}>{dash?.warn?.Date ?? new Date().toLocaleDateString('en-IN')}</span>
          </div>
          <div className={styles.ndRow}>
            <span className={styles.ndLabel}>Valid Until</span>
            <span className={styles.ndVal}>{dash?.warn?.Vupto ?? '—'}</span>
          </div>
          <div className={styles.ndRow}>
            <span className={styles.ndLabel}>Message</span>
            <span className={styles.ndVal}>{dash?.nowcastMsg || 'No active nowcast warning.'}</span>
          </div>
        </div>
      </section>

      <div className={styles.footer}>
        <Info size={14} />
        <span>Warning colors: Green = No warning, Yellow = Watch, Orange = Alert, Red = Warning (highest severity)</span>
      </div>
    </div>
  );
}
