import React, { useState, useEffect } from "react";
import SignalCard from "../components/SignalCard";
import TradeLog from "../components/TradeLog";

const Dashboard = () => {
  const [trades, setTrades] = useState([]);
  const [signals, setSignals] = useState({});

  useEffect(() => {
    // Simulated signal + trade feed
    setSignals({
      Buy: "SPY 0DTE",
      Confidence: "82%",
      Risk: "Moderate"
    });
    setTrades([
      { entry_time: "09:33", symbol: "SPY", pnl: "+$125" },
      { entry_time: "10:12", symbol: "SPY", pnl: "-$40" }
    ]);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Q Algo Live Dashboard</h1>
      <div className="flex flex-wrap">
        {Object.entries(signals).map(([k, v]) => (
          <SignalCard key={k} title={k} value={v} />
        ))}
      </div>
      <TradeLog trades={trades} />
    </div>
  );
};

export default Dashboard;
