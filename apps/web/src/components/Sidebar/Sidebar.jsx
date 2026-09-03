'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Waves, Bell, LineChart, CloudRain,
  Milestone, FileText, Star, MessageSquareCode, Droplets,
} from 'lucide-react';

import { useFloodGuard } from '@/context/FloodGuardContext';
import styles from './Sidebar.module.css';

const NAV = [
  { icon: LayoutDashboard,   label: 'Dashboard',           href: '/' },
  { icon: Waves,             label: 'Current Floods',      href: '/floods' },
  { icon: Bell,              label: 'Alerts',              href: '/alerts' },
  { icon: LineChart,         label: 'Predictions',         href: '/predictions' },
  { icon: CloudRain,         label: 'Weather & Rainfall',  href: '/weather' },
  { icon: Milestone,         label: 'Rivers & Reservoirs', href: '/rivers' },
  { icon: FileText,          label: 'Reports',             href: '/reports' },
  { icon: Star,              label: 'Saved Locations',     href: '/saved' },
  { icon: MessageSquareCode, label: 'Chat Assistant',      href: '/chat' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { health, alertCount } = useFloodGuard();

  // Which upstreams are actually live. Stating that IMD is a mock, rather than
  // letting the numbers imply they are real, is the honest thing to show here.
  const sources = health?.sources;
  const feeds = sources ? [
    { name: 'OpenWeather', live: sources.openweather?.configured, note: 'observed' },
    { name: 'IMD', live: false, note: 'mock' },
    { name: 'CWC', live: false, note: 'pending' },
  ] : [];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <Droplets className={styles.brandIcon} />
        <div>
          <div className={styles.brandName}>Flood Intelligence</div>
          <div className={styles.brandSub}>Platform</div>
        </div>
      </div>

      <nav className={styles.nav}>
        {NAV.map(({ icon: Icon, label, href }) => {
          // '/' must match exactly, everything else matches its subtree.
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`${styles.navLink} ${active ? styles.active : ''}`}
              aria-current={active ? 'page' : undefined}
            >
              <Icon size={18} />
              <span>{label}</span>
              {href === '/alerts' && alertCount > 0 && (
                <span className={styles.navBadge}>{alertCount}</span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className={styles.footer}>
        <div className={styles.feedsLabel}>Data sources</div>
        <ul className={styles.feeds}>
          {feeds.map(f => (
            <li key={f.name} className={styles.feedRow}>
              <span className={`${styles.feedDot} ${f.live ? styles.dotLive : styles.dotIdle}`} />
              <span className={styles.feedName}>{f.name}</span>
              <span className={styles.feedNote}>{f.live ? f.note : f.note}</span>
            </li>
          ))}
          {feeds.length === 0 && <li className={styles.feedRow}><span className={styles.feedNote}>connecting…</span></li>}
        </ul>
      </div>
    </aside>
  );
}
