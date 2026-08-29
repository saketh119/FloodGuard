'use client';

import styles from './BottomCard.module.css';
import { ChevronRight } from 'lucide-react';

export default function BottomCard({
  label, value, desc, descColor, icon: Icon, severity, clickable, onClick, live,
}) {
  const interactive = Boolean(clickable || onClick);

  const content = (
    <>
      <div className={styles.left}>
        <span className={styles.label}>
          {label}
          {/* Marks figures sourced from a real live feed rather than the IMD mock. */}
          {live && <span className={styles.liveTag} title="Live observed reading">LIVE</span>}
        </span>
        <span className={styles.value}>{value}</span>
        <span className={styles.desc} style={{ color: descColor }}>{desc}</span>
      </div>
      <div className={`${styles.iconWrap} ${styles[severity]}`}>
        <Icon size={22} />
      </div>
      {interactive && <ChevronRight size={16} className={styles.chevron} />}
    </>
  );

  // A card that navigates is a button, not a div — it must be keyboard reachable.
  return interactive ? (
    <button type="button" className={`${styles.card} ${styles.clickable}`} onClick={onClick}>
      {content}
    </button>
  ) : (
    <div className={styles.card}>{content}</div>
  );
}
