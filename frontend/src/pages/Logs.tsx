import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";

export default function Logs() {
  const [tradeLogs, setTradeLogs] = useState<any[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch("/logs/trade_flow/trades.jsonl");
        const text = await response.text();
        const lines = text.trim().split("\n");
        const parsed = lines.map((line) => JSON.parse(line));
        setTradeLogs(parsed.reverse()); // show most recent first
      } catch (error) {
        console.error("Failed to load trade logs:", error);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Trade Flow Log</h1>
      {tradeLogs.length === 0 ? (
        <p className="text-zinc-400">No trade logs found.</p>
      ) : (
        tradeLogs.map((log, idx) => (
          <Card key={idx}>
            <CardContent className="p-4 text-white bg-zinc-900 overflow-x-auto">
              <pre>{JSON.stringify(log, null, 2)}</pre>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
