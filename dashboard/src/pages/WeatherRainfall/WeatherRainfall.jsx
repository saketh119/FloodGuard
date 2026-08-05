import styles from './WeatherRainfall.module.css';
import { LOCATIONS, deriveDashboardData, WX_CODE_MAP } from '../../data/locations';
import { CloudRain, Wind, Thermometer, Droplets, Gauge, Eye } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';

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

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={styles.tooltip}>
      <div className={styles.ttLabel}>{label}</div>
      {payload.map(p => (
        <div key={p.name} className={styles.ttRow}>
          <span style={{ color: p.color }}>{p.name}</span>
          <span>{parseFloat(p.value).toFixed(1)} mm</span>
        </div>
      ))}
    </div>
  );
};

export default function WeatherRainfall({ locationKey, apiData, loading }) {
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, location);

  const wx  = apiData?.weather?.data?.[0] ?? {};
  const aws = apiData?.aws?.data?.[0] ?? {};
  const rf  = apiData?.rainfall?.data?.[0] ?? {};

  const temp      = aws['CURR_TEMP']    ?? wx['Temperature']      ?? '—';
  const maxTemp   = aws['MAX_TEMP']     ?? '—';
  const minTemp   = aws['MIN_TEMP']     ?? '—';
  const humidity  = aws['RH']           ?? wx['Humidity']          ?? '—';
  const windSpd   = aws['WIND_SPEED']   ?? wx['Wind Speed']        ?? '—';
  const windDir   = aws['WIND_DIRECTION'] ?? wx['Wind Direction']  ?? '—';
  const mslp      = aws['MSLP']         ?? wx['M.S.L.P']           ?? '—';
  const wxCode    = String(wx['Weather Code'] ?? '00').padStart(2,'0');
  const wxDesc    = WX_CODE_MAP[wxCode] ?? 'Partly Cloudy';
  const stationName = aws['STATION'] ?? wx['Station'] ?? location.label;
  const feel      = aws['Feel Like'] ?? '—';

  const rainfallRows = [
    { period: 'Daily',    actual: rf['Daily Actual'],    normal: rf['Daily Normal'],    dep: rf['Daily Departure Per'],    cat: rf['Daily Category'] },
    { period: 'Weekly',   actual: rf['Weekly Actual'],   normal: rf['Weekly Normal'],   dep: rf['Weekly Departure Per'],   cat: rf['Weekly Category'] },
    { period: 'Monthly',  actual: rf['Monthly Actual'],  normal: rf['Monthly Normal'],  dep: rf['Monthly Departure Per'],  cat: rf['Monthly Category'] },
    { period: 'Cumulative',actual: rf['Cumulative Actual'],normal:rf['Cumulative Normal'],dep:rf['Cumulative Departure Per'],cat:rf['Cumulative Category'] },
  ];

  // Chart data: actual vs normal rainfall for bar chart
  const chartData = rainfallRows.map(r => ({
    name: r.period,
    Actual: r.actual != null ? parseFloat(r.actual) : 0,
    Normal: r.normal != null ? parseFloat(r.normal) : 0,
  }));

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><CloudRain size={22} /> Weather &amp; Rainfall</h1>
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

      {/* Rainfall Bar Chart */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Actual vs Normal Rainfall</h2>
        <p className={styles.sectionSub}>District: {rf['District'] ?? location.label} · {rf['Date'] ?? new Date().toLocaleDateString('en-IN')}</p>
        <div className={styles.chartWrap}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} axisLine={{ stroke: 'var(--border)' }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} unit=" mm" />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
              <Bar dataKey="Actual" fill="#2563eb" radius={[6, 6, 0, 0]} />
              <Bar dataKey="Normal" fill="#94a3b8" radius={[6, 6, 0, 0]} />
              <ReferenceLine y={64.5} stroke="var(--danger)" strokeDasharray="5 3" label={{ value: 'Heavy Rain Threshold', position: 'insideTopRight', fill: 'var(--danger)', fontSize: 10 }} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Rainfall table */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Rainfall Statistics Table</h2>
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
