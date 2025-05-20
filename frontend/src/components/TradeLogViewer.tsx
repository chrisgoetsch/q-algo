import React, { useEffect, useState } from 'react'

type Trade = {
  timestamp: string
  trade_id: string
  symbol: string
  action: string
  contracts: number
  allocation: number
  mesh_score: number
  gpt_confidence: number
  agent: string
  pnl?: number
  exit_price?: number
  exit_reason?: string
}

export const TradeLogViewer: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([])

  useEffect(() => {
    const fetchLog = async () => {
      try {
        const res = await fetch('/api/sync_log.jsonl')
        const text = await res.text()
        const parsed = text.trim().split('\n').map(line => JSON.parse(line))
        setTrades(parsed.reverse()) // Most recent first
      } catch (err) {
        console.error('❌ Failed to load sync log:', err)
      }
    }

    fetchLog()
    const interval = setInterval(fetchLog, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-4 bg-gray-900 text-white rounded-2xl shadow-lg">
      <h2 className="text-xl font-bold mb-4">Trade Log</h2>
      <div className="overflow-x-auto max-h-[32rem] overflow-y-auto text-sm">
        <table className="min-w-full border-collapse">
          <thead className="sticky top-0 bg-gray-800 z-10">
            <tr>
              <th className="p-2 text-left">Time</th>
              <th className="p-2 text-left">Action</th>
              <th className="p-2 text-left">PnL</th>
              <th className="p-2 text-left">Alloc%</th>
              <th className="p-2 text-left">Contracts</th>
              <th className="p-2 text-left">Agent</th>
              <th className="p-2 text-left">GPT</th>
              <th className="p-2 text-left">Mesh</th>
              <th className="p-2 text-left">Exit Reason</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => {
              const pnlColor =
                trade.pnl === undefined
                  ? 'text-gray-400'
                  : trade.pnl > 0
                  ? 'text-green-400'
                  : 'text-red-400'

              return (
                <tr key={trade.trade_id} className="border-t border-gray-700 hover:bg-gray-800">
                  <td className="p-2 whitespace-nowrap">{new Date(trade.timestamp).toLocaleTimeString()}</td>
                  <td className="p-2 capitalize">{trade.action}</td>
                  <td className={`p-2 font-mono ${pnlColor}`}>
                    {trade.pnl !== undefined ? trade.pnl.toFixed(2) : '--'}
                  </td>
                  <td className="p-2">{trade.allocation}%</td>
                  <td className="p-2">{trade.contracts}</td>
                  <td className="p-2">{trade.agent}</td>
                  <td className="p-2 text-blue-400">{(trade.gpt_confidence * 100).toFixed(0)}%</td>
                  <td className="p-2 text-yellow-300">{(trade.mesh_score * 100).toFixed(0)}%</td>
                  <td className="p-2 text-gray-300">{trade.exit_reason || '--'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
