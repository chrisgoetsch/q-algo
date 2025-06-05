import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import Dashboard from '@/pages/Dashboard';

/**
 * Root application component.
 * Wraps the router in an ErrorBoundary so any uncaught
 * render/runtime error in child trees shows a friendly fallback UI.
 */
export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          {/* (Add more routes here as the app grows) */}
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
