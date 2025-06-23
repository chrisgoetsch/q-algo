// File: src/components/cards/TradeLog.tsx

import React, { useEffect, useState } from 'react';

export function TradeLog() {
  const [trades, setTrades] = useState<any[]>([]);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const res = await fetch('/api/trades/recent');
        const json = await res.json();
        setTrades(json);
      } catch (err) {
        console.error('Failed to load trade log', err);
      }
    };
    fetchTrades();
    const interval = setInterval(fetchTrades, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow overflow-y-auto">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">📋 Trade Log</h2>
      <ul className="text-sm divide-y divide-gray-200 dark:divide-gray-700">
        {trades.slice(0, 10).map((trade, idx) => (
          <li key={idx} className="py-2 flex flex-col">
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {trade.direction} {trade.contracts}x {trade.option_symbol}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Entry: {new Date(trade.timestamp).toLocaleTimeString()} | Score: {trade.score?.toFixed(2)} | PnL: {trade.pnl ?? 'n/a'}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
