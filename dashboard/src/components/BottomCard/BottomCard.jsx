import styles from './BottomCard.module.css';
import { ChevronRight } from 'lucide-react';

export default function BottomCard({ label, value, desc, descColor, icon: Icon, severity, clickable, onClick }) {
  return (
    <div className={`${styles.card} ${clickable || onClick ? styles.clickable : ''}`} onClick={onClick}>
      <div className={styles.left}>
        <span className={styles.label}>{label}</span>
        <span className={styles.value}>{value}</span>
        <span className={styles.desc} style={{ color: descColor }}>{desc}</span>
      </div>
      <div className={`${styles.iconWrap} ${styles[severity]}`}>
        <Icon size={22} />
      </div>
      {clickable && <ChevronRight size={16} className={styles.chevron} />}
    </div>
  );
}
