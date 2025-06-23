// File: src/components/cards/GptPanel.tsx

import React, { useEffect, useState } from 'react';

export function GptPanel() {
  const [gptData, setGptData] = useState<any>(null);

  useEffect(() => {
    const fetchLatestGpt = async () => {
      try {
        const res = await fetch('/api/models/entry/latest');
        const json = await res.json();
        setGptData(json);
      } catch (err) {
        console.error('Failed to fetch GPT data', err);
      }
    };
    fetchLatestGpt();
    const interval = setInterval(fetchLatestGpt, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!gptData) {
    return <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">Loading GPT Panel…</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">🧠 GPT Entry Reasoning</h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
        <strong>Confidence:</strong> {gptData.gpt_confidence ?? 'n/a'}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
        <strong>Direction:</strong> {gptData.regime?.match(/bull|trend|stable/) ? 'CALL' : 'PUT'}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
        <strong>Rationale:</strong> {gptData.gpt_reasoning || gptData.rationale}
      </p>
      <p className="text-xs text-gray-400 dark:text-gray-500">
        <strong>Updated:</strong> {new Date(gptData.timestamp || Date.now()).toLocaleTimeString()}
      </p>
      <pre className="text-xs mt-3 p-2 bg-gray-100 dark:bg-gray-900 rounded text-gray-700 dark:text-gray-200 overflow-x-auto">
        {JSON.stringify(gptData, null, 2)}
      </pre>
    </div>
  );
}
