import styles from './StatCard.module.css';

/**
 * severity: 'danger' | 'warning' | 'success'
 */
export default function StatCard({ label, value, desc, icon: Icon, severity = 'success' }) {
  return (
    <div className={styles.card}>
      <div className={`${styles.iconWrap} ${styles[severity]}`}>
        <Icon size={20} />
      </div>
      <div className={styles.info}>
        <span className={styles.label}>{label}</span>
        <span className={`${styles.value} ${styles[`val_${severity}`]}`}>{value}</span>
        <span className={styles.desc}>{desc}</span>
      </div>
    </div>
  );
}
