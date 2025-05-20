type Props = {
  data: {
    timestamp: string
    agent: string
    score: number
    status: string
    reason: string
    trade_id?: string
  }
}

export const MeshAgentCard = ({ data }: Props) => {
  const scoreColor =
    data.score > 0.8 ? 'bg-green-500'
    : data.score > 0.5 ? 'bg-yellow-500'
    : 'bg-red-500'

  const statusLabel: string = {
    active: '🟢 Active',
    idle: '🟡 Idle',
    suppressed: '🔴 Suppressed'
  }[data.status] || data.status

  const timeString = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(new Date(data.timestamp))

  return (
    <div className="p-4 bg-gray-700 rounded-xl shadow-inner">
      <div className="flex justify-between items-center mb-1">
        <h3 className="text-lg font-bold">{data.agent}</h3>
        <span className="text-sm">{statusLabel}</span>
      </div>

      <div className="mb-2">
        <div className="w-full bg-gray-500 h-2 rounded">
          <div
            className={`${scoreColor} h-2 rounded`}
            style={{ width: `${Math.round(data.score * 100)}%` }}
          />
        </div>
        <p className="text-xs text-right mt-1 opacity-80">
          {(data.score * 100).toFixed(1)}%
        </p>
      </div>

      <p className="text-xs text-gray-300">🧠 {data.reason}</p>
      <p className="text-xs text-gray-400 mt-1">
        📁 Trade ID: {data.trade_id || 'N/A'}
      </p>
      <p className="text-xs text-gray-500 mt-1">
        ⏱ {timeString}
      </p>
    </div>
  )
}
