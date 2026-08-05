import { useState, useEffect, useCallback, useRef } from 'react';
import backendService from '../services/backendService';

export function useBackendData(location, pollIntervalMs = 30000) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);
    const intervalRef = useRef(null);

    const fetchAll = useCallback(async () => {
        if (!location) return;
        try {
            const district = location.districtId === '164' ? 'Kamrup Metropolitan' : location.label;

            const [events, weather, stations, predictions] = await Promise.all([
                backendService.getEvents({ district }),
                backendService.getWeather({ district }),
                backendService.getStations(), // For rivers
                backendService.getPredictions({ district })
            ]);

            setData({ events, weather, stations, predictions });
            setLastUpdated(new Date());
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to fetch backend data');
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
