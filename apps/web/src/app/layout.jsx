import { Toaster } from 'react-hot-toast';

import { FloodGuardProvider } from '@/context/FloodGuardContext';
import Sidebar from '@/components/Sidebar/Sidebar';
import Header from '@/components/Header/Header';
import styles from './App.module.css';
import './globals.css';

export const metadata = {
  title: 'FloodGuard — Flood Intelligence Platform',
  description:
    'AI-powered flood intelligence: IMD ingestion, event correlation, ML risk scoring '
    + 'and RAG-grounded guidance from NDMA and IMD publications.',
};

export const viewport = { width: 'device-width', initialScale: 1 };

/**
 * Root layout. The sidebar, header and data provider are mounted once here and
 * persist across navigations — switching pages does not re-fetch the district.
 */
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <FloodGuardProvider>
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
            <Sidebar />
            <div className={styles.body}>
              <Header />
              <main className={styles.content}>{children}</main>
            </div>
          </div>
        </FloodGuardProvider>
      </body>
    </html>
  );
}
