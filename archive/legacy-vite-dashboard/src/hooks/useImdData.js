/**
 * useImdData.js — Polls all IMD endpoints for a given location.
 *
 * Strategy:
 *  • Immediate fetch on mount / location change
 *  • setInterval re-fetches every pollIntervalMs (default 30 s)
 *  • Interval is cleared on unmount — no memory leaks
 *  • Promise.all → all 6 endpoints in parallel, single latency budget
 *  • Exposes { data, loading, error, lastUpdated, refresh }
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchCurrentWeather,
  fetchDistrictNowcast,
  fetchDistrictRainfall,
  fetchDistrictWarning,
  fetchBasinQpf,
  fetchAwsData,
  fetchCityForecast,
} from '../services/imdService';

const DEFAULT_POLL_MS = 30_000;

export function useImdData(location, pollIntervalMs = DEFAULT_POLL_MS) {
  const [data, setData]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);

  const fetchAll = useCallback(async () => {
    if (!location) return;
    try {
      const [weather, nowcast, rainfall, warning, qpf, aws, forecast] = await Promise.all([
        fetchCurrentWeather(location.stationId),
        fetchDistrictNowcast(location.districtId),
        fetchDistrictRainfall(location.districtId),
        fetchDistrictWarning(location.districtId),
        fetchBasinQpf(location.basinId),
        fetchAwsData(location.awsStateId),           // AWS station data for weather page
        fetchCityForecast(location.stationId),       // 7-day forecast for predictions page
      ]);

      setData({ weather, nowcast, rainfall, warning, qpf, aws, forecast });
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch IMD data');
    } finally {
      setLoading(false);
    }
  }, [location]);

  useEffect(() => {
    setLoading(true);
    setData(null);
    fetchAll();

    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(fetchAll, pollIntervalMs);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchAll, pollIntervalMs]);

  return { data, loading, error, lastUpdated, refresh: fetchAll };
}
