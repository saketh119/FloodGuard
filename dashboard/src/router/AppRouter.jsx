import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard        from '../components/Dashboard/Dashboard';
import CurrentFloods    from '../pages/CurrentFloods/CurrentFloods';
import Alerts           from '../pages/Alerts/Alerts';
import Predictions      from '../pages/Predictions/Predictions';
import WeatherRainfall  from '../pages/WeatherRainfall/WeatherRainfall';
import RiversReservoirs from '../pages/RiversReservoirs/RiversReservoirs';
import Reports          from '../pages/Reports/Reports';
import SavedLocations   from '../pages/SavedLocations/SavedLocations';
import ChatAssistant    from '../pages/ChatAssistant/ChatAssistant';
import MapView          from '../pages/MapView/MapView';

/**
 * AppRouter — all pages receive shared props:
 *  locationKey, onLocationChange, apiData, loading, error, onRefresh
 * so every page shows the same location's live data without re-fetching.
 */
export default function AppRouter({ locationKey, onLocationChange, apiData, loading, error, onRefresh }) {
  const shared = { locationKey, onLocationChange, apiData, loading, error, onRefresh };
  return (
    <Routes>
      <Route path="/"            element={<Dashboard        {...shared} />} />
      <Route path="/floods"      element={<CurrentFloods    {...shared} />} />
      <Route path="/alerts"      element={<Alerts           {...shared} />} />
      <Route path="/predictions" element={<Predictions      {...shared} />} />
      <Route path="/weather"     element={<WeatherRainfall  {...shared} />} />
      <Route path="/rivers"      element={<RiversReservoirs {...shared} />} />
      <Route path="/reports"     element={<Reports          {...shared} />} />
      <Route path="/saved"       element={<SavedLocations   {...shared} />} />
      <Route path="/chat"        element={<ChatAssistant />} />
      <Route path="/map"         element={<MapView       {...shared} />} />
      <Route path="*"            element={<Navigate to="/" replace />} />
    </Routes>
  );
}
