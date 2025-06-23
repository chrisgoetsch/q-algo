// File: src/components/cards/ControlPanel.tsx

import React, { useState, useEffect } from 'react';

export function ControlPanel() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      const json = await res.json();
      setStatus(json);
    } catch (e) {
      console.error('Error loading control status:', e);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (updates: any) => {
    const next = { ...status, ...updates };
    setStatus(next);
    await fetch('/api/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(next),
    });
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading || !status) {
    return <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">Loading Controls…</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">🕹️ Control Panel</h2>

      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-800 dark:text-gray-100">Kill Switch</span>
        <button
          onClick={() => updateStatus({ killSwitch: !status.killSwitch })}
          className={`px-3 py-1 rounded font-medium transition text-white ${
            status.killSwitch ? 'bg-red-500' : 'bg-green-500'
          }`}
        >
          {status.killSwitch ? 'OFF' : 'ON'}
        </button>
      </div>

      <div className="mb-4">
        <label className="block text-gray-800 dark:text-gray-100 mb-1">
          Capital Allocation: <strong>{status.capitalAllocation}%</strong>
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={status.capitalAllocation}
          onChange={(e) => updateStatus({ capitalAllocation: +e.target.value })}
          className="w-full"
        />
      </div>

      <div>
        <button
          onClick={() => updateStatus({ overrideEntry: true })}
          className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg shadow"
        >
          🔁 Trigger Manual Entry Override
        </button>
      </div>
    </div>
  );
}
