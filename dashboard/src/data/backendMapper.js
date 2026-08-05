export function mapBackendToDash(backendData, locationCfg) {
    if (!backendData || !backendData.weather) return null;
    const { events = [], weather, stations = [], predictions = [] } = backendData;

    // --- Weather ---
    const rain24h = weather.rainfall_1h ? weather.rainfall_1h * 24 : 0;
    const temp = weather.temp ? (weather.temp - 273.15).toFixed(1) : '—'; // OWM mock might return Kelvin, but our mock returns Celsius directly (wait, our mock returns 24.2 / 32.8)
    const tempC = weather.temp; // Mock returns celsius
    const humidity = weather.humidity ?? '—';
    const windSpd = weather.wind_speed ?? 0;
    const mslp = weather.pressure ?? '—';
    const wxDesc = (weather.weather_desc || 'Clear').replace(/\b\w/g, l => l.toUpperCase());
    const stationName = weather.city_name || locationCfg.label;

    // --- Events ---
    const activeEvents = events.filter(e => e.status === 'active' || e.status === 'high_risk');
    const mappedEvents = events.map(e => ({
        id: e.event_id,
        title: `Flood Event: ${e.status.replace('_', ' ').toUpperCase()}`,
        severity: e.status === 'active' ? 'danger' : e.status === 'high_risk' ? 'warning' : 'success',
        subtitle: `${e.district}, ${e.state}`,
        started: new Date(e.first_seen).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }),
        metric: `${(e.confidence_score * 100).toFixed(0)}%`,
        metricLabel: 'Confidence',
        icon: e.status === 'active' ? 'alert-triangle' : 'shield-alert',
        message: e.ai_summary || `Event detected with ${(e.confidence_score * 100).toFixed(0)}% confidence based on ${e.source_count} sources.`,
    }));

    // Find highest severity event for the alert banner
    const topEvent = activeEvents.length > 0 ? activeEvents.sort((a,b) => b.confidence_score - a.confidence_score)[0] : null;
    const alertLabel = topEvent ? topEvent.status.replace('_', ' ').toUpperCase() : 'Safe';
    const alertSeverity = topEvent ? (topEvent.status === 'active' ? 'danger' : 'warning') : 'success';
    const alertColor = topEvent ? (topEvent.status === 'active' ? 4 : 3) : 1;
    const nowcastMsg = topEvent?.ai_summary || '';

    // --- Predictions ---
    const mappedPreds = predictions.slice(0, 5).map((p, i) => {
        const pct = Math.round(p.flood_probability * 100);
        const severity = pct > 60 ? 'danger' : pct > 30 ? 'warning' : 'success';
        const date = new Date(p.prediction_time);
        date.setDate(date.getDate() + i);
        return {
            day: date.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }),
            pct,
            severity,
            label: severity === 'danger' ? 'High' : severity === 'warning' ? 'Medium' : 'Low',
            qpfRange: `${pct}% Risk`,
            basin: p.district,
            subBasin: p.state
        };
    });

    const trendUp = mappedPreds.length >= 2 && mappedPreds[1].pct > mappedPreds[0].pct;
    const trendDown = mappedPreds.length >= 2 && mappedPreds[1].pct < mappedPreds[0].pct;

    // --- Rivers (CWC) ---
    // Try to find a station in the same district, or just take the first one with a flood scenario
    const station = stations.find(s => s.district?.toLowerCase() === locationCfg.districtId?.toLowerCase()) || stations[0] || {};
    const measurements = station.measurements || [];
    const latestMeasurement = measurements[0] || {};
    
    const riverLevelValue = latestMeasurement.water_level ? `${latestMeasurement.water_level.toFixed(2)} m` : '—';
    const riverLevelProxy = latestMeasurement.status === 'severe' ? 'Above Danger Level' : latestMeasurement.status === 'danger' ? 'At Danger Level' : latestMeasurement.status === 'warning' ? 'At Warning Level' : 'Safe';
    const riverSeverity = latestMeasurement.status === 'severe' || latestMeasurement.status === 'danger' ? 'danger' : latestMeasurement.status === 'warning' ? 'warning' : 'success';

    return {
        // Alert
        alertLabel, alertSeverity, alertColor,
        nowcastMsg, nowcastStation: stationName,
        activeEvents: activeEvents.length,
        // Weather
        rain24h, temp: tempC, humidity, windSpd, mslp, nebulosity: 0, wxDesc, wxCode: '00', stationName,
        // AWS placeholder
        awsTemp: tempC, awsRH: humidity, awsWind: windSpd, awsMSLP: mslp, awsMaxTemp: tempC, awsMinTemp: tempC,
        // Rainfall placeholder
        dailyActual: rain24h, dailyNormal: 10, weeklyActual: rain24h * 7, weeklyNormal: 70,
        monthlyActual: rain24h * 30, monthlyNormal: 300,
        dailyDep: 0, weeklyDep: 0, monthlyDep: 0, dailyCategory: 'N', weeklyCategory: 'N',
        // Reservoir proxy
        reservoirRatio: 1, reservoirsStressed: false, reservoirLabel: 'Normal', reservoirSeverity: 'success',
        // River
        riverLevelValue, riverLevelProxy, riverSeverity,
        // Trend
        trendUp, trendDown,
        trendLabel: trendUp ? 'Increasing' : trendDown ? 'Decreasing' : 'Stable',
        trendSeverity: trendUp ? 'danger' : trendDown ? 'success' : 'warning',
        // Events & predictions
        events: mappedEvents, predictions: mappedPreds,
        // Warning grid (mock 5-day colours based on predictions)
        dayColors: mappedPreds.map(p => p.severity === 'danger' ? 4 : p.severity === 'warning' ? 3 : 1),
        dayCodes: mappedPreds.map(p => p.severity === 'danger' ? [3,4] : p.severity === 'warning' ? [2] : [1]),
        // Raw
        warn: { District: locationCfg.label, Date: new Date().toLocaleDateString('en-IN') }, 
        rf: {}, nc: {}, wx: { temp: tempC, humidity, windSpd, mslp, wxDesc, rain24h },
    };
}
