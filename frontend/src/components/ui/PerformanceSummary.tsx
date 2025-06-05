import { useEffect, useState } from 'react'

type Trade = {
  action: string
  pnl?: number
  allocation?: number
  contracts?: number
  mesh_score?: number
  gpt_confidence?: number
}

export const PerformanceSummary = () => {
  const [stats, setStats] = useState({
    totalTrades: 0,
    wins: 0,
    totalPnL: 0,
    maxDrawdown: 0,
    avgPnL: 0,
    avgAlloc: 0,
    avgContracts: 0,
    avgMesh: 0,
    avgGPT: 0,
    winRate: 0
  })

  useEffect(() => {
    fetch('/api/sync_log.jsonl')
      .then(res => res.text())
      .then(text => {
        const lines = text.trim().split('\n').map(line => JSON.parse(line)) as Trade[]
        const exits = lines.filter(t => t.action === 'exit')

        let totalTrades = exits.length
        let wins = 0
        let totalPnL = 0
        let maxDrawdown = 0
        let rollingEquity = 0

        let allocSum = 0
        let contractSum = 0
        let meshSum = 0
        let gptSum = 0

        exits.forEach(t => {
          const pnl = t.pnl || 0
          const alloc = t.allocation || 0
          const contracts = t.contracts || 0
          const mesh = t.mesh_score || 0
          const gpt = t.gpt_confidence || 0

          totalPnL += pnl
          if (pnl > 0) wins++
          rollingEquity += pnl
          maxDrawdown = Math.min(maxDrawdown, rollingEquity)

          allocSum += alloc
          contractSum += contracts
          meshSum += mesh
          gptSum += gpt
        })

        const winRate = totalTrades > 0 ? wins / totalTrades : 0

        setStats({
          totalTrades,
          wins,
          winRate,
          totalPnL,
          maxDrawdown,
          avgPnL: totalTrades ? totalPnL / totalTrades : 0,
          avgAlloc: totalTrades ? allocSum / totalTrades : 0,
          avgContracts: totalTrades ? contractSum / totalTrades : 0,
          avgMesh: totalTrades ? meshSum / totalTrades : 0,
          avgGPT: totalTrades ? gptSum / totalTrades : 0
        })
      })
      .catch(err => console.error('❌ Failed to load sync_log.jsonl:', err))
  }, [])

  return (
    <div className="p-4 bg-gray-800 text-white rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-4">📈 Performance Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        <Metric label="Trades" value={stats.totalTrades} />
        <Metric label="Win Rate" value={(stats.winRate * 100).toFixed(1) + '%'} />
        <Metric label="Total PnL" value={`$${stats.totalPnL.toFixed(2)}`} color={stats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'} />
        <Metric label="Max Drawdown" value={`$${stats.maxDrawdown.toFixed(2)}`} color="text-red-400" />
        <Metric label="Avg PnL" value={`$${stats.avgPnL.toFixed(2)}`} />
        <Metric label="Avg Allocation" value={(stats.avgAlloc * 100).toFixed(1) + '%'} />
        <Metric label="Avg Contracts" value={stats.avgContracts.toFixed(1)} />
        <Metric label="Avg Mesh Score" value={stats.avgMesh.toFixed(2)} />
        <Metric label="Avg GPT Conf" value={stats.avgGPT.toFixed(2)} />
      </div>
    </div>
  )
}

const Metric = ({ label, value, color = 'text-white' }: { label: string; value: string | number; color?: string }) => (
  <div className="flex flex-col">
    <span className="text-gray-400 text-xs">{label}</span>
    <span className={`font-bold text-base ${color}`}>{value}</span>
  </div>
)
