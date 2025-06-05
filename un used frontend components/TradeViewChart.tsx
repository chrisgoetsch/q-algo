import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'

interface GptDialog {
  timestamp: string
  model: string
  stage: string
  prompt: string
  response: string
}

export const TradeViewChart = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const [dialog, setDialog] = useState<GptDialog | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#1f2937' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
    })

    const candleSeries = chart.addCandlestickSeries()

    const POLY_KEY = import.meta.env.VITE_POLYGON_API_KEY
    const today = new Date().toISOString().split('T')[0]

    fetch(`https://api.polygon.io/v2/aggs/ticker/SPY/range/1/minute/${today}/${today}?adjusted=true&sort=asc&apiKey=${POLY_KEY}`)
      .then(res => res.json())
      .then(res => {
        if (!res.results) return

        const candles = res.results.map((c: any) => ({
          time: c.t / 1000,
          open: c.o,
          high: c.h,
          low: c.l,
          close: c.c,
        }))

        candleSeries.setData(candles)
      })

    fetch('/api/sync_log.jsonl')
      .then(res => res.text())
      .then(text => {
        const trades = text.trim().split('\n').map(line => JSON.parse(line))
          .filter(t => t.action === 'entry')
          .map(t => ({
            time: Math.floor(new Date(t.timestamp).getTime() / 1000),
            position: 'aboveBar',
            color: 'lime',
            shape: 'arrowDown',
            text: `${t.agent}\n${(t.gpt_confidence * 100).toFixed(0)}%`,
            id: t.trade_id,
          }))
        candleSeries.setMarkers(trades as any)
      })

    chart.subscribeClick((param: any) => {
      if ('time' in param) {
        const timestamp = new Date((param.time as number) * 1000).toISOString()
        fetch('/api/qthink_dialogs.jsonl')
          .then(res => res.text())
          .then(text => {
            const lines = text.trim().split('\n')
            const match = lines
              .map((line: string) => JSON.parse(line))
              .reverse()
              .find((l: any) => l.timestamp <= timestamp)
            if (match) setDialog(match as GptDialog)
          })
      }
    })

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      chart.remove()
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <div className="relative">
      <div ref={chartContainerRef} className="w-full" />

      {dialog && (
        <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-900 text-black dark:text-white p-6 rounded-xl max-w-2xl w-full">
            <h3 className="text-lg font-bold mb-2">GPT Insight ({dialog.stage})</h3>
            <p className="text-xs text-gray-400 mb-1">Model: {dialog.model}</p>
            <pre className="whitespace-pre-wrap text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded max-h-96 overflow-y-auto">
Prompt:
{dialog.prompt}

Response:
{dialog.response}
            </pre>
            <button
              onClick={() => setDialog(null)}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
