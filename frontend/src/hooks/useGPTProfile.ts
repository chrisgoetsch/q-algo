// ──────────────────────────────────────────────────────────────────────────
// src/hooks/useGPTProfile.ts

import useSWR from 'swr';
import fetcher from '../api/fetcher';

export interface GPTProfile {
  lastUpdated: number;   // UNIX ms timestamp
  labels: string[];      // e.g. ["Bullish setup", "Volatility spike"]
  comments: string;      // GPT’s commentary
  outlook: string;       // GPT’s “today’s outlook” text
}

export default function useGPTProfile() {
  const { data, error } = useSWR<GPTProfile>('/api/reinforcement', fetcher);
  return {
    profile: data,
    loading: !error && !data,
    error,
  };
}
