import React from 'react'

import { CapitalManager } from './components/CapitalManager'
import { CapitalSlider } from './components/CapitalSlider'
import { MeshAgentPanel } from './components/MeshAgentPanel'
import { TradeLogViewer } from './components/TradeLogViewer'
import { PerformanceSummary } from './components/PerformanceSummary'
import { KillSwitchToggle } from './components/KillSwitchToggle'
import { GptIntelPanel } from './components/GptIntelPanel'
import { TradeViewChart } from './components/TradeViewChart'
import { AccountSummaryPanel } from './components/AccountSummaryPanel'
import { SystemHUD } from './components/SystemHUD'

const Dashboard: React.FC = () => {
  return (
    <div className="h-screen w-screen overflow-hidden grid grid-cols-6 grid-rows-6 gap-4 p-4 bg-black text-white font-sans">

      {/* HUD Status Bar */}
      <div className="col-span-6 row-span-1">
        <SystemHUD />
      </div>

      {/* Chart */}
      <div className="col-span-4 row-span-2 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <TradeViewChart />
      </div>

      {/* Mesh Panel */}
      <div className="col-span-2 row-span-2 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <MeshAgentPanel />
      </div>

      {/* Trade Log */}
      <div className="col-span-4 row-span-2 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <TradeLogViewer />
      </div>

      {/* Performance */}
      <div className="col-span-2 row-span-1 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <PerformanceSummary />
      </div>

      {/* Bottom Row */}
      <div className="col-span-1 row-span-1 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <CapitalManager />
      </div>
      <div className="col-span-1 row-span-1 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <CapitalSlider />
      </div>
      <div className="col-span-1 row-span-1 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <KillSwitchToggle />
      </div>
      <div className="col-span-2 row-span-1 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <GptIntelPanel />
      </div>
      <div className="col-span-1 row-span-1 bg-gray-900 rounded-2xl shadow-lg p-4 overflow-hidden h-full">
        <AccountSummaryPanel />
      </div>
    </div>
  )
}

export default Dashboard
