// ──────────────────────────────────────────────────────────────────────────
// src/components/status/GPTPanel.tsx

import React from 'react';
import useGPTProfile from '../frontend/src/hooks/useGPTProfile';

export default function GPTPanel() {
  const { profile, loading, error } = useGPTProfile();

  if (loading) return <p className="text-gray-700 dark:text-gray-300">Loading GPT insights…</p>;
  if (error || !profile) return <p className="text-red-600">Error loading GPT insights</p>;

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow">
      <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100">
        GPT Intelligence
      </h3>

      <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
        Last Updated: {new Date(profile.lastUpdated).toLocaleTimeString()}
      </p>

      <div className="mb-2">
        <span className="font-medium text-gray-800 dark:text-gray-100">Labels:</span>
        <ul className="mt-1 ml-4 list-disc">
          {profile.labels.map(label => (
            <li key={label} className="text-gray-700 dark:text-gray-200">
              {label}
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-2">
        <span className="font-medium text-gray-800 dark:text-gray-100">Comments:</span>
        <p className="text-gray-700 dark:text-gray-200">{profile.comments}</p>
      </div>

      <div>
        <span className="font-medium text-gray-800 dark:text-gray-100">Outlook:</span>
        <p className="text-gray-700 dark:text-gray-200">{profile.outlook}</p>
      </div>
    </div>
  );
}
