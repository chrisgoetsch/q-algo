// ──────────────────────────────────────────────────────────────────────────
// src/components/controls/OverrideButton.tsx

import React from 'react';

export default function OverrideButton() {
  const handleOverride = async () => {
    try {
      const res = await fetch('/api/trades/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ override: true }),
      });
      if (!res.ok) throw new Error(`Status ${res.status}`);
      alert('Manual override sent');
    } catch (err) {
      console.error(err);
      alert('Failed to send override');
    }
  };

  return (
    <button
      onClick={handleOverride}
      className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
    >
      Manual Trade Override
    </button>
  );
}
