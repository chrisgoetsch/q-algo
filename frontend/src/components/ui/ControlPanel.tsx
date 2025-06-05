// ──────────────────────────────────────────────────────────────────────────
// src/components/controls/ControlPanel.tsx

import React from 'react';
import useStatus from '../../hooks/useStatus';
import OverrideButton from '../controls/OverrideButton';

export default function ControlPanel() {
  const { status, loading, updateStatus, error } = useStatus();

  if (loading) return <p className="text-gray-700 dark:text-gray-300">Loading controls…</p>;
  if (error || !status) return <p className="text-red-600">Error loading controls</p>;

  const toggleKill = () =>
    updateStatus({ killSwitch: !status.killSwitch });

  const changeCapital = (e: React.ChangeEvent<HTMLInputElement>) =>
    updateStatus({ capitalAllocation: +e.target.value });

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-100">
        Control Panel
      </h3>

      {/* Kill Switch */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-800 dark:text-gray-100">Kill Switch</span>
        <button
          onClick={toggleKill}
          className={`px-3 py-1 rounded font-medium transition ${
            status.killSwitch
              ? 'bg-red-500 text-white'
              : 'bg-green-500 text-white'
          }`}
        >
          {status.killSwitch ? 'OFF' : 'ON'}
        </button>
      </div>

      {/* Capital Allocation Slider */}
      <div className="mb-4">
        <label className="block text-gray-800 dark:text-gray-100 mb-1">
          Capital Allocation: <strong>{status.capitalAllocation}%</strong>
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={status.capitalAllocation}
          onChange={changeCapital}
          className="w-full"
        />
      </div>

      {/* Manual Override */}
      <OverrideButton />
    </div>
  );
}
