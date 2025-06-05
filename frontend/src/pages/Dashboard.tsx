
// src/pages/Dashboard.tsx
import React from 'react';
import MainLayout from '../MainLayout';
import SPYChart from '../components/charts/SPYChart';
import ControlPanel from '../components/ui/ControlPanel';
import RuntimeStatusPanel from '../components/ui/RuntimeStatusPanel';
import TradeLogViewer from '../components/ui/TradeLogViewer';
import GptIntelPanel from '../components/ui/GptIntelPanel';
import PerformanceSummary from '../components/ui/PerformanceSummary';

export default function Dashboard() {
  return (
    <MainLayout>
      <div className="grid gap-4 xl:grid-cols-3">
        {/* Column 1: Chart */}
        <div className="xl:col-span-2 bg-white dark:bg-gray-800 rounded-2xl shadow p-4">
          <SPYChart />
        </div>

        {/* Column 2: Control & Status */}
        <div className="space-y-4">
          <ControlPanel />
          <RuntimeStatusPanel />
          <PerformanceSummary />
          <GptIntelPanel />
        </div>

        {/* Full-width Trade History */}
        <div className="xl:col-span-3">
          <TradeLogViewer />
        </div>
      </div>
    </MainLayout>
  );
}
