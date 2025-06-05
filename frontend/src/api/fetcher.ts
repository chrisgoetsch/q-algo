// ──────────────────────────────────────────────────────────────────────────
// src/api/fetcher.ts

export default async function fetcher(
  input: RequestInfo,
  init?: RequestInit
): Promise<any> {
  const res = await fetch(input, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Fetch error ${res.status}: ${text}`);
  }
  return res.json();
}
