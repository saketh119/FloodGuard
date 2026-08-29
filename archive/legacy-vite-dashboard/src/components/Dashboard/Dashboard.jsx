import { useNavigate } from 'react-router-dom';
import styles from './Dashboard.module.css';
import { LOCATIONS, deriveDashboardData } from '../../data/locations';
import LocationBar from '../LocationBar/LocationBar';
import StatCard from '../StatCard/StatCard';
import EventItem from '../EventItem/EventItem';
import PredictionRow from '../PredictionRow/PredictionRow';
import BottomCard from '../BottomCard/BottomCard';

import {
  AlertTriangle, Waves, CloudRain, TrendingUp, TrendingDown,
  Minus, MapPin, Navigation2, CloudLightning, Droplets,
  Database, Home, Info, ShieldCheck, ListTodo, Activity,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function Dashboard({ locationKey, onLocationChange, apiData, loading, error }) {
  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const navigate = useNavigate();
  const dash = deriveDashboardData(apiData, location);

  const trendIcon = dash?.trendUp ? TrendingUp : dash?.trendDown ? TrendingDown : Minus;

  const statsCards = dash ? [
    {
      label: 'Current Alert Level',
      value: dash.alertLabel,
      desc: 'Flood risk in your area',
      icon: AlertTriangle,
      severity: dash.alertSeverity,
    },
    {
      label: 'Active Flood Events',
      value: String(dash.activeEvents),
      desc: 'In and around selected area',
      icon: Waves,
      severity: dash.activeEvents >= 2 ? 'danger' : dash.activeEvents === 1 ? 'warning' : 'success',
    },
    {
      label: 'Last 24h Rainfall',
      value: `${dash.rain24h.toFixed(1)} mm`,
      desc: dash.rain24h > 64 ? 'Heavy rainfall' : dash.rain24h > 15 ? 'Moderate' : 'Light / No rain',
      icon: CloudRain,
      severity: dash.rain24h > 64 ? 'danger' : dash.rain24h > 15 ? 'warning' : 'success',
    },
    {
      label: 'Risk Trend',
      value: dash.trendLabel,
      desc: 'Next 24–48 hours',
      icon: trendIcon,
      severity: dash.trendSeverity,
    },
  ] : [];

  // Bottom cards — all wired from API data
  const bottomCards = dash ? [
    {
      label: 'Weather Now',
      value: dash.awsTemp != null ? `${dash.awsTemp}°C` : `${dash.temp}°C`,
      desc: dash.wxDesc,
      descColor: 'var(--brand)',
      icon: CloudLightning,
      severity: 'brand',
      onClick: () => navigate('/weather'),
    },
    {
      label: `River Level (${location.riverName})`,
      value: dash.riverLevelValue,
      desc: dash.riverLevelProxy,
      descColor: `var(--${dash.riverSeverity})`,
      icon: Droplets,
      severity: dash.riverSeverity,
      clickable: true,
      onClick: () => navigate('/rivers'),
    },
    {
      label: 'Reservoir Status',
      value: dash.reservoirLabel,
      desc: dash.reservoirsStressed ? `${dash.weeklyDep.toFixed(0)}% above normal` : 'Within normal range',
      descColor: `var(--${dash.reservoirSeverity})`,
      icon: Database,
      severity: dash.reservoirSeverity,
    },
    {
      label: 'Nearby Shelters',
      value: '—',
      desc: 'User input needed',
      descColor: 'var(--text-muted)',
      icon: Home,
      severity: 'success',
      clickable: true,
      onClick: () => navigate('/saved'),
    },
  ] : [];

  const handleLocationChange = (key) => {
    onLocationChange(key);
    toast(`Switched to ${LOCATIONS[key]?.label ?? key}`, { icon: '📍' });
  };

  return (
    <div className={styles.page}>

      <LocationBar selected={location} onSelect={handleLocationChange} />

      {/* Active Location banner */}
      <div className={styles.activeBanner}>
        <div className={styles.bannerLeft}>
          <MapPin size={16} style={{ color: 'var(--brand)' }} />
          <span className={styles.bannerCity}>{location.label}, {location.state}</span>
          <button className={styles.changeBtn} onClick={() => document.querySelector('input[placeholder*="Search"]')?.focus()}>
            Change
          </button>
        </div>
        <div className={styles.bannerRight}>
          <Navigation2 size={14} style={{ transform: 'rotate(45deg)', opacity: .7 }} />
          <span>{location.coords}</span>
        </div>
      </div>

      {/* Stats row */}
      {loading && !dash ? (
        <div className={styles.statsGrid}>
          {[0,1,2,3].map(i => <div key={i} className={styles.skeleton} style={{ height: 88 }} />)}
        </div>
      ) : error ? (
        <div className={styles.errorBanner}>
          ⚠️ Could not reach the IMD mock server. Run: <code>python d:/FloodGuard/scripts/mock_imd_server.py</code>
        </div>
      ) : (
        <div className={styles.statsGrid}>
          {statsCards.map(c => <StatCard key={c.label} {...c} />)}
        </div>
      )}

      {/* Split grid */}
      {dash && (
        <div className={styles.splitGrid}>
          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelTitle}>
                <ListTodo size={18} style={{ color: 'var(--brand)' }} />
                Active Flood Events
              </h2>
              <button className={styles.viewAll} onClick={() => navigate('/floods')}>View All</button>
            </div>

            {dash.events.length === 0 ? (
              <div className={styles.emptyState}>
                <ShieldCheck size={44} style={{ color: 'var(--success)' }} />
                <strong>No active flood events</strong>
                <span>Conditions are currently safe in {location.label}.</span>
              </div>
            ) : (
              <div className={styles.eventsList}>
                {dash.events.map(evt => <EventItem key={evt.id} event={evt} />)}
              </div>
            )}
          </section>

          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelTitle}>
                <Activity size={18} style={{ color: 'var(--brand)' }} />
                Flood Risk Prediction
              </h2>
              <button className={styles.viewAll} onClick={() => navigate('/predictions')}>
                Next 5 Days ›
              </button>
            </div>

            {dash.predictions.length === 0 ? (
              <p className={styles.noPred}>No forecast data available.</p>
            ) : (
              dash.predictions.map((p, i) => <PredictionRow key={i} {...p} />)
            )}

            <div className={styles.predFooter}>
              <Info size={14} style={{ flexShrink: 0, color: 'var(--text-secondary)' }} />
              <span>Based on IMD Basin QPF data. CWC river levels pending integration.</span>
            </div>
          </section>
        </div>
      )}

      {/* Bottom cards */}
      {dash && (
        <div className={styles.bottomGrid}>
          {bottomCards.map(c => (
            <BottomCard key={c.label} {...c} />
          ))}
        </div>
      )}

    </div>
  );
}
