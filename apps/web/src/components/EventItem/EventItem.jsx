'use client';

import styles from './EventItem.module.css';
import { Clock, ChevronRight, CloudLightning, CloudRain, Wind, ShieldAlert, Waves, AlertTriangle } from 'lucide-react';

const ICON_MAP = {
  'cloud-lightning': CloudLightning,
  'cloud-rain':      CloudRain,
  'wind':            Wind,
  'shield-alert':    ShieldAlert,
  'waves':           Waves,
  'alert-triangle':  AlertTriangle,
};

export default function EventItem({ event }) {
  const Icon = ICON_MAP[event.icon] ?? AlertTriangle;
  const sev  = event.severity; // 'danger' | 'warning' | 'success'

  return (
    <div className={styles.item}>
      <div className={styles.left}>
        <div className={`${styles.iconCircle} ${styles[sev]}`}>
          <Icon size={18} />
        </div>
        <div className={styles.details}>
          <div className={styles.titleRow}>
            <span className={styles.title}>{event.title}</span>
            <span className={`${styles.badge} ${styles[sev]}`}>
              {sev === 'danger' ? 'High' : sev === 'warning' ? 'Medium' : 'Low'}
            </span>
          </div>
          <span className={styles.subtitle}>{event.subtitle}</span>
          <span className={styles.time}>
            <Clock size={11} />
            Started: {event.started}
          </span>
        </div>
      </div>
      <div className={styles.right}>
        <div className={styles.metric}>
          <span className={styles.metricVal}>{event.metric}</span>
          <span className={styles.metricLbl}>{event.metricLabel}</span>
        </div>
        <ChevronRight size={16} className={styles.chevron} />
      </div>
    </div>
  );
}
