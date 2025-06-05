// ──────────────────────────────────────────────────────────────────────────
// src/components/tables/TradeHistoryTable.tsx

import React from 'react';
import useTrades, { Trade } from '../frontend/src/hooks/useTrades';

export default function TradeHistoryTable() {
  const { trades, loading, error } = useTrades();

  if (loading) return <p className="text-gray-700 dark:text-gray-300">Loading trade history…</p>;
  if (error || !trades) return <p className="text-red-600">Error loading trades</p>;

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow overflow-x-auto">
      <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100">
        Trade History
      </h3>
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
              Time
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
              Direction
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
              Strike
            </th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
              PnL
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
              Agent
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
              Exit Reason
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {trades.map((t: Trade) => (
            <tr key={t.timestamp}>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 dark:text-gray-200">
                {new Date(t.timestamp).toLocaleString()}
              </td>
              <td
                className={`px-3 py-2 whitespace-nowrap text-sm ${
                  t.direction === 'BUY' ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {t.direction}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 dark:text-gray-200">
                {t.strike}
              </td>
              <td
                className={`px-3 py-2 whitespace-nowrap text-sm text-right ${
                  t.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {t.pnl.toFixed(2)}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 dark:text-gray-200">
                {t.agent}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-700 dark:text-gray-200">
                {t.exitReason}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
