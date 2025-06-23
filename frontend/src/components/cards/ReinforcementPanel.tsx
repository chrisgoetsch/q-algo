// File: src/components/cards/ReinforcementPanel.tsx

import React, { useEffect, useState } from 'react';

export function ReinforcementPanel() {
  const [labels, setLabels] = useState<any[]>([]);

  useEffect(() => {
    const fetchLabels = async () => {
      try {
        const res = await fetch('/api/gpt/reinforcement');
        const json = await res.json();
        setLabels(json);
      } catch (e) {
        console.error('Failed to load reinforcement profile', e);
      }
    };
    fetchLabels();
    const interval = setInterval(fetchLabels, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">📦 Reinforcement Learning Summary</h2>
      <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
        {labels.sort((a, b) => b.count - a.count).slice(0, 12).map((label) => (
          <li key={label.label} className="flex justify-between">
            <span>{label.label}</span>
            <span className="font-mono text-right">{label.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
