'use client';

/**
 * useFloodEvents — correlated flood events across ALL districts.
 *
 * Distinct from the dashboard context, which is scoped to one district.
 *
 * Updates are driven by the shared SSE cycle signal rather than this hook opening its
 * own EventSource: browsers cap concurrent connections per origin, and one stream
 * already carries the event. The interval below is only a fallback for when the
 * stream is down, so it can be slow.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

import { useFloodGuard } from '@/context/FloodGuardContext';
import { getEvents } from '@/lib/api';

const FALLBACK_POLL_MS = 60_000;

export function useFloodEvents(params = {}, pollIntervalMs = FALLBACK_POLL_MS) {
  const { cycle } = useFloodGuard();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  // Serialised so a fresh object literal per render does not restart the interval.
  const paramKey = JSON.stringify(params);

  const load = useCallback(async () => {
    try {
      setEvents(await getEvents(JSON.parse(paramKey)));
      setError(null);
    } catch (err) {
      setError(err?.message ?? 'FloodGuard API unreachable');
    } finally {
      setLoading(false);
    }
  }, [paramKey]);

  // Refetch on mount and whenever the pipeline reports a completed cycle.
  useEffect(() => { load(); }, [load, cycle]);

  useEffect(() => {
    intervalRef.current = setInterval(load, pollIntervalMs);
    return () => clearInterval(intervalRef.current);
  }, [load, pollIntervalMs]);

  return { events, loading, error, refresh: load };
}
