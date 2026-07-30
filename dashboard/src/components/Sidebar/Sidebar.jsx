import styles from './Sidebar.module.css';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Waves, Bell, LineChart, CloudRain,
  Milestone, FileText, Star, MessageSquareCode,
  Settings, LogOut, Droplets,
} from 'lucide-react';

const NAV = [
  { icon: LayoutDashboard,     label: 'Dashboard',           to: '/' },
  { icon: Waves,               label: 'Current Floods',      to: '/floods' },
  { icon: Bell,                label: 'Alerts',              to: '/alerts' },
  { icon: LineChart,           label: 'Predictions',         to: '/predictions' },
  { icon: CloudRain,           label: 'Weather & Rainfall',  to: '/weather' },
  { icon: Milestone,           label: 'Rivers & Reservoirs', to: '/rivers' },
  { icon: FileText,            label: 'Reports',             to: '/reports' },
  { icon: Star,                label: 'Saved Locations',     to: '/saved' },
  { icon: MessageSquareCode,   label: 'Chat Assistant',      to: '/chat' },
];

export default function Sidebar({ lastUpdated }) {
  const timeStr = lastUpdated
    ? lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : '—';
  const dateStr = lastUpdated
    ? lastUpdated.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
    : '—';

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
        {NAV.map(({ icon: Icon, label, to }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <a href="#" className={styles.navLink} onClick={(e) => e.preventDefault()}>
          <Settings size={18} /><span>Settings</span>
        </a>
        <a href="#" className={styles.navLink} onClick={(e) => e.preventDefault()}>
          <LogOut size={18} /><span>Logout</span>
        </a>
        <div className={styles.lastUpdated}>
          <span className={styles.pulseDot} />
          <span>Last updated: {dateStr}, {timeStr}</span>
        </div>
      </div>
    </aside>
  );
}
