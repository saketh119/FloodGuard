/**
 * useFloodEvents.js — polls the FloodGuard backend for correlated flood events.
 *
 * Separate from useImdData because these are derived events with confidence and
 * evidence behind them, not raw IMD readings, and they change on the backend's
 * collection cycle rather than on every render.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchEvents } from '../services/floodguardService';

const DEFAULT_POLL_MS = 60_000;

export function useFloodEvents(params = {}, pollIntervalMs = DEFAULT_POLL_MS) {
  const [events, setEvents]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const intervalRef = useRef(null);

  // Serialise so a fresh object literal each render does not restart the interval.
  const paramKey = JSON.stringify(params);

  const load = useCallback(async () => {
    try {
      setEvents(await fetchEvents(JSON.parse(paramKey)));
      setError(null);
    } catch (err) {
      setError(err?.message ?? 'FloodGuard backend unreachable');
    } finally {
      setLoading(false);
    }
  }, [paramKey]);

  useEffect(() => {
    load();
    intervalRef.current = setInterval(load, pollIntervalMs);
    return () => clearInterval(intervalRef.current);
  }, [load, pollIntervalMs]);

  return { events, loading, error, refresh: load };
}
