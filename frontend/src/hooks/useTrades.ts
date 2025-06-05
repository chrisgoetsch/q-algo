// ──────────────────────────────────────────────────────────────────────────
// src/hooks/useTrades.ts

import useSWR from 'swr';
import fetcher from '../api/fetcher';

export interface Trade {
  timestamp: number;
  direction: 'BUY' | 'SELL';
  strike: string;      // e.g. "SPY_20250620_450_C"
  pnl: number;
  agent: string;
  exitReason: string;
}

export default function useTrades() {
  const { data, error } = useSWR<Trade[]>('/api/logs/trades', fetcher);
  return {
    trades: data,
    loading: !error && !data,
    error,
  };
}
