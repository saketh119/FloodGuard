import styles from './Predictions.module.css';
import { LOCATIONS, deriveDashboardData } from '../../data/locations';
import PredictionRow from '../../components/PredictionRow/PredictionRow';
import { LineChart, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function Predictions({ locationKey, apiData, loading }) {
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, location);
  const predictions = dash?.predictions ?? [];

  // 7-day forecast from city forecast endpoint
  const forecast = apiData?.forecast?.data ?? [];

  const TrendIcon = dash?.trendUp ? TrendingUp : dash?.trendDown ? TrendingDown : Minus;

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><LineChart size={22} /> Flood Risk Predictions</h1>
        <p className={styles.subtitle}>Basin QPF + 7-day city forecast for {location.label}, {location.state}</p>
      </div>

      {/* Trend summary */}
      <div className={styles.trendRow}>
        <div className={`${styles.trendCard} ${styles[dash?.trendSeverity ?? 'success']}`}>
          <TrendIcon size={28} />
          <div>
            <div className={styles.trendLabel}>{dash?.trendLabel ?? 'Stable'}</div>
            <div className={styles.trendSub}>Risk trend over next 48 hours</div>
          </div>
        </div>
        <div className={styles.trendCard2}>
          <span className={styles.trendStat}>{dash?.rain24h?.toFixed(1) ?? '—'} mm</span>
          <span className={styles.trendStatLbl}>24h Actual Rainfall</span>
        </div>
        <div className={styles.trendCard2}>
          <span className={styles.trendStat}>{dash?.weeklyActual?.toFixed(1) ?? '—'} mm</span>
          <span className={styles.trendStatLbl}>7-Day Accumulated</span>
        </div>
        <div className={styles.trendCard2}>
          <span className={styles.trendStat}>{dash?.weeklyDep?.toFixed(0) ?? '—'}%</span>
          <span className={styles.trendStatLbl}>Departure from Normal</span>
        </div>
      </div>

      {/* QPF Prediction bars */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Basin QPF — Flood Risk Score</h2>
        <p className={styles.sectionSub}>Quantitative Precipitation Forecast from IMD basin data · {location.riverName} basin</p>
        <div className={styles.qpfPanel}>
          {loading && !dash ? (
            [0,1,2,3,4].map(i => <div key={i} className={styles.skeleton} style={{height:48}} />)
          ) : predictions.length === 0 ? (
            <p className={styles.noData}>No QPF data available for this basin.</p>
          ) : (
            predictions.map((p, i) => (
              <div key={i}>
                <PredictionRow {...p} />
                {p.qpfRange && (
                  <div className={styles.qpfRange}>QPF: {p.qpfRange} mm · {p.basin} / {p.subBasin}</div>
                )}
              </div>
            ))
          )}
        </div>
      </section>

      {/* 7-day city forecast table */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>7-Day City Weather Forecast</h2>
        <p className={styles.sectionSub}>Source: IMD city forecast API · Station {location.stationId}</p>

        {loading && !apiData ? (
          <div className={styles.skeleton} style={{height: 200}} />
        ) : forecast.length === 0 ? (
          <p className={styles.noData}>No 7-day forecast available.</p>
        ) : (
          <div className={styles.forecastGrid}>
            {forecast.slice(0, 1).flatMap(item =>
              [1,2,3,4,5,6,7].map(d => ({
                day: d === 1 ? 'Today' : d === 2 ? 'Tomorrow' : `Day ${d}`,
                maxTemp: d === 1 ? item['Todays_Forecast_Max_Temp'] : item[`Day_${d}_Max_Temp`],
                minTemp: d === 1 ? item['Todays_Forecast_Min_temp'] : item[`Day_${d}_Min_Temp`],
                forecast: d === 1 ? item['Todays_Forecast'] : item[`Day_${d}_Forecast`],
              }))
            ).map((f, i) => (
              <div key={i} className={styles.forecastCard}>
                <div className={styles.fcDay}>{f.day}</div>
                <div className={styles.fcTemps}>
                  <span className={styles.fcMax}>{f.maxTemp ?? '—'}°C</span>
                  <span className={styles.fcMin}>{f.minTemp ?? '—'}°C</span>
                </div>
                <div className={styles.fcDesc}>{f.forecast ?? 'N/A'}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className={styles.footer}>
        <Info size={14} />
        <span>QPF scores are calculated from IMD basin precipitation forecasts. CWC hydrograph integration pending.</span>
      </div>
    </div>
  );
}
