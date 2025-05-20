// hooks/useSyncLog.ts
import { useEffect, useState } from 'react'

export const useSyncLog = () => {
  const [trades, setTrades] = useState([])

  useEffect(() => {
    const fetchLog = async () => {
      const res = await fetch('/api/sync_log.jsonl')
      const text = await res.text()
      const lines = text.trim().split('\n').map(line => JSON.parse(line))
      setTrades(lines.reverse())
    }
    fetchLog()
    const interval = setInterval(fetchLog, 5000)
    return () => clearInterval(interval)
  }, [])

  return trades
}
