import { useEffect, useState } from 'react'
import { MeshAgentCard } from '../frontend/src/components/ui/MeshAgentCard'

type AgentLog = {
  timestamp: string
  agent: string
  score: number
  status: string
  reason: string
  trade_id?: string
}

export const MeshAgentPanel = () => {
  const [agentData, setAgentData] = useState<Record<string, AgentLog>>({})

  useEffect(() => {
    fetch('/api/mesh_logger.jsonl')
      .then(res => res.text())
      .then(text => {
        const lines = text.trim().split('\n')
        const latestByAgent: Record<string, AgentLog> = {}
        lines.map(line => JSON.parse(line)).forEach(entry => {
          latestByAgent[entry.agent] = entry
        })
        setAgentData(latestByAgent)
      })
      .catch(err => console.error('⚠️ Failed to load mesh logger:', err))
  }, [])

  return (
    <div className="p-4 bg-gray-800 text-white rounded-xl shadow-md">
      <h2 className="text-lg font-semibold mb-4">Mesh Agent Status</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(agentData).map(([agent, data]) => (
          <MeshAgentCard key={agent} data={data} />
        ))}
      </div>
    </div>
  )
}
