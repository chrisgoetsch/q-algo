import React, { useEffect, useState } from 'react'

type RuntimeState = {
  mode: string
  pivot_active: boolean
  mesh_agents: string[]
  last_updated: string
}

type PivotAlert = {
  macro_type: string
  vix_level: number
  impact_sector: string
  recommended_mode: string
}

export const SystemHUD: React.FC = () => {
  const [state, setState] = useState<RuntimeState | null>(null)
  const [pivot, setPivot] = useState<PivotAlert | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resState = await fetch('/api/runtime_state.json')
        const jsonState = await resState.json()
        setState(jsonState)

        const resPivot = await fetch('/api/pivot_alert.json')
        const jsonPivot = await resPivot.json()
        setPivot(jsonPivot)
      } catch (err) {
        console.error('❌ Failed to load HUD data:', err)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="w-full bg-gray-800 text-sm text-gray-300 px-6 py-2 rounded-xl flex items-center justify-between shadow-md">
      <div className="flex gap-4 items-center">
        <span>🟢 Live</span>
        <span>Mode: <strong>{state?.mode || '...'}</strong></span>
        <span>Agents: <strong>{state?.mesh_agents?.length || 0}</strong></span>
      </div>
      <div className="flex gap-4 items-center">
        {pivot?.macro_type ? (
          <span className="text-yellow-400 animate-pulse">⚠️ Pivot: {pivot.macro_type} — VIX {pivot.vix_level}</span>
        ) : (
          <span className="text-green-500">No Pivot</span>
        )}
        <span className="text-gray-500">Updated: {new Date(state?.last_updated || Date.now()).toLocaleTimeString()}</span>
      </div>
    </div>
  )
}
