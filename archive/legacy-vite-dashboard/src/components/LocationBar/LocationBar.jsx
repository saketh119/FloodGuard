import { useState } from 'react';
import styles from './LocationBar.module.css';
import { Search, MapPin, Navigation, Loader2 } from 'lucide-react';
import { POPULAR_LOCATIONS, nearestLocation } from '../../data/locations';
import toast from 'react-hot-toast';

async function reverseGeocode(lat, lng) {
  const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`;
  const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
  if (!res.ok) throw new Error('Reverse geocode failed');
  return res.json();
}

export default function LocationBar({ selected, onSelect }) {
  const [geoLoading, setGeoLoading] = useState(false);

  const handleTagClick = (e, key) => {
    e.preventDefault();
    onSelect(key);
  };

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim().toLowerCase();
      const match = POPULAR_LOCATIONS.find(
        l => l.key === q || l.label.toLowerCase().includes(q)
      );
      if (match) {
        onSelect(match.key);
        e.target.value = '';
      } else {
        toast.error(`Location "${e.target.value}" not found. Try one of the popular options.`);
      }
    }
  };

  const handleShareLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser.');
      return;
    }

    setGeoLoading(true);
    const toastId = toast.loading('Detecting your location…');

    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const { lat, lng } = { lat: coords.latitude, lng: coords.longitude };

          // Find nearest registered location
          const nearest = nearestLocation(lat, lng);

          // Reverse geocode for display name
          let displayName = nearest?.label ?? 'your area';
          try {
            const geo = await reverseGeocode(lat, lng);
            const city = geo.address?.city || geo.address?.town || geo.address?.county || geo.address?.state_district;
            if (city) displayName = city;
          } catch {
            // Nominatim failed — use nearest label as fallback
          }

          toast.success(`Located: ${displayName} → showing ${nearest.label}`, { id: toastId });
          onSelect(nearest.key);
        } catch (err) {
          toast.error('Could not determine your location.', { id: toastId });
        } finally {
          setGeoLoading(false);
        }
      },
      (err) => {
        setGeoLoading(false);
        const msg = err.code === 1
          ? 'Location access denied. Please allow location in your browser.'
          : 'Could not get your position.';
        toast.error(msg, { id: toastId });
      },
      { timeout: 10000, maximumAge: 60000 }
    );
  };

  return (
    <section className={styles.wrapper}>
      {/* Search box */}
      <div className={styles.searchBox}>
        <h2 className={styles.heading}>Select Location</h2>
        <p className={styles.subheading}>Search by location or share your current location</p>
        <div className={styles.inputWrap}>
          <Search size={16} className={styles.searchIcon} />
          <input
            className={styles.input}
            placeholder="Search for city, district, river, or station…"
            onKeyDown={handleSearch}
          />
        </div>
        <div className={styles.tags}>
          <span className={styles.tagLabel}>Popular:</span>
          {POPULAR_LOCATIONS.map(loc => (
            <a
              key={loc.key}
              href="#"
              className={`${styles.tag} ${selected.key === loc.key ? styles.tagActive : ''}`}
              onClick={(e) => handleTagClick(e, loc.key)}
            >
              {loc.label}
            </a>
          ))}
        </div>
      </div>

      <div className={styles.divider}>or</div>

      {/* Use my location */}
      <div className={styles.locBox}>
        <MapPin size={28} className={styles.locIcon} />
        <div>
          <p className={styles.locTitle}>Use My Location</p>
          <p className={styles.locDesc}>Share your current location to get localized flood insights</p>
        </div>
        <button
          className={styles.shareBtn}
          onClick={handleShareLocation}
          disabled={geoLoading}
        >
          {geoLoading
            ? <Loader2 size={14} className={styles.spin} />
            : <Navigation size={14} />
          }
          {geoLoading ? 'Locating…' : 'Share Location'}
        </button>
      </div>
    </section>
  );
}
