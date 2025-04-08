import React from "react";

const TradeLog = ({ trades }) => (
  <div className="bg-slate-700 p-4 rounded-xl m-4">
    <h2 className="text-xl mb-2 font-bold">Trade Log</h2>
    <ul>
      {trades.map((trade, i) => (
        <li key={i} className="border-b border-slate-600 py-1">
          {trade.entry_time} — {trade.symbol} — PnL: {trade.pnl}
        </li>
      ))}
    </ul>
  </div>
);

export default TradeLog;
