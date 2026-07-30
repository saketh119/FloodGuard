import { useState, useCallback } from 'react';
import { BrowserRouter } from 'react-router-dom';
import styles from './App.module.css';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';

import Sidebar    from './components/Sidebar/Sidebar';
import Header     from './components/Header/Header';
import AppRouter  from './router/AppRouter';

import { useImdData }  from './hooks/useImdData';
import { LOCATIONS }   from './data/locations';

const POLL_MS = 30_000;

export default function App() {
  const [darkMode,     setDarkMode]     = useState(false);
  const [locationKey,  setLocationKey]  = useState('hyderabad');
  const [prevUpdated,  setPrevUpdated]  = useState(null);

  const location = LOCATIONS[locationKey] ?? LOCATIONS.hyderabad;

  const { data, loading, error, lastUpdated, refresh } = useImdData(location, POLL_MS);

  // Notify on every auto-refresh after the first load
  const handleRefreshed = useCallback(() => {
    if (!lastUpdated) return;
    if (prevUpdated && lastUpdated !== prevUpdated) {
      toast.success('Data refreshed', { id: 'auto-refresh', duration: 2000 });
    }
    setPrevUpdated(lastUpdated);
  }, [lastUpdated, prevUpdated]);

  const toggleTheme = useCallback(() => {
    setDarkMode(prev => {
      const next = !prev;
      document.documentElement.setAttribute('data-theme', next ? 'dark' : 'light');
      return next;
    });
  }, []);

  return (
    <BrowserRouter>
      <div className={styles.shell}>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              fontSize: '13px',
            },
          }}
        />

        <Sidebar lastUpdated={lastUpdated} />

        <div className={styles.body}>
          <Header
            darkMode={darkMode}
            onToggleTheme={toggleTheme}
            loading={loading}
            onRefresh={refresh}
            location={location}
          />
          <main className={styles.content}>
            <AppRouter
              locationKey={locationKey}
              onLocationChange={setLocationKey}
              apiData={data}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
