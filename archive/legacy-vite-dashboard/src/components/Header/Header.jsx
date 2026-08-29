import styles from './Header.module.css';
import { Menu, Bell, Moon, Sun, ChevronDown, RefreshCw, Loader2 } from 'lucide-react';

export default function Header({ darkMode, onToggleTheme, loading, onRefresh, location }) {
  const subtitle = location ? `${location.label}, ${location.state}` : 'Real-time flood intelligence and alerts';
  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <button className={styles.iconBtn} aria-label="Menu">
          <Menu size={20} />
        </button>
        <div>
          <h1 className={styles.title}>Dashboard</h1>
          <p className={styles.subtitle}>{subtitle}</p>
        </div>
      </div>

      <div className={styles.right}>
        {/* Manual refresh */}
        <button
          className={styles.iconBtn}
          onClick={onRefresh}
          aria-label="Refresh data"
          title="Refresh data now"
        >
          {loading
            ? <Loader2 size={18} className={styles.spin} />
            : <RefreshCw size={18} />
          }
        </button>

        {/* Notifications */}
        <button className={styles.iconBtn} aria-label="Notifications">
          <Bell size={18} />
          <span className={styles.badge}>3</span>
        </button>

        {/* Theme toggle */}
        <button className={styles.iconBtn} onClick={onToggleTheme} aria-label="Toggle theme">
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User */}
        <div className={styles.user}>
          <div className={styles.avatar}>S</div>
          <span className={styles.username}>Saketh</span>
          <ChevronDown size={14} />
        </div>
      </div>
    </header>
  );
}
