// src/components/KillSwitchToggle.tsx
import { useEffect, useState } from 'react'

export const KillSwitchToggle = () => {
  const [enabled, setEnabled] = useState(false)

  useEffect(() => {
    fetch('/api/status.json')
      .then(res => res.json())
      .then(data => setEnabled(data.kill_switch || false))
      .catch(err => console.error('⚠️ Failed to load status:', err))
  }, [])

  const toggleKillSwitch = () => {
    const newState = !enabled
    setEnabled(newState)
    fetch('/api/status.json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kill_switch: newState })
    }).catch(err => console.error('⚠️ Failed to update kill switch:', err))
  }

  return (
    <div className="p-4 bg-gray-800 rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-2">Kill Switch</h2>
      <button
        onClick={toggleKillSwitch}
        className={`px-4 py-2 rounded-md font-bold ${
          enabled ? 'bg-red-600' : 'bg-green-600'
        } text-white`}
      >
        {enabled ? 'DISABLED (Kill ON)' : 'ENABLED (Kill OFF)'}
      </button>
    </div>
  )
}
