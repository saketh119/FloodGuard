import { useEffect } from 'react';
import styles from './MapView.module.css';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { LOCATIONS, deriveDashboardData } from '../../data/locations';
import { MapPin, Info } from 'lucide-react';

// Fix Leaflet default marker icon paths (Vite bundles break them)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const SEVERITY_COLOR = {
  danger:  '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
};

function makeIcon(severity) {
  const color = SEVERITY_COLOR[severity] ?? '#2563eb';
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="36" viewBox="0 0 28 36">
      <path d="M14 0C6.268 0 0 6.268 0 14c0 9.625 14 22 14 22S28 23.625 28 14C28 6.268 21.732 0 14 0z" fill="${color}" opacity="0.9"/>
      <circle cx="14" cy="14" r="6" fill="white" opacity="0.95"/>
    </svg>
  `;
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [28, 36],
    iconAnchor: [14, 36],
    popupAnchor: [0, -36],
  });
}

const ALERT_LABELS = { success: 'Safe', warning: 'Moderate', danger: 'High Alert' };

export default function MapView({ locationKey, apiData, loading }) {
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, location);
  const allLocations = Object.values(LOCATIONS);

  // Derive severity per location (current data for selected, estimated for others)
  const locSeverity = (loc) => {
    if (loc.key === locationKey && dash) return dash.alertSeverity;
    // Hyderabad/Warangal share the same districtId=164 (flood mock) — mark danger
    if (loc.districtId === '164') return 'danger';
    return 'success';
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><MapPin size={22} /> Interactive Map</h1>
        <p className={styles.subtitle}>IMD station locations with live alert levels — {location.label}, {location.state}</p>
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        {Object.entries(SEVERITY_COLOR).map(([sev, color]) => (
          <div key={sev} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: color }} />
            <span>{ALERT_LABELS[sev]}</span>
          </div>
        ))}
        <div className={styles.legendNote}><Info size={12} /> Click a marker for station details</div>
      </div>

      {/* Map */}
      <div className={styles.mapWrap}>
        <MapContainer
          center={[location.lat, location.lng]}
          zoom={6}
          className={styles.map}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {allLocations.map(loc => {
            const sev = locSeverity(loc);
            const color = SEVERITY_COLOR[sev];
            const isSelected = loc.key === locationKey;
            const d = isSelected ? dash : null;

            return (
              <Marker
                key={loc.key}
                position={[loc.lat, loc.lng]}
                icon={makeIcon(sev)}
              >
                <Popup className={styles.popup} maxWidth={260}>
                  <div className={styles.popupContent}>
                    <div className={styles.popupHeader}>
                      <strong className={styles.popupCity}>{loc.label}</strong>
                      <span className={styles.popupBadge} style={{ background: color + '22', color }}>
                        {ALERT_LABELS[sev]}
                      </span>
                    </div>
                    <div className={styles.popupState}>{loc.state}</div>
                    <div className={styles.popupStats}>
                      <div className={styles.popupStat}>
                        <span className={styles.pStatLabel}>River</span>
                        <span className={styles.pStatVal}>{loc.riverName}</span>
                      </div>
                      {d && (
                        <>
                          <div className={styles.popupStat}>
                            <span className={styles.pStatLabel}>24h Rainfall</span>
                            <span className={styles.pStatVal}>{d.rain24h.toFixed(1)} mm</span>
                          </div>
                          <div className={styles.popupStat}>
                            <span className={styles.pStatLabel}>Temperature</span>
                            <span className={styles.pStatVal}>{d.awsTemp ?? d.temp}°C</span>
                          </div>
                          <div className={styles.popupStat}>
                            <span className={styles.pStatLabel}>Nowcast</span>
                            <span className={styles.pStatVal}>{d.nowcastMsg || 'Clear'}</span>
                          </div>
                        </>
                      )}
                    </div>
                    <div className={styles.popupCoords}>{loc.coords}</div>
                  </div>
                </Popup>

                {/* Alert radius circle for high severity */}
                {sev !== 'success' && (
                  <Circle
                    center={[loc.lat, loc.lng]}
                    radius={sev === 'danger' ? 60000 : 35000}
                    pathOptions={{
                      color,
                      fillColor: color,
                      fillOpacity: 0.08,
                      weight: 1.5,
                      dashArray: sev === 'danger' ? '6 4' : '4 4',
                    }}
                  />
                )}
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      {/* Station summary grid */}
      <div className={styles.stationGrid}>
        {allLocations.map(loc => {
          const sev = locSeverity(loc);
          const color = SEVERITY_COLOR[sev];
          const isSelected = loc.key === locationKey;
          return (
            <div key={loc.key} className={`${styles.stationCard} ${isSelected ? styles.selected : ''}`}>
              <div className={styles.stationDot} style={{ background: color }} />
              <div className={styles.stationInfo}>
                <div className={styles.stationName}>{loc.label}</div>
                <div className={styles.stationState}>{loc.state}</div>
                <div className={styles.stationRiver}>{loc.riverName}</div>
              </div>
              <div className={styles.stationAlert} style={{ color }}>{ALERT_LABELS[sev]}</div>
            </div>
          );
        })}
      </div>

      <div className={styles.footer}>
        <Info size={14} />
        <span>Map data: OpenStreetMap contributors · Alert levels sourced from IMD mock server · Radius circles are illustrative zones.</span>
      </div>
    </div>
  );
}
