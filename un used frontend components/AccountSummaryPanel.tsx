// src/components/AccountSummaryPanel.tsx
import { useEffect, useState } from 'react'

type AccountSummary = {
  timestamp: string
  account_number: string
  account_type: string
  cash_available: number
  cash_balance: number
  option_buying_power: number
  equity: number
  unrealized_pl: number
  realized_pl: number
  margin_balance: number
  day_trade_buying_power: number
}

export const AccountSummaryPanel = () => {
  const [data, setData] = useState<AccountSummary | null>(null)

  useEffect(() => {
    fetch('/api/account_summary.json')
      .then(res => res.json())
      .then(setData)
      .catch(err => console.error('❌ Failed to load account summary:', err))
  }, [])

if (!data) return <div className="p-4 bg-gray-800 text-white rounded-xl">Loading account info...</div>

if (data.equity === 0 && data.cash_available === 0) {
  return (
    <div className="p-4 bg-yellow-800 text-white rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-2">Account Summary</h2>
      <p className="text-sm">⚠️ This account appears to be unfunded or inactive.</p>
      <p className="text-xs text-gray-300 mt-2">Account ID: {data.account_number}</p>
    </div>
  )
}


  return (
    <div className="p-4 bg-gray-800 text-white rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-2">Account Summary</h2>
      <p className="text-sm mb-1 text-gray-400">Account #{data.account_number} ({data.account_type})</p>
      <ul className="text-sm grid grid-cols-2 gap-2">
        <li>💰 Cash Available: ${data.cash_available.toFixed(2)}</li>
        <li>💼 Option BP: ${data.option_buying_power.toFixed(2)}</li>
        <li>📈 Equity: ${data.equity.toFixed(2)}</li>
        <li>📉 Unrealized PnL: ${data.unrealized_pl.toFixed(2)}</li>
        <li>📊 Realized PnL: ${data.realized_pl.toFixed(2)}</li>
        <li>📉 Margin Used: ${data.margin_balance.toFixed(2)}</li>
        <li>⚡ DT Buying Power: ${data.day_trade_buying_power.toFixed(2)}</li>
        <li className="text-xs text-gray-500 mt-2 col-span-2">Last Updated: {data.timestamp}</li>
      </ul>
    </div>
  )
}
