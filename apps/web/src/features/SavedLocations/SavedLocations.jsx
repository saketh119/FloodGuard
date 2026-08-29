'use client';

import { useEffect, useState } from 'react';
import { Star, StarOff, MapPin, Plus, Eye } from 'lucide-react';
import toast from 'react-hot-toast';

import { useFloodGuard } from '@/context/FloodGuardContext';
import styles from './SavedLocations.module.css';

const STORAGE_KEY = 'floodguard.saved';

/**
 * Saved locations. Persisted per-browser in localStorage — there is no user account
 * layer yet, and every access is guarded because storage throws in some privacy modes.
 */
export default function SavedLocations() {
  const { districts, district, setDistrict, dash } = useFloodGuard();
  const [saved, setSaved] = useState([]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) setSaved(JSON.parse(raw));
    } catch { /* start with an empty list */ }
  }, []);

  const persist = (next) => {
    setSaved(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      toast.error('Could not save — browser storage is unavailable');
    }
  };

  const add = (name) => {
    if (saved.includes(name)) return;
    persist([...saved, name]);
    toast.success(`${name} added to your locations`);
  };

  const remove = (name) => {
    persist(saved.filter(n => n !== name));
    toast(`Removed ${name}`);
  };

  const savedDistricts = districts.filter(d => saved.includes(d.district));
  const unsaved = districts.filter(d => !saved.includes(d.district));

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><Star size={22} /> Saved Locations</h1>
        <p className={styles.subtitle}>
          Districts you follow · stored in this browser only
        </p>
      </div>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Your Locations</h2>
        {savedDistricts.length === 0 && (
          <div className={styles.empty}>
            No saved locations yet — add one from the list below.
          </div>
        )}
        <div className={styles.grid}>
          {savedDistricts.map(d => {
            const isActive = d.district === district;
            return (
              <div key={d.id} className={`${styles.card} ${isActive ? styles.cardActive : ''}`}>
                <div className={styles.cardHead}>
                  <MapPin size={16} />
                  <div>
                    <div className={styles.cardName}>{d.district}</div>
                    <div className={styles.cardMeta}>{d.state} · {d.basin} basin</div>
                  </div>
                  <button
                    className={styles.starBtn}
                    onClick={() => remove(d.district)}
                    aria-label={`Remove ${d.district}`}
                    title="Remove"
                  >
                    <StarOff size={16} />
                  </button>
                </div>

                {/* Live figures are only available for the district currently loaded —
                    showing another district's numbers would mean fetching all of them. */}
                {isActive && dash ? (
                  <div className={styles.cardStats}>
                    <span className={`${styles.alertPill} ${styles[dash.alertSeverity]}`}>
                      {dash.alertColorName}
                    </span>
                    <span>{dash.activeEvents} active</span>
                    <span>{dash.rain24h?.toFixed(1) ?? '—'} mm / 24h</span>
                  </div>
                ) : (
                  <div className={styles.cardStats}>
                    <span className={styles.muted}>Open to load live data</span>
                  </div>
                )}

                <button className={styles.viewBtn} onClick={() => setDistrict(d.district)}>
                  <Eye size={14} /> {isActive ? 'Currently viewing' : 'View dashboard'}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Available Districts</h2>
        <p className={styles.sectionSub}>Served by the platform&apos;s district registry</p>
        <div className={styles.chips}>
          {unsaved.map(d => (
            <button key={d.id} className={styles.chip} onClick={() => add(d.district)}>
              <Plus size={13} /> {d.label}
            </button>
          ))}
          {unsaved.length === 0 && districts.length > 0 && (
            <span className={styles.muted}>Every covered district is saved.</span>
          )}
          {districts.length === 0 && (
            <span className={styles.muted}>District registry unavailable — is the API running?</span>
          )}
        </div>
      </section>
    </div>
  );
}
