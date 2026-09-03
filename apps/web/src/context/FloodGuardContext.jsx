'use client';

/**
 * FloodGuardContext — one place that owns the selected location and its live data.
 *
 * The Vite app threaded `apiData / loading / error / onRefresh / locationKey` through
 * a router component into all nine pages. In the App Router there is no such shared
 * parent, and prop-drilling through route boundaries is not possible anyway, so the
 * state lives in a provider mounted once in the root layout.
 */

import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from 'react';
import toast from 'react-hot-toast';

import { getDashboard, getDistricts, getHealth } from '@/lib/api';
import { deriveDashboard } from '@/lib/derive';

// The SSE stream is the primary update path; this poll is only a safety net for
// when the stream is down, so it can be slow.
const FALLBACK_POLL_MS = 60_000;
const TICK_MS = 1_000;
const DEFAULT_DISTRICT = 'Kamrup Metropolitan';
const STORAGE_KEY = 'floodguard.district';

const FloodGuardContext = createContext(null);

export function FloodGuardProvider({ children }) {
  const [districts, setDistricts] = useState([]);
  const [district, setDistrictState] = useState(DEFAULT_DISTRICT);
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [health, setHealth] = useState(null);
  const [connected, setConnected] = useState(false);
  // Bumped on every completed collection cycle. Components that keep their own
  // data (cross-district events, for one) depend on this instead of polling.
  const [cycle, setCycle] = useState(0);
  // Ticks once a second purely so "12s ago" counts up without a data refetch.
  const [now, setNow] = useState(() => Date.now());

  const firstLoad = useRef(true);
  const intervalRef = useRef(null);
  const loadRef = useRef(null);

  // Restore the last viewed district. Wrapped because storage throws in some
  // privacy modes, and a missing preference must never break the dashboard.
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) setDistrictState(saved);
    } catch { /* no stored preference available */ }
  }, []);

  const setDistrict = useCallback((next) => {
    setDistrictState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch { /* preference simply will not persist */ }
  }, []);

  const reloadDistricts = useCallback(
    () => getDistricts().then(setDistricts).catch(() => {}),
    [],
  );

  useEffect(() => {
    // Degrades to the current district if this fails — the dashboard still works.
    reloadDistricts();
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, [reloadDistricts]);

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(t);
  }, []);

  const load = useCallback(async (notify = false) => {
    try {
      const data = await getDashboard(district);
      setPayload(data);
      setLastUpdated(new Date());
      setError(null);
      if (notify) toast.success('Data refreshed', { id: 'refresh', duration: 2000 });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail ?? err?.message ?? 'FloodGuard API unreachable');
    } finally {
      setLoading(false);
    }
  }, [district]);

  // Keep a stable handle so the SSE effect does not need `load` as a dependency —
  // it would otherwise tear down and reopen the stream on every district change.
  useEffect(() => { loadRef.current = load; }, [load]);

  useEffect(() => {
    setLoading(true);
    setPayload(null);
    load(!firstLoad.current);
    firstLoad.current = false;

    clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => load(false), FALLBACK_POLL_MS);
    return () => clearInterval(intervalRef.current);
  }, [load]);

  // Live updates: the backend announces each completed collection cycle, so the UI
  // refreshes the moment new data exists instead of waiting out a poll interval.
  // EventSource reconnects by itself, so there is no retry logic to write here.
  useEffect(() => {
    let source;
    try {
      source = new EventSource('/api/stream');
    } catch {
      return;                       // no EventSource support: the poll still runs
    }

    source.addEventListener('ready', () => setConnected(true));
    source.addEventListener('cycle', () => {
      setConnected(true);
      setCycle(c => c + 1);
      loadRef.current?.(false);     // silent: an automatic update should not toast
    });
    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);

    return () => source.close();
  }, []);

  const toggleTheme = useCallback(() => {
    setDarkMode(prev => {
      const next = !prev;
      document.documentElement.setAttribute('data-theme', next ? 'dark' : 'light');
      return next;
    });
  }, []);

  const dash = useMemo(() => deriveDashboard(payload), [payload]);

  const value = useMemo(() => ({
    districts, district, setDistrict,
    payload, dash, loading, error, lastUpdated, now,
    refresh: () => load(true),
    darkMode, toggleTheme,
    health, connected, cycle, reloadDistricts,
    alertCount: dash?.activeEvents ?? 0,
    location: dash?.location ?? { district, state: '' },
  }), [districts, district, setDistrict, payload, dash, loading, error, lastUpdated,
       now, load, darkMode, toggleTheme, health, connected, cycle, reloadDistricts]);

  return <FloodGuardContext.Provider value={value}>{children}</FloodGuardContext.Provider>;
}

export function useFloodGuard() {
  const ctx = useContext(FloodGuardContext);
  if (!ctx) throw new Error('useFloodGuard must be used inside <FloodGuardProvider>');
  return ctx;
}
