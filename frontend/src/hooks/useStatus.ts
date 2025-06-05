// ──────────────────────────────────────────────────────────────────────────
// src/hooks/useStatus.ts

import useSWR from 'swr';
import fetcher from '../api/fetcher';

export interface Status {
  killSwitch: boolean;
  capitalAllocation: number;
}

export default function useStatus() {
  const { data, error, mutate } = useSWR<Status>('/api/status', fetcher);

  const updateStatus = async (patch: Partial<Status>) => {
    await fetcher('/api/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    await mutate(); // revalidate
  };

  return {
    status: data,
    loading: !error && !data,
    error,
    updateStatus,
  };
}

