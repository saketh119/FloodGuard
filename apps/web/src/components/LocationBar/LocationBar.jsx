'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { MapPin, Search, LocateFixed, Loader2, Plus, Globe } from 'lucide-react';
import toast from 'react-hot-toast';

import { useFloodGuard } from '@/context/FloodGuardContext';
import { reverseLookup, searchPlaces, trackPlace } from '@/lib/api';
import styles from './LocationBar.module.css';

const SEARCH_DEBOUNCE_MS = 350;

/**
 * Location picker.
 *
 * Two tiers, deliberately distinguished. Followed locations resolve instantly from the
 * backend registry. Anything else is geocoded on demand and can be added — those get
 * live weather but no IMD warnings, so the UI labels them rather than showing empty
 * IMD panels and letting the user assume the data is merely late.
 */
export default function LocationBar() {
  const { districts, district, setDistrict, location, dash, reloadDistricts } = useFloodGuard();
  const [query, setQuery] = useState('');
  const [remote, setRemote] = useState([]);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(null);
  const [locating, setLocating] = useState(false);
  const debounceRef = useRef(null);

  const followed = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return districts
      .filter(d => d.district.toLowerCase().includes(q) || (d.state ?? '').toLowerCase().includes(q))
      .slice(0, 5);
  }, [query, districts]);

  // Geocode anything we are not already following, debounced so typing does not
  // fire a request per keystroke.
  useEffect(() => {
    const q = query.trim();
    clearTimeout(debounceRef.current);
    if (q.length < 2) { setRemote([]); setSearching(false); return; }

    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchPlaces(q);
        const known = new Set(districts.map(d => d.district.toLowerCase()));
        setRemote(results.filter(r => !known.has((r.name ?? '').toLowerCase())));
      } catch {
        setRemote([]);          // search unavailable: followed locations still work
      } finally {
        setSearching(false);
      }
    }, SEARCH_DEBOUNCE_MS);

    return () => clearTimeout(debounceRef.current);
  }, [query, districts]);

  const choose = (name) => {
    setDistrict(name);
    setQuery('');
    setRemote([]);
    toast.success(`Now viewing ${name}`);
  };

  const addPlace = async (place) => {
    setAdding(place.label);
    try {
      await trackPlace({
        district: place.name, state: place.state,
        latitude: place.latitude, longitude: place.longitude, country: place.country,
      });
      await reloadDistricts?.();
      choose(place.name);
      toast.success(`Now following ${place.name} — live weather available shortly`);
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? `Could not add ${place.name}`);
    } finally {
      setAdding(null);
    }
  };

  /**
   * Resolve the browser's actual position.
   *
   * The previous version picked the nearest ALREADY-FOLLOWED location, which reported
   * Kerala to someone standing in Telangana — the closest known point, and wrong. Now
   * the coordinates are reverse-geocoded to whatever place is really there, and that
   * place is followed if we are not already following it.
   */
  const useMyLocation = () => {
    if (!navigator.geolocation) {
      return toast.error('Geolocation is not available in this browser');
    }

    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        const { latitude, longitude } = coords;
        try {
          const place = await reverseLookup(latitude, longitude);

          const known = districts.find(
            d => d.district.toLowerCase() === (place.name ?? '').toLowerCase(),
          );
          if (known) {
            choose(known.district);
          } else {
            await trackPlace({
              district: place.name, state: place.state,
              latitude, longitude, country: place.country,
            });
            await reloadDistricts?.();
            choose(place.name);
          }
          toast.success(`Located: ${place.label}`);
        } catch (err) {
          const detail = err?.response?.data?.detail;
          toast.error(
            typeof detail === 'string'
              ? detail
              : 'Could not identify your location — try searching for it by name',
          );
        } finally {
          setLocating(false);
        }
      },
      (err) => {
        const reasons = {
          1: 'Location permission denied — allow it in your browser, or search by name',
          2: 'Your position is unavailable right now',
          3: 'Timed out getting your position',
        };
        toast.error(reasons[err?.code] ?? 'Could not read your location');
        setLocating(false);
      },
      { timeout: 12_000, enableHighAccuracy: true, maximumAge: 60_000 },
    );
  };

  const current = districts.find(d => d.district === district);
  const showResults = query.trim().length > 0;

  return (
    <section className={styles.wrap}>
      <div className={styles.searchRow}>
        <label className={styles.label} htmlFor="place-search">Location</label>
        <div className={styles.searchBox}>
          <Search size={16} className={styles.searchIcon} />
          <input
            id="place-search"
            className={styles.input}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search any city or district in India…"
            autoComplete="off"
          />
          <button className={styles.locateBtn} onClick={useMyLocation} disabled={locating}>
            {locating ? <Loader2 size={15} className={styles.spin} /> : <LocateFixed size={15} />}
            <span>Use my location</span>
          </button>
        </div>

        {showResults && (
          <ul className={styles.results}>
            {followed.map(d => (
              <li key={d.id}>
                <button className={styles.resultBtn} onClick={() => choose(d.district)}>
                  <MapPin size={14} />
                  <span>{d.label}</span>
                  <em>{d.imd ? 'IMD + live weather' : 'live weather'}</em>
                </button>
              </li>
            ))}

            {remote.length > 0 && (
              <li className={styles.resultsDivider}>
                <Globe size={11} /> Not followed yet — add to start collecting
              </li>
            )}
            {remote.map(place => (
              <li key={`${place.label}-${place.latitude}`}>
                <button
                  className={styles.resultBtn}
                  onClick={() => addPlace(place)}
                  disabled={adding === place.label}
                >
                  {adding === place.label
                    ? <Loader2 size={14} className={styles.spin} />
                    : <Plus size={14} />}
                  <span>{place.label}</span>
                  <em>live weather only</em>
                </button>
              </li>
            ))}

            {searching && followed.length === 0 && remote.length === 0 && (
              <li className={styles.resultsHint}>Searching…</li>
            )}
            {!searching && followed.length === 0 && remote.length === 0 && (
              <li className={styles.resultsHint}>No places found for “{query.trim()}”.</li>
            )}
          </ul>
        )}
      </div>

      <div className={styles.activeBar}>
        <MapPin size={17} />
        <div className={styles.activeText}>
          <span className={styles.activeName}>
            {location?.district}{location?.state ? `, ${location.state}` : ''}
          </span>
          <span className={styles.activeCoords}>{current?.coords ?? '—'}</span>
        </div>
        {current && !current.imd && (
          <span className={styles.liveOnly} title="IMD warnings and district rainfall are not available here">
            Live weather only
          </span>
        )}
        {dash && (
          <span className={`${styles.activeAlert} ${styles[dash.alertSeverity]}`}>
            {dash.alertColorName} · {dash.activeEvents} active
          </span>
        )}
      </div>

      <div className={styles.quickRow}>
        {districts.slice(0, 8).map(d => (
          <button
            key={d.id}
            className={`${styles.chip} ${d.district === district ? styles.chipActive : ''}`}
            onClick={() => choose(d.district)}
          >
            {d.district}
          </button>
        ))}
      </div>
    </section>
  );
}
