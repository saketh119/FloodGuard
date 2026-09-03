'use client';

import { useFloodGuard } from '@/context/FloodGuardContext';
import { useRouter } from 'next/navigation';
import styles from './Dashboard.module.css';
import LocationBar from '@/components/LocationBar/LocationBar';
import StatCard from '@/components/StatCard/StatCard';
import EventItem from '@/components/EventItem/EventItem';
import PredictionRow from '@/components/PredictionRow/PredictionRow';
import BottomCard from '@/components/BottomCard/BottomCard';

import {
  AlertTriangle, Waves, CloudRain, TrendingUp, TrendingDown, Minus, CloudLightning, Droplets, Database, Info, ShieldCheck, ListTodo, Activity,
} from 'lucide-react';

export default function Dashboard() {
  const { dash, loading, error, location } = useFloodGuard();
  const router = useRouter();

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
      label: 'Conditions Now',
      value: dash.liveTemp != null ? `${Math.round(dash.liveTemp)}°C` : `${dash.temp}°C`,
      desc: dash.liveConditions
        ? `${dash.liveConditions}${dash.liveHumidity != null ? ` · ${Math.round(dash.liveHumidity)}% RH` : ''}`
        : dash.wxDesc,
      descColor: 'var(--brand)',
      icon: CloudLightning,
      severity: 'brand',
      live: dash.isLive,
      clickable: true,
      onClick: () => router.push('/weather'),
    },
    {
      label: `River Level (${(location.basin ? `${location.basin} basin` : 'river basin')})`,
      value: dash.riverLevelValue,
      desc: dash.riverLevelProxy,
      descColor: `var(--${dash.riverSeverity})`,
      icon: Droplets,
      severity: dash.riverSeverity,
      clickable: true,
      onClick: () => router.push('/rivers'),
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
      label: 'Rain Forecast (24h)',
      value: dash.forecast24hMm != null ? `${dash.forecast24hMm.toFixed(1)} mm` : '—',
      desc: dash.forecast72hMm != null ? `${dash.forecast72hMm.toFixed(0)} mm over 72h` : 'Awaiting forecast',
      descColor: dash.forecast24hMm > 64.5 ? 'var(--danger)'
        : dash.forecast24hMm > 15 ? 'var(--warning)' : 'var(--text-secondary)',
      icon: CloudRain,
      severity: dash.forecast24hMm > 64.5 ? 'danger'
        : dash.forecast24hMm > 15 ? 'warning' : 'success',
      live: dash.isLive,
      clickable: true,
      onClick: () => router.push('/predictions'),
    },
  ] : [];

  return (
    <div className={styles.page}>

      <LocationBar />

      {/* Stats row */}
      {loading && !dash ? (
        <div className={styles.statsGrid}>
          {[0,1,2,3].map(i => <div key={i} className={styles.skeleton} style={{ height: 88 }} />)}
        </div>
      ) : error ? (
        <div className={styles.errorBanner}>
          <AlertTriangle size={15} />
          <span>Live data unavailable — the ingestion service is not responding. Showing no figures rather than stale ones.</span>
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
              <button className={styles.viewAll} onClick={() => router.push('/floods')}>View All</button>
            </div>

            {dash.events.length === 0 ? (
              <div className={styles.emptyState}>
                <ShieldCheck size={44} style={{ color: 'var(--success)' }} />
                <strong>No active flood events</strong>
                <span>Conditions are currently safe in {location.district}.</span>
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
              <button className={styles.viewAll} onClick={() => router.push('/predictions')}>
                Next 5 Days ›
              </button>
            </div>

            {dash.predictions.length === 0 ? (
              <p className={styles.noPred}>No forecast available yet — the next collection cycle will populate this.</p>
            ) : (
              dash.predictions.map(p => <PredictionRow key={p.iso} {...p} />)
            )}

            <div className={styles.predFooter}>
              <Info size={14} style={{ flexShrink: 0, color: 'var(--text-secondary)' }} />
              <span>Rainfall forecast from OpenWeather, combined with IMD basin QPF where the district is covered. River gauge levels are estimated from rainfall until CWC telemetry is connected.</span>
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
