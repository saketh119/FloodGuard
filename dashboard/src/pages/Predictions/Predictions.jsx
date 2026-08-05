import styles from './Predictions.module.css';
import { LOCATIONS, deriveDashboardData } from '../../data/locations';
import PredictionRow from '../../components/PredictionRow/PredictionRow';
import { LineChart, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';

const RiskTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const val = payload[0]?.value ?? 0;
  const color = val > 60 ? 'var(--danger)' : val > 30 ? 'var(--warning)' : 'var(--success)';
  return (
    <div className={styles.tooltip}>
      <div className={styles.ttLabel}>{label}</div>
      <div className={styles.ttRow}>
        <span>Flood Risk</span>
        <span style={{ color, fontWeight: 700 }}>{val}%</span>
      </div>
    </div>
  );
};

export default function Predictions({ locationKey, apiData, loading }) {
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, location);
  const predictions = dash?.predictions ?? [];

  // 7-day forecast from city forecast endpoint
  const forecast = apiData?.forecast?.data ?? [];

  const TrendIcon = dash?.trendUp ? TrendingUp : dash?.trendDown ? TrendingDown : Minus;

  // Area chart data from QPF predictions
  const chartData = predictions.map(p => ({ name: p.day, Risk: p.pct }));

  // Color gradient stops based on risk
  const gradientId = 'riskGradient';

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

      {/* Risk Area Chart */}
      {chartData.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>5-Day Flood Risk Trend</h2>
          <p className={styles.sectionSub}>Flood risk probability derived from IMD Basin QPF forecasts</p>
          <div className={styles.chartWrap}>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData} margin={{ top: 12, right: 16, left: 0, bottom: 4 }}>
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} axisLine={{ stroke: 'var(--border)' }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} unit="%" />
                <Tooltip content={<RiskTooltip />} />
                <ReferenceLine y={60} stroke="var(--danger)" strokeDasharray="5 3" label={{ value: 'High Risk', position: 'insideTopRight', fill: 'var(--danger)', fontSize: 10 }} />
                <ReferenceLine y={30} stroke="var(--warning)" strokeDasharray="5 3" label={{ value: 'Medium Risk', position: 'insideTopRight', fill: 'var(--warning)', fontSize: 10 }} />
                <Area type="monotone" dataKey="Risk" stroke="#2563eb" strokeWidth={2.5} fill={`url(#${gradientId})`} dot={{ fill: '#2563eb', r: 4 }} activeDot={{ r: 6 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

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
