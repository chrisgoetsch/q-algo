// ──────────────────────────────────────────────────────────────────────────
// src/components/charts/SPYChart.tsx

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
} from 'recharts';
import useWebSocket from '../../hooks/useWebSocket';

interface DataPoint {
  timestamp: number;
  price: number;
  vwap: number;
  markers?: { type: 'ENTRY' | 'EXIT'; price: number; timestamp: number }[];
}

export default function SPYChart() {
  const [data, setData] = useState<DataPoint[]>([]);
  const { lastMessage } = useWebSocket('/ws/spy');

  useEffect(() => {
    if (!lastMessage) return;
    try {
      const msg: any = JSON.parse(lastMessage.data);
      const point: DataPoint = {
        timestamp: msg.timestamp,
        price: msg.price,
        vwap: msg.vwap,
        markers: msg.markers,
      };
      setData(prev => [...prev.slice(-199), point]);
    } catch {
      // ignore parse errors
    }
  }, [lastMessage]);

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100">
        Live SPY Price
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={t => new Date(t as number).toLocaleTimeString()}
            tick={{ fill: '#6B7280', fontSize: 12 }}
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fill: '#6B7280', fontSize: 12 }}
          />
          <Tooltip
            labelFormatter={val => new Date(val as number).toLocaleTimeString()}
          />

          {/* Price (blue) */}
          <Line
            type="monotone"
            dataKey="price"
            stroke="#3B82F6"
            dot={false}
            strokeWidth={2}
            animationDuration={200}
          />

          {/* VWAP (gold dashed) */}
          <Line
            type="monotone"
            dataKey="vwap"
            stroke="#FACC15"
            dot={false}
            strokeWidth={2}
            strokeDasharray="4 2"
            animationDuration={200}
          />

          {/* Entry/Exit markers */}
          {data.flatMap((pt) =>
            pt.markers?.map((m, i) => (
              <ReferenceDot
                key={`${pt.timestamp}-${i}`}
                x={pt.timestamp}
                y={m.price}
                r={4}
                fill={m.type === 'ENTRY' ? '#10B981' : '#EF4444'}
                stroke="none"
              />
            ))
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex space-x-4 mt-2 text-xs">
        <div className="flex items-center">
          <span className="w-2 h-2 bg-blue-500 inline-block rounded-full mr-1" />
          <span className="text-gray-700 dark:text-gray-200">Price</span>
        </div>
        <div className="flex items-center">
          <span className="w-2 h-2 bg-yellow-400 inline-block rounded-full mr-1" />
          <span className="text-gray-700 dark:text-gray-200">VWAP</span>
        </div>
        <div className="flex items-center">
          <span className="w-2 h-2 bg-green-400 inline-block rounded-full mr-1" />
          <span className="text-gray-700 dark:text-gray-200">Entry</span>
        </div>
        <div className="flex items-center">
          <span className="w-2 h-2 bg-red-400 inline-block rounded-full mr-1" />
          <span className="text-gray-700 dark:text-gray-200">Exit</span>
        </div>
      </div>
    </div>
  );
}
