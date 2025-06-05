// src/components/GptIntelPanel.tsx
import { useEffect, useState } from 'react'

type GPTInsight = {
  timestamp: string
  model: string
  stage: string
  prompt: string
  response: string
  confidence: number
  regret_risk: number
  agents: Record<string, number>  // { Q_Precision: 0.8, Q_Quant: 0.6 }
}

export const GptIntelPanel = () => {
  const [latest, setLatest] = useState<GPTInsight | null>(null)
  const [showDialog, setShowDialog] = useState(false)

  useEffect(() => {
    fetch('/api/qthink_dialogs.jsonl')
      .then(res => res.text())
      .then(text => {
        const lines = text.trim().split('\n')
        const last = JSON.parse(lines[lines.length - 1])
        setLatest(last)
      })
      .catch(err => console.error('Failed to load GPT insight', err))
  }, [])

  if (!latest) return <div className="p-4 bg-gray-800 text-white rounded-xl">Loading GPT Insight...</div>

  return (
    <div className="p-4 bg-gray-800 text-white rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-2">GPT Reasoning Summary</h2>
      <p className="text-sm mb-2 text-gray-300">{latest.response}</p>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm">Confidence: {(latest.confidence * 100).toFixed(1)}%</span>
        <span className={`text-sm ${latest.regret_risk > 0.5 ? 'text-red-400' : 'text-green-400'}`}>
          Regret Risk: {(latest.regret_risk * 100).toFixed(1)}%
        </span>
      </div>
      <div className="mb-2">
        <h3 className="text-sm font-medium mb-1">Agent Influence</h3>
        <ul className="text-xs grid grid-cols-2 gap-1">
          {Object.entries(latest.agents).map(([agent, score]) => (
            <li key={agent}>{agent}: {(score * 100).toFixed(0)}%</li>
          ))}
        </ul>
      </div>
      <button
        className="mt-2 px-3 py-1 bg-blue-500 text-white text-sm rounded"
        onClick={() => setShowDialog(true)}
      >
        View Full GPT Dialog
      </button>

      {showDialog && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-70 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-900 text-black dark:text-white p-6 rounded-xl max-w-2xl w-full">
            <h3 className="text-lg font-bold mb-2">Full GPT Dialog</h3>
            <p className="mb-2 text-xs text-gray-500">Model: {latest.model}</p>
            <pre className="whitespace-pre-wrap text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-y-scroll max-h-96">
Prompt:
{latest.prompt}

Response:
{latest.response}
            </pre>
            <button
              onClick={() => setShowDialog(false)}
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
