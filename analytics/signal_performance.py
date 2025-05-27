import json
from collections import defaultdict
import pandas as pd

SIGNAL_LOG = "logs/mesh_signals.jsonl"
TRADE_LOG = "logs/trades.jsonl"

def load_jsonl(filepath):
    with open(filepath, "r") as f:
        return [json.loads(line) for line in f]

def analyze_signals():
    signals = load_jsonl(SIGNAL_LOG)
    trades = load_jsonl(TRADE_LOG)

    # Join trades to signals by signal_id
    trades_by_signal = {t["signal_id"]: t for t in trades if "signal_id" in t}

    results = defaultdict(list)

    for sig in signals:
        sid = sig["signal_id"]
        agent = sig["agent"]
        if sid in trades_by_signal:
            trade = trades_by_signal[sid]
            pnl = trade.get("pnl", 0.0)
            results[agent].append(pnl)

    summary = {
        agent: {
            "count": len(pnls),
            "hit_rate": sum(1 for p in pnls if p > 0) / len(pnls) if pnls else 0,
            "avg_return": sum(pnls) / len(pnls) if pnls else 0
        }
        for agent, pnls in results.items()
    }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    analyze_signals()
