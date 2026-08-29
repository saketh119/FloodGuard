'use client';

import { useFloodGuard } from '@/context/FloodGuardContext';
import styles from './CurrentFloods.module.css';
import { useRouter } from 'next/navigation';
import { COLOR_SEVERITY } from '@/lib/derive';
import EventItem from '@/components/EventItem/EventItem';
import { Waves, Filter, ShieldCheck, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import CorrelatedEvents from '@/components/CorrelatedEvents/CorrelatedEvents';

const FILTERS = ['All', 'High', 'Medium', 'Low'];

export default function CurrentFloods() {
  const { dash, loading, error, refresh, location } = useFloodGuard();
  const [filter, setFilter] = useState('All');

  const allEvents = dash?.events ?? [];
  const filtered  = filter === 'All' ? allEvents : allEvents.filter(e => {
    const sev = e.severity;
    if (filter === 'High')   return sev === 'danger';
    if (filter === 'Medium') return sev === 'warning';
    if (filter === 'Low')    return sev === 'success';
    return true;
  });

  // 5-day district warnings as separate cards
  const dayColors  = dash?.dayColors ?? [1,1,1,1,1];
  const dayCodes   = dash?.dayCodes  ?? [];
  const COLOR_NAME = { 1:'Green', 2:'Yellow', 3:'Orange', 4:'Red' };
  const WARNING_CODE_MAP = {
    1: 'No Warning', 2: 'Heavy Rain', 3: 'Very Heavy Rain', 4: 'Thunderstorm & Lightning',
    5: 'Strong Wind', 6: 'Cold Wave', 9: 'Heat Wave', 12: 'Hailstorm',
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.title}><Waves size={22} /> Current Floods</h1>
          <p className={styles.subtitle}>Live flood events derived from IMD nowcast and rainfall thresholds — {location.district}, {location.state}</p>
        </div>
        <button className={styles.refreshBtn} onClick={refresh}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {/* Summary strip */}
      <div className={styles.summaryStrip}>
        <div className={styles.summaryItem}>
          <span className={styles.summaryVal} style={{ color: `var(--${dash?.alertSeverity ?? 'success'})` }}>
            {dash?.alertLabel ?? '—'}
          </span>
          <span className={styles.summaryLbl}>Alert Level</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryVal}>{allEvents.length}</span>
          <span className={styles.summaryLbl}>Active Events</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryVal}>{dash?.rain24h?.toFixed(1) ?? '—'} mm</span>
          <span className={styles.summaryLbl}>24h Rainfall</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryVal}>{dash?.nowcastMsg ? 'Active' : 'Clear'}</span>
          <span className={styles.summaryLbl}>Nowcast Status</span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className={styles.filterRow}>
        <Filter size={15} style={{ color: 'var(--text-secondary)' }} />
        {FILTERS.map(f => (
          <button
            key={f}
            className={`${styles.filterBtn} ${filter === f ? styles.filterActive : ''}`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
        <span className={styles.count}>{filtered.length} event{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Event List */}
      {loading && !dash ? (
        <div className={styles.skeletonList}>
          {[0,1,2].map(i => <div key={i} className={styles.skeleton} />)}
        </div>
      ) : error ? (
        <div className={styles.error}>Live data unavailable — the ingestion service is not responding.</div>
      ) : filtered.length === 0 ? (
        <div className={styles.empty}>
          <ShieldCheck size={52} style={{ color: 'var(--success)' }} />
          <strong>No {filter !== 'All' ? filter.toLowerCase() + ' severity ' : ''}events found</strong>
          <span>Conditions are currently safe in {location.district}.</span>
        </div>
      ) : (
        <div className={styles.eventList}>
          {filtered.map(evt => <EventItem key={evt.id} event={evt} />)}
        </div>
      )}

      {/* Nowcast message */}
      {dash?.nowcastMsg && (
        <div className={styles.nowcastCard}>
          <strong>📡 IMD Nowcast Message</strong>
          <p>{dash.nowcastMsg}</p>
          <span>Issued for: {dash.nowcastStation} · Valid until: {dash.warn?.Vupto ?? '—'}</span>
        </div>
      )}

      {/* 5-Day Warning Grid */}
      <section className={styles.warningSection}>
        <h2 className={styles.sectionTitle}>5-Day District Warning Forecast</h2>
        <div className={styles.warningGrid}>
          {[1,2,3,4,5].map(d => {
            const col = dayColors[d-1] ?? 1;
            const codes = dayCodes[d-1] ?? [1];
            const sev = COLOR_SEVERITY[col] ?? 'success';
            const colName = COLOR_NAME[col] ?? 'Green';
            return (
              <div key={d} className={`${styles.warningCard} ${styles[sev]}`}>
                <div className={styles.warningDay}>Day {d}</div>
                <div className={styles.warningColor}>{colName} Alert</div>
                <div className={styles.warningCodes}>
                  {codes.map(c => <span key={c} className={styles.warnCode}>{WARNING_CODE_MAP[c] ?? `Code ${c}`}</span>)}
                </div>
              </div>
            );
          })}
        </div>
      </section>
      <CorrelatedEvents />

    </div>
  );
}
