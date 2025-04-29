import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Switch } from "@/components/ui/Switch";
import { Slider } from "@/components/ui/Slider";

export default function Dashboard() {
  const [killSwitch, setKillSwitch] = useState(false);
  const [capitalAllocation, setCapitalAllocation] = useState(0.2);
  const [runtimeState, setRuntimeState] = useState<any>({});
  const [openTrades, setOpenTrades] = useState<any[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("/logs/status.json")
        .then((res) => res.json())
        .then((data) => {
          setKillSwitch(data.kill_switch);
          setCapitalAllocation(data.capital_allocation);
        });

      fetch("/logs/runtime_state.json")
        .then((res) => res.json())
        .then((data) => setRuntimeState(data));

      fetch("/logs/open_trades.jsonl")
        .then((res) => res.text())
        .then((text) => {
          const lines = text.trim().split("\n");
          const trades = lines.map((line) => JSON.parse(line));
          setOpenTrades(trades);
        });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleKillSwitchToggle = async () => {
    const newStatus = !killSwitch;
    setKillSwitch(newStatus);
    await fetch("/logs/status.json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kill_switch: newStatus, capital_allocation: capitalAllocation }),
    });
  };

  const handleCapitalChange = async (val: number[]) => {
    const allocation = val[0] / 100;
    setCapitalAllocation(allocation);
    await fetch("/logs/status.json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kill_switch: killSwitch, capital_allocation: allocation }),
    });
  };

  return (
    <div className="grid grid-cols-1 gap-6 p-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardContent className="p-4">
          <h2 className="text-xl font-bold">Kill Switch</h2>
          <Switch checked={killSwitch} onCheckedChange={handleKillSwitchToggle} />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <h2 className="text-xl font-bold">Capital Allocation</h2>
          <Slider defaultValue={[capitalAllocation * 100]} max={100} step={1} onValueChange={handleCapitalChange} />
          <p>{(capitalAllocation * 100).toFixed(0)}%</p>
        </CardContent>
      </Card>
      <Card className="col-span-2">
        <CardContent className="p-4">
          <h2 className="text-xl font-bold mb-2">Runtime State</h2>
          <pre className="text-sm bg-black text-white p-2 rounded overflow-x-auto">
            {JSON.stringify(runtimeState, null, 2)}
          </pre>
        </CardContent>
      </Card>
      <Card className="col-span-3">
        <CardContent className="p-4">
          <h2 className="text-xl font-bold mb-2">Open Trades</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {openTrades.map((trade, idx) => (
              <div key={idx} className="border p-2 rounded bg-gray-900 text-white">
                <pre>{JSON.stringify(trade, null, 2)}</pre>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
