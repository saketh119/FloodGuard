/**
 * imdService.js
 *
 * Centralised API client for the IMD Mock Server.
 * Every function here maps 1-to-1 with a real IMD endpoint.
 * When we go live, change IMD_BASE_URL to the real API base and
 * add the JWT auth header — the rest of the app stays untouched.
 *
 * Real IMD base: https://api.imd.gov.in
 * Mock base:     http://localhost:8080
 */

import axios from 'axios';

const IMD_BASE_URL = import.meta.env.VITE_IMD_BASE_URL ?? '';

const client = axios.create({
  baseURL: IMD_BASE_URL,
  timeout: 8000,
  headers: {
    // Swap for:  Authorization: `Bearer ${token}`  when going live
    'Content-Type': 'application/json',
  },
});

// ── Helpers ──────────────────────────────────────────────────────────
const unwrap = (res) => res.data;   // IMD envelope: { status, data, totalCount, message }

// ── API Methods ───────────────────────────────────────────────────────

/**
 * GET /api/v1/cityforecastloc?id=<stationCode>
 * 7-day forecast including lat/lon.
 */
export async function fetchCityForecast(stationId) {
  const res = await client.get('/api/v1/cityforecastloc', {
    params: stationId ? { id: stationId } : {},
  });
  return unwrap(res);
}

/**
 * GET /api/v1/current_wx?id=<stationId>
 * Current weather observation.
 */
export async function fetchCurrentWeather(stationId) {
  const res = await client.get('/api/v1/current_wx', {
    params: stationId ? { id: stationId } : {},
  });
  return unwrap(res);
}

/**
 * GET /api/v1/nowcast?id=<districtId>
 * District-level nowcast warning (next 3 hrs).
 */
export async function fetchDistrictNowcast(districtId) {
  const res = await client.get('/api/v1/nowcast', {
    params: districtId ? { id: districtId } : {},
  });
  return unwrap(res);
}

/**
 * GET /api/v1/districtrainfall?id=<districtId>
 * Daily / weekly / monthly rainfall actuals vs. normals.
 */
export async function fetchDistrictRainfall(districtId) {
  const res = await client.get('/api/v1/districtrainfall', {
    params: districtId ? { id: districtId } : {},
  });
  return unwrap(res);
}

/**
 * GET /api/v1/districtwarning?id=<districtId>
 * 5-day colour-coded district warnings.
 */
export async function fetchDistrictWarning(districtId) {
  const res = await client.get('/api/v1/districtwarning', {
    params: districtId ? { id: districtId } : {},
  });
  return unwrap(res);
}

/**
 * GET /api/v1/aws_data?sid=<stateId>
 * AWS/ARG realtime station data for an entire state.
 */
export async function fetchAwsData(stateId) {
  const res = await client.get('/api/v1/aws_data', {
    params: stateId ? { sid: stateId } : {},
  });
  return unwrap(res);
}

/**
 * GET /api/v1/basinqpf?id=<basinId>
 * River basin quantitative precipitation forecast.
 */
export async function fetchBasinQpf(basinId) {
  const res = await client.get('/api/v1/basinqpf', {
    params: basinId ? { id: basinId } : {},
  });
  return unwrap(res);
}
