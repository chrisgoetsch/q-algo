// File: src/components/cards/CapitalPanel.tsx

import React, { useEffect, useState } from 'react';

export function CapitalPanel() {
  const [capital, setCapital] = useState<any>(null);

  useEffect(() => {
    const fetchCapital = async () => {
      try {
        const res = await fetch('/api/account/summary');
        const json = await res.json();
        setCapital(json);
      } catch (err) {
        console.error('Failed to fetch capital data', err);
      }
    };
    fetchCapital();
    const interval = setInterval(fetchCapital, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!capital) {
    return <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">Loading Capital Panel…</div>;
  }

  const drawdown = ((capital.currentEquity - capital.startEquity) / capital.startEquity) * 100;

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">💰 Capital Overview</h2>
      <p className="text-sm text-gray-700 dark:text-gray-200">
        <strong>Current Equity:</strong> ${capital.currentEquity?.toFixed(2)}
      </p>
      <p className="text-sm text-gray-700 dark:text-gray-200">
        <strong>Starting Equity:</strong> ${capital.startEquity?.toFixed(2)}
      </p>
      <p className={`text-sm ${drawdown < 0 ? 'text-red-500' : 'text-green-500'}`}> 
        <strong>Drawdown:</strong> {drawdown.toFixed(2)}%
      </p>
      <p className="text-sm text-gray-700 dark:text-gray-200">
        <strong>Throttle:</strong> {capital.throttle?.toFixed(2)}x
      </p>
    </div>
  );
}
