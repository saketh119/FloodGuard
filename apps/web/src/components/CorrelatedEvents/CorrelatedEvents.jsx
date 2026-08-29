'use client';

import { useState } from 'react';
import styles from './CorrelatedEvents.module.css';
import { useFloodEvents } from '@/hooks/useFloodEvents';
import { getEvent } from '@/lib/api';
import { Layers, ChevronDown, ChevronRight, AlertTriangle, Sparkles } from 'lucide-react';

const STATUS_TONE = {
  active: 'danger', high_risk: 'danger', developing: 'warning',
  potential: 'info', resolved: 'muted',
};

/**
 * Flood events produced by the backend's correlation engine — one row per evolving
 * situation, not per API reading. Expanding a row shows the evidence trail that
 * justifies it, which is the whole point of the correlation design.
 */
export default function CorrelatedEvents() {
  const { events, loading, error } = useFloodEvents();
  const [expanded, setExpanded] = useState(null);
  const [detail, setDetail] = useState({});

  const toggle = async (id) => {
    if (expanded === id) return setExpanded(null);
    setExpanded(id);
    if (!detail[id]) {
      try {
        const full = await getEvent(id);
        setDetail(prev => ({ ...prev, [id]: full }));
      } catch {
        setDetail(prev => ({ ...prev, [id]: { evidence: [], failed: true } }));
      }
    }
  };

  if (error) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}><Layers size={17} /> Correlated Flood Events</h2>
        <div className={styles.errorBox}>
          <AlertTriangle size={15} />
          <span>FloodGuard backend unreachable — {error}. Start the FastAPI service on port 8000.</span>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}><Layers size={17} /> Correlated Flood Events</h2>
      <p className={styles.sectionSub}>
        Multi-source evidence merged into single evolving events by the correlation engine ·
        confidence reflects how many independent IMD signals agree
      </p>

      {loading && <div className={styles.empty}>Loading events…</div>}
      {!loading && events.length === 0 && (
        <div className={styles.empty}>No flood events correlated yet. Trigger a collection cycle with
          <code> POST /api/ingest/run</code>.</div>
      )}

      <div className={styles.list}>
        {events.map(ev => {
          const tone = STATUS_TONE[ev.status] ?? 'info';
          const open = expanded === ev.id;
          const evidence = detail[ev.id]?.evidence ?? [];
          return (
            <div key={ev.id} className={`${styles.card} ${styles[tone]}`}>
              <button className={styles.cardHead} onClick={() => toggle(ev.id)}>
                {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                <div className={styles.headMain}>
                  <span className={styles.district}>{ev.district}</span>
                  <span className={styles.state}>{ev.state}</span>
                  <span className={`${styles.badge} ${styles[tone]}`}>{ev.status.replace('_', ' ')}</span>
                  <span className={styles.sev}>{ev.severity}</span>
                </div>
                <div className={styles.metrics}>
                  <span title="Blended risk score"><b>{ev.risk_score}</b>/100 risk</span>
                  <span title="Evidence agreement">{(ev.confidence_score * 100).toFixed(0)}% confidence</span>
                  {ev.prediction_probability != null && (
                    <span title="ML severe-escalation probability">
                      {(ev.prediction_probability * 100).toFixed(0)}% severe
                    </span>
                  )}
                  <span>{ev.evidence_count} evidence</span>
                </div>
              </button>

              {open && (
                <div className={styles.body}>
                  {ev.ai_summary && (
                    <div className={styles.summary}>
                      <span className={styles.summaryLabel}><Sparkles size={12} /> AI summary</span>
                      <p>{ev.ai_summary}</p>
                    </div>
                  )}
                  <div className={styles.evidenceLabel}>Evidence trail</div>
                  {evidence.length === 0 && <div className={styles.empty}>Loading evidence…</div>}
                  <ul className={styles.evidence}>
                    {evidence.map(e => (
                      <li key={e.id}>
                        <span className={styles.evType}>{e.observation_type}</span>
                        <span className={styles.evReason}>{e.trigger_reason}</span>
                        <span className={styles.evWeight}>+{e.contribution_score}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
