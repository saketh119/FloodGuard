/**
 * derive.js — shapes the backend's /dashboard aggregate for the UI.
 *
 * Note what is NOT here: threshold logic. The Vite version re-implemented IMD's
 * rainfall thresholds and alert rules in the browser, so the same rules lived in two
 * places and could disagree. Flood events, severity and risk now arrive already
 * decided by the backend's trigger and correlation engines; this file only formats.
 */

export const COLOR_LABEL = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'High' };
export const COLOR_SEVERITY = { 1: 'success', 2: 'warning', 3: 'warning', 4: 'danger' };
export const COLOR_NAME = { 1: 'Green', 2: 'Yellow', 3: 'Orange', 4: 'Red' };

export const WX_CODE_MAP = {
  '00': 'Clear', '01': 'Clear', '02': 'Clear Sky', '03': 'Partly Cloudy',
  '10': 'Mist', '11': 'Shallow Fog', '45': 'Fog',
  '60': 'Light Rain', '61': 'Light Rain', '63': 'Moderate Rain',
  '65': 'Heavy Rain', '66': 'Freezing Rain', '80': 'Rain Showers',
  '81': 'Heavy Showers', '95': 'Thunderstorm', '96': 'Thunderstorm with Hail',
};

export const WARNING_CODE_MAP = {
  1: 'No Warning', 2: 'Heavy Rain', 3: 'Very Heavy Rain', 4: 'Thunderstorm & Lightning',
  5: 'Strong Wind', 6: 'Cold Wave', 9: 'Heat Wave', 12: 'Hailstorm',
};

/** Backend severity vocabulary → the UI's colour tokens. */
export const SEVERITY_TONE = {
  low: 'success', moderate: 'warning', high: 'warning', severe: 'danger',
};

const num = (v, fallback = 0) => {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : fallback;
};

/** '50-100' → 75, '>200' → 200 */
function qpfMidpoint(band) {
  const parts = String(band ?? '0').replace(/[<>]/g, '').split('-').map(Number)
    .filter(n => !Number.isNaN(n));
  if (parts.length === 0) return 0;
  return parts.length === 2 ? (parts[0] + parts[1]) / 2 : parts[0];
}

/**
 * Rainfall in a day → a flood-risk percentage.
 *
 * Anchored on IMD's own daily rainfall classification (heavy 64.5, very heavy 115.6,
 * extremely heavy 204.5 mm) and interpolated between those points, so the number moves
 * continuously instead of jumping between buckets.
 */
const RISK_CURVE = [[0, 0], [15, 22], [64.5, 55], [115.6, 76], [204.5, 93], [300, 98]];

function riskFromRainfall(mm) {
  const v = Math.max(0, Number(mm) || 0);
  let pct = 98;
  for (let i = 1; i < RISK_CURVE.length; i += 1) {
    const [x0, y0] = RISK_CURVE[i - 1];
    const [x1, y1] = RISK_CURVE[i];
    if (v <= x1) {
      pct = Math.round(y0 + ((v - x0) / (x1 - x0)) * (y1 - y0));
      break;
    }
  }
  const severity = pct >= 55 ? 'danger' : pct >= 25 ? 'warning' : 'success';
  return {
    pct,
    severity,
    label: severity === 'danger' ? 'High' : severity === 'warning' ? 'Medium' : 'Low',
  };
}

const DAY_FMT = { weekday: 'short', day: 'numeric', month: 'short' };

/**
 * 'YYYY-MM-DD' from a Date, using LOCAL calendar parts.
 *
 * Not toISOString(): that converts to UTC first, so local midnight in any timezone
 * ahead of UTC lands on the previous day — which stamped an IMD forecast issued on
 * the 29th as the 28th.
 */
function isoDay(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/**
 * Build the five-day risk strip.
 *
 * Two sources, deliberately combined this way:
 *
 *  - OpenWeather gives a real per-day rainfall total for ANY coordinate, so it is the
 *    base series and every location gets a forecast — including tracked places that
 *    IMD does not cover.
 *  - IMD basin QPF, where available, is authoritative for river basins. Its rows are
 *    SUB-BASINS (each carrying Day1…Day5), not days — reading one day per sub-basin
 *    is what produced five rows all stamped with the same issue date. We take the
 *    worst sub-basin per day, which is the right reading for a basin-wide warning.
 *
 * Where both exist the higher figure wins, because under-stating flood risk is the
 * more costly error.
 */
function buildPredictions(forecastDaily, qpf) {
  const rows = new Map();   // ISO date → row

  // Base series: real observed-forecast rainfall, available everywhere.
  for (const [iso, mm] of Object.entries(forecastDaily ?? {})) {
    rows.set(iso, { iso, mm: Number(mm) || 0, sources: ['OpenWeather'] });
  }

  // Overlay: IMD basin QPF, expanded across days and reduced across sub-basins.
  if (Array.isArray(qpf) && qpf.length > 0) {
    const issued = qpf.find(r => r.Date)?.Date;
    if (issued) {
      for (let day = 1; day <= 5; day += 1) {
        const worst = Math.max(
          ...qpf.map(r => qpfMidpoint(r[`Day${day}`])),
          0,
        );
        if (!Number.isFinite(worst) || worst <= 0) continue;

        const date = new Date(`${issued}T00:00:00`);
        date.setDate(date.getDate() + (day - 1));
        const iso = isoDay(date);

        const existing = rows.get(iso);
        if (!existing) {
          rows.set(iso, { iso, mm: worst, sources: ['IMD basin QPF'] });
        } else if (worst > existing.mm) {
          existing.mm = worst;
          existing.sources = ['IMD basin QPF', ...existing.sources];
        } else {
          existing.sources = [...existing.sources, 'IMD basin QPF'];
        }
      }
    }
  }

  return [...rows.values()]
    .sort((a, b) => a.iso.localeCompare(b.iso))
    .slice(0, 5)
    .map(row => {
      const risk = riskFromRainfall(row.mm);
      const date = new Date(`${row.iso}T00:00:00`);
      return {
        day: date.toLocaleDateString('en-IN', DAY_FMT),
        iso: row.iso,
        mm: Math.round(row.mm * 10) / 10,
        source: row.sources.join(' + '),
        ...risk,
      };
    });
}

export function deriveDashboard(payload) {
  if (!payload) return null;

  const { location, summary, observations, qpf = [], events = [], predictions = [] } = payload;
  const raw = (key) => observations?.[key]?.raw ?? {};

  // ── Live conditions (OpenWeather — a real reading, unlike IMD's mock) ──
  const live = summary?.live ?? null;

  // ── Current weather (station observation) ──────────────────────────
  const wx = raw('current_wx');
  const rain24h = num(wx['Last 24 hrs Rainfall'], num(summary?.rain_24h_mm));
  const windSpd = num(wx['Wind Speed']);
  const wxCode = String(wx['Weather Code'] ?? '00').padStart(2, '0');

  // ── District rainfall actuals vs normals ───────────────────────────
  const rf = raw('rainfall');
  const weeklyActual = num(rf['Weekly Actual']);
  const weeklyNormal = num(rf['Weekly Normal'], 70);
  const reservoirRatio = weeklyNormal > 0 ? weeklyActual / weeklyNormal : 1;
  const reservoirsStressed = reservoirRatio > 1.5;

  // ── 5-day colour-coded warnings ────────────────────────────────────
  const warn = raw('warning');
  const dayColors = [1, 2, 3, 4, 5].map(d => warn[`Day${d}_Color`] ?? 1);
  const dayCodes = [1, 2, 3, 4, 5].map(d =>
    String(warn[`Day_${d}`] ?? '1').split(',').map(Number)
  );

  // ── AWS telemetry ──────────────────────────────────────────────────
  const aws = raw('aws');

  // ── Five-day risk strip ────────────────────────────────────────────
  const forecastDaily = observations?.ow_forecast?.raw?.daily_mm ?? {};
  const qpfRows = buildPredictions(forecastDaily, qpf);

  const trendUp = qpfRows.length >= 2 && qpfRows[1].pct > qpfRows[0].pct;
  const trendDown = qpfRows.length >= 2 && qpfRows[1].pct < qpfRows[0].pct;

  // ── Events: already correlated and scored by the backend ───────────
  const uiEvents = events
    .filter(e => e.status !== 'resolved')
    .map(e => ({
      id: e.id,
      eventUid: e.event_uid,
      title: `${e.category.replace(/_/g, ' ')} — ${e.district}`.replace(/^\w/, c => c.toUpperCase()),
      severity: SEVERITY_TONE[e.severity] ?? 'warning',
      severityLabel: e.severity,
      status: e.status,
      subtitle: `${e.district}, ${e.state ?? ''}`.replace(/, $/, ''),
      started: new Date(e.first_seen).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
      }),
      metric: `${e.risk_score}/100`,
      metricLabel: 'Risk Score',
      confidence: e.confidence_score,
      probability: e.prediction_probability,
      message: e.ai_summary,
      icon: 'cloud-lightning',
    }));

  const alertColor = summary?.alert_code ?? 1;

  return {
    location,

    // Alert headline — decided by the backend, formatted here
    alertColor,
    alertLabel: COLOR_LABEL[alertColor] ?? 'Low',
    alertSeverity: COLOR_SEVERITY[alertColor] ?? 'success',
    alertColorName: summary?.alert_color ?? 'Green',
    nowcastMsg: observations?.nowcast?.message ?? '',
    nowcastStation: observations?.nowcast?.district ?? location?.district,

    activeEvents: summary?.active_events ?? uiEvents.length,
    maxRisk: summary?.max_risk_score ?? 0,
    severeProbability: summary?.severe_probability ?? null,

    // Live conditions, preferred wherever a real number beats a mocked one
    live,
    isLive: Boolean(live),
    liveTemp: live?.temperature_c ?? null,
    liveFeelsLike: live?.feels_like_c ?? null,
    liveHumidity: live?.humidity_pct ?? null,
    liveWind: live?.wind_speed_kmph ?? null,
    livePressure: live?.pressure_hpa ?? null,
    liveConditions: live?.conditions ?? null,
    liveRain: live?.rain_observed_mm ?? null,
    liveObservedAt: live?.observed_at ?? null,
    liveStation: live?.station ?? null,
    forecast24hMm: summary?.forecast_24h_mm ?? null,
    forecast72hMm: summary?.forecast_72h_mm ?? null,
    forecastSlots: observations?.ow_forecast?.raw?.slots ?? [],
    forecastDaily,

    // Weather
    rain24h,
    temp: wx.Temperature != null ? `${wx.Temperature}` : '—',
    humidity: wx.Humidity != null ? `${wx.Humidity}%` : '—',
    windSpd,
    mslp: wx['M.S.L.P'] ?? '—',
    nebulosity: wx.Nebulosity ?? 0,
    wxCode,
    wxDesc: WX_CODE_MAP[wxCode] ?? 'Partly Cloudy',
    stationName: wx.Station ?? observations?.current_wx?.station_name ?? location?.district,

    // AWS
    awsTemp: aws.CURR_TEMP ?? null,
    awsRH: aws.RH ?? null,
    awsWind: aws.WIND_SPEED ?? null,
    awsMSLP: aws.MSLP ?? null,
    awsMaxTemp: aws.MAX_TEMP ?? null,
    awsMinTemp: aws.MIN_TEMP ?? null,

    // Rainfall actuals vs normals
    dailyActual: num(rf['Daily Actual']),
    dailyNormal: num(rf['Daily Normal'], 10),
    weeklyActual, weeklyNormal,
    monthlyActual: num(rf['Monthly Actual']),
    monthlyNormal: num(rf['Monthly Normal'], 300),
    dailyDep: num(rf['Daily Departure Per']),
    weeklyDep: num(rf['Weekly Departure Per']),
    monthlyDep: num(rf['Monthly Departure Per']),
    dailyCategory: rf['Daily Category'] ?? 'N',
    weeklyCategory: rf['Weekly Category'] ?? 'N',

    // Reservoir proxy — still a proxy until CWC is wired, and labelled as such in the UI
    reservoirRatio, reservoirsStressed,
    reservoirLabel: reservoirsStressed
      ? `${Math.min(Math.round(reservoirRatio * 60), 98)}% est.` : 'Normal',
    reservoirSeverity: reservoirsStressed ? 'warning' : 'success',

    // River proxy — same caveat
    riverLevelValue: rain24h > 50 ? `${(rain24h / 15).toFixed(1)} m`
      : rain24h > 20 ? `${(rain24h / 18).toFixed(1)} m` : `${(rain24h / 25 + 1.2).toFixed(1)} m`,
    riverLevelProxy: rain24h > 50 ? 'Above Warning Level'
      : rain24h > 20 ? 'At Warning Level' : 'Safe Levels',
    riverSeverity: rain24h > 50 ? 'danger' : rain24h > 20 ? 'warning' : 'success',

    // Trend
    trendUp, trendDown,
    trendLabel: trendUp ? 'Increasing' : trendDown ? 'Decreasing' : 'Stable',
    trendSeverity: trendUp ? 'danger' : trendDown ? 'success' : 'warning',

    events: uiEvents,
    predictions: qpfRows,
    mlPredictions: predictions,
    dayColors, dayCodes,
    forecast: raw('forecast'),
    warn, rf, wx,
  };
}
