// ──────────────────────────────────────────────────────────────────────────
// src/hooks/useRuntimeState.ts

import useSWR from 'swr';
import fetcher from '../api/fetcher';

export interface AgentInfo {
  name: string;
  confidence: number; // 0.0–1.0
}

export interface LastTradeInfo {
  timestamp: number;
  direction: 'BUY' | 'SELL';
  pnl: number;
  agent: string;
  exitReason: string;
}

export interface RuntimeState {
  mode: 'live' | 'test';
  activeAgents: AgentInfo[];
  lastTrade: LastTradeInfo;
  meshHealth: 'healthy' | 'degraded' | 'down';
}

export default function useRuntimeState() {
  const { data, error } = useSWR<RuntimeState>('/api/runtime_state', fetcher);
  return {
    runtime: data,
    loading: !error && !data,
    error,
  };
}
