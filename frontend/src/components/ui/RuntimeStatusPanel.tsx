// ──────────────────────────────────────────────────────────────────────────
// src/components/status/RuntimeStatusPanel.tsx

import React from 'react';
import useRuntimeState from '../../hooks/useRuntimeState';

export default function RuntimeStatusPanel() {
  const { runtime, loading, error } = useRuntimeState();

  if (loading) return <p className="text-gray-700 dark:text-gray-300">Loading status…</p>;
  if (error || !runtime) return <p className="text-red-600">Error loading status</p>;

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100">
        Runtime Status
      </h3>

      {/* Mode Badge */}
      <div className="flex items-center mb-2">
        <span className="font-medium text-gray-800 dark:text-gray-100">Mode:</span>
        <span
          className={`ml-2 px-2 py-1 rounded-full text-xs ${
            runtime.mode === 'live'
              ? 'bg-green-200 text-green-800'
              : 'bg-yellow-200 text-yellow-800'
          }`}
        >
          {runtime.mode.toUpperCase()}
        </span>
      </div>

      {/* Active Agents */}
      <div className="mb-2">
        <span className="font-medium text-gray-800 dark:text-gray-100">
          Active Agents:
        </span>
        <ul className="mt-1 ml-2 list-disc">
          {runtime.activeAgents.map(agent => (
            <li key={agent.name} className="flex items-center">
              <span
                className={`w-2 h-2 rounded-full mr-1 ${
                  agent.confidence > 0.8
                    ? 'bg-green-400'
                    : agent.confidence > 0.5
                    ? 'bg-yellow-400'
                    : 'bg-red-400'
                }`}
              />
              <span className="text-gray-800 dark:text-gray-100">
                {agent.name} ({(agent.confidence * 100).toFixed(0)}%)
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Last Trade Summary */}
      <div className="mb-2">
        <span className="font-medium text-gray-800 dark:text-gray-100">
          Last Trade:
        </span>
        <div className="ml-2">
          <p className="text-gray-800 dark:text-gray-100">
            {new Date(runtime.lastTrade.timestamp).toLocaleTimeString()} —{' '}
            <span className={runtime.lastTrade.direction === 'BUY' ? 'text-green-600' : 'text-red-600'}>
              {runtime.lastTrade.direction}
            </span>{' '}
            {runtime.lastTrade.agent} — PnL: {runtime.lastTrade.pnl.toFixed(2)}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Exit reason: {runtime.lastTrade.exitReason}
          </p>
        </div>
      </div>

      {/* Mesh Health Badge */}
      <div className="mb-2">
        <span className="font-medium text-gray-800 dark:text-gray-100">Mesh Health:</span>
        <span
          className={`ml-2 px-2 py-1 rounded-full text-xs ${
            runtime.meshHealth === 'healthy'
              ? 'bg-green-200 text-green-800'
              : runtime.meshHealth === 'degraded'
              ? 'bg-yellow-200 text-yellow-800'
              : 'bg-red-200 text-red-800'
          }`}
        >
          {runtime.meshHealth.toUpperCase()}
        </span>
      </div>
    </div>
  );
}
