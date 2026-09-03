import { useState, useEffect } from 'react';
import styles from './SavedLocations.module.css';
import { LOCATIONS, POPULAR_LOCATIONS, deriveDashboardData } from '../../data/locations';
import { Star, Trash2, MapPin, Plus } from 'lucide-react';
import toast from 'react-hot-toast';

const STORAGE_KEY = 'floodguard_saved_locations';

export default function SavedLocations({ locationKey, onLocationChange, apiData }) {
  const [saved, setSaved] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? ['hyderabad']; }
    catch { return ['hyderabad']; }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
  }, [saved]);

  const currentLocation = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;
  const dash = deriveDashboardData(apiData, currentLocation);

  const addLocation = (key) => {
    if (saved.includes(key)) { toast('Already saved.', { icon: '⭐' }); return; }
    setSaved(prev => [...prev, key]);
    toast.success(`${LOCATIONS[key]?.label} saved!`);
  };

  const removeLocation = (key) => {
    setSaved(prev => prev.filter(k => k !== key));
    toast(`Removed ${LOCATIONS[key]?.label}`);
  };

  // Attach alert level from current API data when it matches the selected location
  const getAlertInfo = (key) => {
    if (key === locationKey && dash) {
      return { alertLabel: dash.alertLabel, alertSeverity: dash.alertSeverity, rain24h: dash.rain24h };
    }
    return { alertLabel: '—', alertSeverity: 'success', rain24h: null };
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><Star size={22} /> Saved Locations</h1>
        <p className={styles.subtitle}>Your bookmarked areas — live alert levels shown for currently selected location</p>
      </div>

      {/* Saved list */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>My Locations ({saved.length})</h2>
        {saved.length === 0 ? (
          <div className={styles.empty}><Star size={44} /><strong>No saved locations</strong><span>Add locations below to track them.</span></div>
        ) : (
          <div className={styles.savedGrid}>
            {saved.map(key => {
              const loc = LOCATIONS[key];
              if (!loc) return null;
              const { alertLabel, alertSeverity, rain24h } = getAlertInfo(key);
              const isActive = key === locationKey;
              return (
                <div key={key} className={`${styles.savedCard} ${isActive ? styles.activeCard : ''}`}>
                  <div className={styles.cardTop}>
                    <div>
                      <div className={styles.locName}>{loc.label}</div>
                      <div className={styles.locState}>{loc.state}</div>
                    </div>
                    <div className={`${styles.alertBadge} ${styles[alertSeverity]}`}>{alertLabel}</div>
                  </div>
                  <div className={styles.coords}><MapPin size={12} /> {loc.coords}</div>
                  {rain24h != null && (
                    <div className={styles.rain24h}>24h Rainfall: <strong>{rain24h.toFixed(1)} mm</strong></div>
                  )}
                  <div className={styles.cardActions}>
                    <button className={styles.viewBtn} onClick={() => onLocationChange(key)}>
                      View Dashboard
                    </button>
                    <button className={styles.removeBtn} onClick={() => removeLocation(key)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Add more locations */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Add Location</h2>
        <div className={styles.addGrid}>
          {POPULAR_LOCATIONS.filter(l => !saved.includes(l.key)).map(loc => (
            <div key={loc.key} className={styles.addCard}>
              <div>
                <div className={styles.locName}>{loc.label}</div>
                <div className={styles.locState}>{loc.state}</div>
              </div>
              <button className={styles.addBtn} onClick={() => addLocation(loc.key)}>
                <Plus size={14} /> Add
              </button>
            </div>
          ))}
          {POPULAR_LOCATIONS.every(l => saved.includes(l.key)) && (
            <p className={styles.allSaved}>All available locations are saved.</p>
          )}
        </div>
      </section>
    </div>
  );
}
