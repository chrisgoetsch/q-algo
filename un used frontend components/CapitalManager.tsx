import { useEffect, useState } from 'react'

type AccountData = {
  equity: number
  cash_available: number
}

type SyncLogEntry = {
  timestamp: string
  action: 'entry' | 'exit'
  trade_id?: string
  gpt_confidence?: number
  mesh_score?: number
  recommended_allocation?: number
  contracts?: number
  pnl?: number
  exit_reason?: string
  regime?: 'normal' | 'high_vol' | 'shock_event'
  agent?: string
}

type CapitalEntry = {
  recommended_allocation: number
  timestamp: string
}

export const CapitalManager = () => {
  const [equity, setEquity] = useState<number>(0)
  const [cash, setCash] = useState<number>(0)
  const [allocation, setAllocation] = useState<number>(0.2)
  const [meshScore, setMeshScore] = useState<number>(0.5)
  const [gptConfidence, setGptConfidence] = useState<number>(0.5)
  const [riskAlert, setRiskAlert] = useState<boolean>(false)

  useEffect(() => {
    fetch('/api/account_summary.json')
      .then(res => res.json())
      .then((data: AccountData) => {
        setEquity(data.equity)
        setCash(data.cash_available)
      })

    fetch('/api/capital_tracker.json')
      .then(res => res.text())
      .then(text => {
        const lines = text.trim().split('\n')
        const last = JSON.parse(lines[lines.length - 1]) as CapitalEntry
        setAllocation(last.recommended_allocation)
      })

    fetch('/api/sync_log.jsonl')
      .then(res => res.text())
      .then(text => {
        const lines = text.trim().split('\n')
        const lastEntry = lines.reverse().find(l => JSON.parse(l).action === 'entry')
        if (!lastEntry) return

        const last = JSON.parse(lastEntry) as SyncLogEntry
        const mesh = last.mesh_score ?? 0.5
        const gpt = last.gpt_confidence ?? 0.5
        const alloc = last.recommended_allocation ?? 0.2

        setMeshScore(mesh)
        setGptConfidence(gpt)

        const alert = gpt < 0.5 || mesh < 0.5 || alloc < 0.15
        setRiskAlert(alert)
      })
  }, [])

  return (
    <div className="p-4 bg-gray-800 text-white rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-4">💼 Capital Management</h2>

      {riskAlert && (
        <div className="mb-4 p-3 bg-red-600 text-white font-bold rounded shadow">
          ⚠️ RISK ALERT: Low confidence or capital throttled
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        <Metric label="Equity" value={`$${equity.toFixed(2)}`} />
        <Metric label="Cash Available" value={`$${cash.toFixed(2)}`} />
        <Metric label="Current Allocation" value={(allocation * 100).toFixed(1) + '%'} />
        <Metric label="Mesh Score" value={meshScore.toFixed(2)} />
        <Metric label="GPT Confidence" value={gptConfidence.toFixed(2)} />
        <Metric label="Throttle Status" value={allocation < 0.15 ? '🚨 Survival Mode' : '✅ Normal'} />
      </div>
    </div>
  )
}

const Metric = ({ label, value }: { label: string; value: string }) => (
  <div className="flex flex-col">
    <span className="text-gray-400 text-xs">{label}</span>
    <span className="font-bold text-base">{value}</span>
  </div>
)
