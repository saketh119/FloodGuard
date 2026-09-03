'use client';

import { useFloodGuard } from '@/context/FloodGuardContext';
import styles from './WeatherRainfall.module.css';
import { WX_CODE_MAP } from '@/lib/derive';
import { CloudRain, Wind, Thermometer, Droplets, Gauge, Eye } from 'lucide-react';

const DEPARTURE_LABEL = { E:'Excess', N:'Normal', D:'Deficient', LD:'Large Deficient', LE:'Large Excess', NR:'No Rain' };

function StatTile({ icon: Icon, label, value, sub, color }) {
  return (
    <div className={styles.tile}>
      <div className={styles.tileIcon} style={{ color: color ?? 'var(--brand)' }}><Icon size={22} /></div>
      <div className={styles.tileBody}>
        <div className={styles.tileLabel}>{label}</div>
        <div className={styles.tileValue} style={{ color: color ?? 'var(--text-primary)' }}>{value}</div>
        {sub && <div className={styles.tileSub}>{sub}</div>}
      </div>
    </div>
  );
}

export default function WeatherRainfall() {
  const { dash, loading, location, payload } = useFloodGuard();

  const wx  = payload?.observations?.current_wx?.raw ?? {};
  const aws = payload?.observations?.aws?.raw ?? {};
  const rf  = payload?.observations?.rainfall?.raw ?? {};
  const ow  = payload?.observations?.ow_current?.raw ?? {};
  const owMain = ow.main ?? {};

  // OpenWeather is a real reading at real coordinates; the IMD values behind it are
  // still served by the mock. Prefer live wherever we have it, and say which is which.
  const isLive = Boolean(dash?.isLive);
  const round1 = (v) => (v == null || v === '—' ? '—' : Math.round(v * 10) / 10);

  const temp      = round1(owMain.temp ?? aws['CURR_TEMP'] ?? wx['Temperature']);
  const maxTemp   = round1(owMain.temp_max ?? aws['MAX_TEMP']);
  const minTemp   = round1(owMain.temp_min ?? aws['MIN_TEMP']);
  const humidity  = owMain.humidity ?? aws['RH'] ?? wx['Humidity'] ?? '—';
  const windSpd   = dash?.liveWind ?? aws['WIND_SPEED'] ?? wx['Wind Speed'] ?? '—';
  const windDir   = ow.wind?.deg ?? aws['WIND_DIRECTION'] ?? wx['Wind Direction'] ?? '—';
  const mslp      = owMain.pressure ?? aws['MSLP'] ?? wx['M.S.L.P'] ?? '—';
  const wxCode    = String(wx['Weather Code'] ?? '00').padStart(2,'0');
  const wxDesc    = dash?.liveConditions
    ? dash.liveConditions.replace(/^\w/, c => c.toUpperCase())
    : (WX_CODE_MAP[wxCode] ?? 'Partly Cloudy');
  const stationName = dash?.liveStation ?? aws['STATION'] ?? wx['Station'] ?? location.district;
  const feel      = round1(owMain.feels_like ?? aws['Feel Like']);

  const rainfallRows = [
    { period: 'Daily',    actual: rf['Daily Actual'],    normal: rf['Daily Normal'],    dep: rf['Daily Departure Per'],    cat: rf['Daily Category'] },
    { period: 'Weekly',   actual: rf['Weekly Actual'],   normal: rf['Weekly Normal'],   dep: rf['Weekly Departure Per'],   cat: rf['Weekly Category'] },
    { period: 'Monthly',  actual: rf['Monthly Actual'],  normal: rf['Monthly Normal'],  dep: rf['Monthly Departure Per'],  cat: rf['Monthly Category'] },
    { period: 'Cumulative',actual: rf['Cumulative Actual'],normal:rf['Cumulative Normal'],dep:rf['Cumulative Departure Per'],cat:rf['Cumulative Category'] },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><CloudRain size={22} /> Weather & Rainfall</h1>
        <p className={styles.subtitle}>Live observations for {stationName} · {location.state}</p>
      </div>

      {/* Current Conditions */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Current Conditions</h2>
        <div className={styles.tilesGrid}>
          <StatTile icon={Thermometer} label="Temperature" value={`${temp}°C`} sub={`Feels like ${feel}°C`} color="var(--danger)" />
          <StatTile icon={Thermometer} label="Max / Min" value={`${maxTemp}° / ${minTemp}°C`} sub="Today's range" />
          <StatTile icon={Droplets} label="Humidity" value={`${humidity}%`} sub="Relative humidity" color="var(--brand)" />
          <StatTile icon={Wind} label="Wind Speed" value={`${windSpd} km/h`} sub={`Direction: ${windDir}°`} color="var(--success)" />
          <StatTile icon={Gauge} label="Pressure" value={`${mslp} hPa`} sub="Mean sea level" />
          <StatTile icon={Eye} label="Condition" value={wxDesc} sub={`Code: ${wxCode}`} color="var(--warning)" />
        </div>
      </section>

      {/* Rainfall table */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Rainfall Statistics</h2>
        <p className={styles.sectionSub}>District: {rf['District'] ?? location.district} · Date: {rf['Date'] ?? new Date().toLocaleDateString('en-IN')}</p>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Period</th>
                <th>Actual (mm)</th>
                <th>Normal (mm)</th>
                <th>Departure %</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {rainfallRows.map(row => {
                const dep = parseFloat(row.dep ?? 0);
                const depColor = dep > 20 ? 'var(--danger)' : dep < -20 ? 'var(--brand)' : 'var(--success)';
                return (
                  <tr key={row.period}>
                    <td className={styles.tdPeriod}>{row.period}</td>
                    <td>{row.actual != null ? parseFloat(row.actual).toFixed(1) : '—'}</td>
                    <td>{row.normal != null ? parseFloat(row.normal).toFixed(1) : '—'}</td>
                    <td style={{ color: depColor, fontWeight: 700 }}>{dep >= 0 ? '+' : ''}{dep.toFixed(1)}%</td>
                    <td><span className={styles.catBadge}>{DEPARTURE_LABEL[row.cat] ?? row.cat ?? '—'}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* AWS station info */}
      {aws['CALL_SIGN'] && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>AWS Station Details</h2>
          <div className={styles.awsCard}>
            <div className={styles.awsRow}><span>Station Name</span><span>{aws['STATION']}</span></div>
            <div className={styles.awsRow}><span>Call Sign</span><span>{aws['CALL_SIGN']}</span></div>
            <div className={styles.awsRow}><span>District</span><span>{aws['DISTRICT']}</span></div>
            <div className={styles.awsRow}><span>State</span><span>{aws['STATE']}</span></div>
            <div className={styles.awsRow}><span>Coordinates</span><span>{aws['Latitude']}° N, {aws['Longitude']}° E</span></div>
            <div className={styles.awsRow}><span>Observation Time</span><span>{aws['TIME']} · {aws['DATE']}</span></div>
          </div>
        </section>
      )}
    </div>
  );
}
