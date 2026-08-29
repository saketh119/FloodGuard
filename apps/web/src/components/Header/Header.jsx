'use client';

import { usePathname } from 'next/navigation';
import { Menu, Bell, Moon, Sun, RefreshCw, Loader2, Radio } from 'lucide-react';

import { useFloodGuard } from '@/context/FloodGuardContext';
import styles from './Header.module.css';

const TITLES = {
  '/': 'Operations Overview',
  '/floods': 'Current Floods',
  '/alerts': 'Alerts',
  '/predictions': 'Risk Predictions',
  '/weather': 'Weather & Rainfall',
  '/rivers': 'Rivers & Reservoirs',
  '/reports': 'Reports',
  '/saved': 'Saved Locations',
  '/chat': 'Assistant',
};

/** "12s ago" / "4m ago" — an absolute clock time does not convey staleness. */
function ago(then, now) {
  if (!then) return null;
  const s = Math.max(0, Math.round((now - then) / 1000));
  if (s < 10) return 'just now';
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

export default function Header() {
  const pathname = usePathname();
  const {
    darkMode, toggleTheme, loading, refresh, location, dash,
    lastUpdated, now, connected, alertCount,
  } = useFloodGuard();

  const title = TITLES[pathname] ?? 'FloodGuard';
  const subtitle = location?.state
    ? `${location.district}, ${location.state}`
    : 'Select a district to begin';

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <button className={styles.iconBtn} aria-label="Toggle navigation">
          <Menu size={20} />
        </button>
        <div>
          <h1 className={styles.title}>{title}</h1>
          <p className={styles.subtitle}>{subtitle}</p>
        </div>
      </div>

      <div className={styles.right}>
        {/* Connection state replaces the decorative user chip: on an operations
            console, whether the feed is live is the thing worth a permanent slot. */}
        <div
          className={`${styles.feed} ${connected ? styles.feedLive : styles.feedStale}`}
          title={connected
            ? 'Streaming live updates from the ingestion pipeline'
            : 'Live stream disconnected — falling back to periodic polling'}
        >
          <Radio size={13} className={connected ? styles.pulse : undefined} />
          <span className={styles.feedLabel}>{connected ? 'Live' : 'Reconnecting'}</span>
          {lastUpdated && <span className={styles.feedAgo}>· {ago(lastUpdated, now)}</span>}
        </div>

        <button
          className={styles.iconBtn}
          onClick={refresh}
          aria-label="Refresh now"
          title="Refresh now"
        >
          {loading ? <Loader2 size={18} className={styles.spin} /> : <RefreshCw size={18} />}
        </button>

        <button
          className={styles.iconBtn}
          aria-label={`${alertCount} active alert${alertCount === 1 ? '' : 's'}`}
          title={`${alertCount} active alert${alertCount === 1 ? '' : 's'} in ${location?.district ?? 'this district'}`}
        >
          <Bell size={18} />
          {alertCount > 0 && <span className={styles.badge}>{alertCount}</span>}
        </button>

        <button
          className={styles.iconBtn}
          onClick={toggleTheme}
          aria-label={darkMode ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}
