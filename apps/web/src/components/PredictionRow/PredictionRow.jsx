'use client';

import styles from './PredictionRow.module.css';

/**
 * One day of the five-day risk strip.
 *
 * The rainfall figure is shown alongside the percentage because the percentage is a
 * derived index — a reader needs the millimetres to judge it. `source` records which
 * feed the number came from, which differs by location: IMD basin QPF only exists for
 * districts IMD covers, OpenWeather works everywhere.
 */
export default function PredictionRow({ day, pct, severity, label, mm, source }) {
  return (
    <div className={styles.row}>
      <span className={styles.day}>{day}</span>
      <span className={`${styles.badge} ${styles[severity]}`}>{label}</span>

      <div className={styles.meter}>
        <div className={styles.track}>
          <div
            className={`${styles.fill} ${styles[`fill_${severity}`]}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        {mm != null && (
          <span className={styles.mm} title={source ? `Source: ${source}` : undefined}>
            {mm} mm expected
          </span>
        )}
      </div>

      <span className={styles.pct}>{pct}%</span>
    </div>
  );
}
