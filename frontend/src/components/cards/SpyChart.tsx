// File: src/components/cards/SpyChart.tsx

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export function SpyChart() {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    const fetchChart = async () => {
      try {
        const res = await fetch('/api/chart/spy');
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error('Failed to load SPY chart data', e);
      }
    };
    fetchChart();
    const interval = setInterval(fetchChart, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">📈 SPY Chart</h2>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="timestamp" hide />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Line type="monotone" dataKey="price" stroke="#3b82f6" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
