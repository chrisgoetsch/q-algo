// File: src/components/cards/MeshPanel.tsx

import React, { useEffect, useState } from 'react';

export function MeshPanel() {
  const [meshData, setMeshData] = useState<any>(null);

  useEffect(() => {
    const fetchMesh = async () => {
      try {
        const res = await fetch('/api/mesh/status');
        const json = await res.json();
        setMeshData(json);
      } catch (e) {
        console.error('Failed to load mesh data', e);
      }
    };
    fetchMesh();
    const interval = setInterval(fetchMesh, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!meshData) {
    return <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">Loading Mesh Panel…</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">📡 Mesh Agent Scores</h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
        <strong>Combined Score:</strong> {meshData.mesh_score}
      </p>
      <ul className="text-sm text-gray-700 dark:text-gray-200 mt-2 space-y-1">
        {Object.entries(meshData.agent_signals || {}).map(([agent, score]) => (
          <li key={agent} className="flex justify-between">
            <span className="capitalize">{agent.replace('q_', '')}</span>
            <span>{(score as number).toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
