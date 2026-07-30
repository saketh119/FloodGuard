import styles from './PredictionRow.module.css';

export default function PredictionRow({ day, pct, severity, label }) {
  return (
    <div className={styles.row}>
      <span className={styles.day}>{day}</span>
      <span className={`${styles.badge} ${styles[severity]}`}>{label}</span>
      <div className={styles.track}>
        <div
          className={`${styles.fill} ${styles[`fill_${severity}`]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={styles.pct}>{pct}%</span>
    </div>
  );
}
