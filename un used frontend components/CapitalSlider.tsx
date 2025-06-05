// src/components/CapitalSlider.tsx
import { useEffect, useState } from 'react'

export const CapitalSlider = () => {
  const [value, setValue] = useState(20)

  useEffect(() => {
    fetch('/api/capital_tracker.json')
      .then(res => res.json())
      .then(data => setValue(data.allocation || 20))
      .catch(err => console.error('⚠️ Failed to load capital:', err))
  }, [])

  const updateSlider = (newValue: number) => {
    setValue(newValue)
    fetch('/api/capital_tracker.json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ allocation: newValue })
    }).catch(err => console.error('⚠️ Failed to update capital:', err))
  }

  return (
    <div className="p-4 bg-gray-800 rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-2">Capital Allocation</h2>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => updateSlider(Number(e.target.value))}
        className="w-full"
      />
      <p className="mt-2 text-center text-sm">{value}% Allocated</p>
    </div>
  )
}
