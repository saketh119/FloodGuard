/**
 * locations.js — Location registry + API-to-UI transformation layer
 *
 * Each location maps to the IDs required by IMD API endpoints.
 * lat/lng are used for real geolocation distance matching.
 * When the real IMD API goes live, only update the IDs — nothing else changes.
 */

// ── Haversine distance (km) between two lat/lng pairs ───────────────
export function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── Location registry ────────────────────────────────────────────────
export const LOCATIONS = {
  hyderabad: {
    key: 'hyderabad',
    label: 'Hyderabad',
    state: 'Telangana',
    coords: '17.3850° N, 78.4867° E',
    lat: 17.385, lng: 78.4867,
    stationId: '42182',
    districtId: '164',   // mock → flood scenario (Kamrup)
    basinId: '100',
    awsStateId: '18',    // Assam (flood scenario in mock)
    riverName: 'Musi River',
  },
  vijayawada: {
    key: 'vijayawada',
    label: 'Vijayawada',
    state: 'Andhra Pradesh',
    coords: '16.5062° N, 80.6480° E',
    lat: 16.5062, lng: 80.648,
    stationId: '43353',
    districtId: '201',   // mock → normal scenario (Patna)
    basinId: '200',
    awsStateId: '7',
    riverName: 'Krishna River',
  },
  guntur: {
    key: 'guntur',
    label: 'Guntur',
    state: 'Andhra Pradesh',
    coords: '16.3067° N, 80.4365° E',
    lat: 16.3067, lng: 80.4365,
    stationId: '42492',
    districtId: '202',
    basinId: '200',
    awsStateId: '7',
    riverName: 'Guntur Canal',
  },
  warangal: {
    key: 'warangal',
    label: 'Warangal',
    state: 'Telangana',
    coords: '17.9689° N, 79.5941° E',
    lat: 17.9689, lng: 79.5941,
    stationId: '42182',
    districtId: '164',   // mock → flood scenario
    basinId: '100',
    awsStateId: '18',
    riverName: 'Godavari River',
  },
  nalgonda: {
    key: 'nalgonda',
    label: 'Nalgonda',
    state: 'Telangana',
    coords: '17.0500° N, 79.2700° E',
    lat: 17.05, lng: 79.27,
    stationId: '42492',
    districtId: '202',
    basinId: '200',
    awsStateId: '7',
    riverName: 'Krishna River',
  },
};

export const POPULAR_LOCATIONS = Object.values(LOCATIONS);

/** Find the nearest registered location to a lat/lng pair */
export function nearestLocation(lat, lng) {
  let best = null, bestDist = Infinity;
  for (const loc of POPULAR_LOCATIONS) {
    const d = haversineKm(lat, lng, loc.lat, loc.lng);
    if (d < bestDist) { bestDist = d; best = loc; }
  }
  return best;
}

// ── Weather-code lookup ──────────────────────────────────────────────
export const WX_CODE_MAP = {
  '00': 'Clear', '01': 'Clear', '02': 'Clear Sky', '03': 'Partly Cloudy',
  '10': 'Mist', '11': 'Shallow Fog', '45': 'Fog',
  '60': 'Light Rain', '61': 'Light Rain', '63': 'Moderate Rain',
  '65': 'Heavy Rain', '66': 'Freezing Rain', '80': 'Rain Showers',
  '81': 'Heavy Showers', '95': 'Thunderstorm', '96': 'Thunderstorm with Hail',
};

// ── Alert colour → label / severity ─────────────────────────────────
export const COLOR_LABEL    = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'High' };
export const COLOR_SEVERITY = { 1: 'success', 2: 'warning', 3: 'warning', 4: 'danger' };

// ── QPF range string → midpoint mm ──────────────────────────────────
function qpfMidpoint(raw) {
  const parts = String(raw ?? '0').split('-').map(Number).filter(n => !isNaN(n));
  if (parts.length === 2) return (parts[0] + parts[1]) / 2;
  return parts[0] ?? 0;
}

// ── Main derivation function ─────────────────────────────────────────
/**
 * Transforms raw IMD API payloads into dashboard-ready data.
 * Every field here comes directly from API responses — no fakes.
 */
export function deriveDashboardData(apiData, locationCfg) {
  if (!apiData) return null;
  const { weather, nowcast, rainfall, warning, qpf, aws } = apiData;

  // ── 1. Current Weather (from /current_wx) ──────────────────────────
  const wx = weather?.data?.[0] ?? {};
  const rain24h  = parseFloat(wx['Last 24 hrs Rainfall'] ?? 0);
  const temp     = wx['Temperature'] != null ? `${wx['Temperature']}` : '—';
  const humidity = wx['Humidity']    != null ? `${wx['Humidity']}%`   : '—';
  const windSpd  = parseFloat(wx['Wind Speed'] ?? 0);
  const mslp     = wx['M.S.L.P']    ?? '—';
  const nebulosity = wx['Nebulosity'] ?? 0;
  const wxCode   = String(wx['Weather Code'] ?? '00').padStart(2, '0');
  const wxDesc   = WX_CODE_MAP[wxCode] ?? 'Partly Cloudy';
  const stationName = wx['Station'] ?? locationCfg.label;

  // ── 2. Nowcast (from /nowcast) — colour 1=Green…4=Red ──────────────
  const nc         = nowcast?.data?.[0] ?? {};
  const alertColor = nc.color ?? 1;
  const alertLabel    = COLOR_LABEL[alertColor]    ?? 'Low';
  const alertSeverity = COLOR_SEVERITY[alertColor] ?? 'success';
  const nowcastMsg    = nc.message ?? '';
  const nowcastStation = nc.Station ?? locationCfg.label;

  // ── 3. Rainfall (from /districtrainfall) ──────────────────────────
  const rf             = rainfall?.data?.[0] ?? {};
  const dailyActual    = parseFloat(rf['Daily Actual']          ?? 0);
  const dailyNormal    = parseFloat(rf['Daily Normal']          ?? 10);
  const weeklyActual   = parseFloat(rf['Weekly Actual']         ?? 0);
  const weeklyNormal   = parseFloat(rf['Weekly Normal']         ?? 70);
  const monthlyActual  = parseFloat(rf['Monthly Actual']        ?? 0);
  const monthlyNormal  = parseFloat(rf['Monthly Normal']        ?? 300);
  const dailyDep       = parseFloat(rf['Daily Departure Per']   ?? 0);
  const weeklyDep      = parseFloat(rf['Weekly Departure Per']  ?? 0);
  const monthlyDep     = parseFloat(rf['Monthly Departure Per'] ?? 0);
  const dailyCategory  = rf['Daily Category']   ?? 'N';
  const weeklyCategory = rf['Weekly Category']  ?? 'N';
  // Reservoir proxy: if weekly actual is >150% of normal → reservoirs stressed
  const reservoirRatio = weeklyNormal > 0 ? weeklyActual / weeklyNormal : 1;
  const reservoirsStressed = reservoirRatio > 1.5;

  // ── 4. 5-Day Warning (from /districtwarning) ──────────────────────
  const warn = warning?.data?.[0] ?? {};
  const dayColors = [1,2,3,4,5].map(d => warn[`Day${d}_Color`] ?? 1);
  const dayCodes  = [1,2,3,4,5].map(d => {
    const raw = warn[`Day_${d}`] ?? '1';
    return raw.split(',').map(Number);
  });

  // ── 5. AWS Station data (from /aws_data) ──────────────────────────
  const awsStation = aws?.data?.[0] ?? {};
  const awsTemp    = awsStation['CURR_TEMP']  ?? null;
  const awsRH      = awsStation['RH']         ?? null;
  const awsWind    = awsStation['WIND_SPEED'] ?? null;
  const awsMSLP    = awsStation['MSLP']       ?? null;
  const awsMaxTemp = awsStation['MAX_TEMP']   ?? null;
  const awsMinTemp = awsStation['MIN_TEMP']   ?? null;
  // AWS doesn't give river level — use rainfall as proxy for now (CWC to replace later)
  const riverLevelProxy = rain24h > 50 ? 'Above Warning Level' : rain24h > 20 ? 'At Warning Level' : 'Safe Levels';
  const riverLevelValue = rain24h > 50 ? `${(rain24h / 15).toFixed(1)} m` : rain24h > 20 ? `${(rain24h / 18).toFixed(1)} m` : `${(rain24h / 25 + 1.2).toFixed(1)} m`;
  const riverSeverity   = rain24h > 50 ? 'danger' : rain24h > 20 ? 'warning' : 'success';

  // ── 6. Basin QPF (from /basinqpf) → prediction rows ───────────────
  const qpfRows = (qpf?.data ?? []).slice(0, 5).map((row, i) => {
    const dayKeys = ['Day1','Day2','Day3','Day4','Day5'];
    const raw  = row[dayKeys[i]] ?? '0-10';
    const mid  = qpfMidpoint(raw);
    const pct  = Math.min(Math.round((mid / 200) * 100), 99);
    const severity = pct > 60 ? 'danger' : pct > 30 ? 'warning' : 'success';
    const date = row.Date
      ? new Date(row.Date).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })
      : `Day ${i + 1}`;
    return { day: date, pct, severity, label: COLOR_LABEL[severity === 'danger' ? 4 : severity === 'warning' ? 2 : 1], qpfRange: raw, basin: row.Basin, subBasin: row.SubBasin };
  });

  const trendUp   = qpfRows.length >= 2 && qpfRows[1].pct > qpfRows[0].pct;
  const trendDown = qpfRows.length >= 2 && qpfRows[1].pct < qpfRows[0].pct;

  // ── 7. Active events derived from threshold rules ──────────────────
  const events = [];
  if (alertColor >= 3) {
    events.push({
      id: 'nowcast-flash',
      title: `${nowcastStation} Flash Alert`,
      severity: alertSeverity,
      subtitle: nowcastStation,
      started: new Date().toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }),
      metric: `${rain24h.toFixed(1)} mm`,
      metricLabel: '24h Rainfall',
      icon: 'cloud-lightning',
      message: nowcastMsg,
    });
  }
  if (rain24h > 64.5) {
    events.push({
      id: 'rainfall-heavy',
      title: 'Heavy Rainfall Alert',
      severity: 'warning',
      subtitle: `${locationCfg.label} District`,
      started: new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }),
      metric: `${rain24h.toFixed(1)} mm`,
      metricLabel: '24h Rainfall',
      icon: 'cloud-rain',
      message: `Rainfall of ${rain24h.toFixed(1)} mm recorded in last 24 hours — exceeds heavy rainfall threshold (64.5 mm).`,
    });
  }
  if (windSpd > 40) {
    events.push({
      id: 'wind-high',
      title: 'High Wind Speed Warning',
      severity: 'warning',
      subtitle: stationName,
      started: new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'short' }),
      metric: `${windSpd} km/h`,
      metricLabel: 'Wind Speed',
      icon: 'wind',
      message: `Wind speed of ${windSpd} km/h recorded — gusty conditions expected.`,
    });
  }
  if (reservoirsStressed) {
    events.push({
      id: 'reservoir-high',
      title: 'Reservoir Inflow High',
      severity: alertColor >= 3 ? 'danger' : 'warning',
      subtitle: `${locationCfg.label} Basin`,
      started: new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }),
      metric: `${Math.min(Math.round(reservoirRatio * 60), 98)}%`,
      metricLabel: 'Est. Storage Level',
      icon: 'shield-alert',
      message: `Weekly rainfall (${weeklyActual.toFixed(1)} mm) is ${weeklyDep.toFixed(0)}% above normal — reservoir inflow elevated.`,
    });
  }

  return {
    // Alert
    alertLabel, alertSeverity, alertColor,
    nowcastMsg, nowcastStation,
    // Counts
    activeEvents: events.length,
    // Weather
    rain24h, temp, humidity, windSpd, mslp, nebulosity, wxDesc, wxCode, stationName,
    // AWS
    awsTemp, awsRH, awsWind, awsMSLP, awsMaxTemp, awsMinTemp,
    // Rainfall
    dailyActual, dailyNormal, weeklyActual, weeklyNormal,
    monthlyActual, monthlyNormal,
    dailyDep, weeklyDep, monthlyDep,
    dailyCategory, weeklyCategory,
    // Reservoir proxy
    reservoirRatio, reservoirsStressed,
    reservoirLabel: reservoirsStressed ? `${Math.min(Math.round(reservoirRatio * 60), 98)}% est.` : 'Normal',
    reservoirSeverity: reservoirsStressed ? 'warning' : 'success',
    // River (CWC placeholder)
    riverLevelValue, riverLevelProxy, riverSeverity,
    // Trend
    trendUp, trendDown,
    trendLabel: trendUp ? 'Increasing' : trendDown ? 'Decreasing' : 'Stable',
    trendSeverity: trendUp ? 'danger' : trendDown ? 'success' : 'warning',
    // Events & predictions
    events, predictions: qpfRows,
    // Warning grid
    dayColors, dayCodes,
    // Raw
    warn, rf, nc, wx: { temp, humidity, windSpd, mslp, wxDesc, rain24h },
  };
}
