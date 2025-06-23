// File: src/components/cards/SystemStatus.tsx

import React, { useEffect, useState } from 'react';

export function SystemStatus() {
  const [state, setState] = useState<any>(null);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await fetch('/api/system/runtime');
        const json = await res.json();
        setState(json);
      } catch (e) {
        console.error('Failed to fetch runtime state', e);
      }
    };
    fetchState();
    const interval = setInterval(fetchState, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!state) {
    return <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">Loading system status…</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">⚠️ System Status</h2>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        <strong>Mode:</strong> {state.mode || 'n/a'}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        <strong>Market Status:</strong> {state.marketStatus || 'unknown'}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        <strong>WebSocket:</strong> {state.wsOk ? '✔️ Healthy' : '❌ Stale'}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        <strong>Pivot Detected:</strong> {state.pivotActive ? '✅ Yes' : '—'}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        <strong>Agents Active:</strong> {Array.isArray(state.activeAgents) ? state.activeAgents.join(', ') : '—'}
      </p>
    </div>
  );
}
