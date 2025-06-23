// File: src/pages/Dashboard.tsx
// Q-ALGO Hedge Fund Command Center Dashboard Layout (v1.0)

import React from 'react';
import { GptPanel } from '../components/cards/GptPanel';
import { MeshPanel } from '../components/cards/MeshPanel';
import { SpyChart } from '../components/cards/SpyChart';
import { TradeLog } from '../components/cards/TradeLog';
import { ControlPanel } from '../components/cards/ControlPanel';
import { CapitalPanel } from '../components/cards/CapitalPanel';
import { SystemStatus } from '../components/cards/SystemStatus';
import { ReinforcementPanel } from '../components/cards/ReinforcementPanel';
import { Sidebar } from '../components/layout/Sidebar';

export default function Dashboard() {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />

      <main className="flex-1 p-4 overflow-y-scroll grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div id="gpt"><GptPanel /></div>
        <div id="mesh"><MeshPanel /></div>
        <div id="chart"><SpyChart /></div>
        <div id="trades"><TradeLog /></div>
        <div id="controls"><ControlPanel /></div>
        <div id="capital"><CapitalPanel /></div>
        <div id="status"><SystemStatus /></div>
        <div id="learning"><ReinforcementPanel /></div>
      </main>
    </div>
  );
}
