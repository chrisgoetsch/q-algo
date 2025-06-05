# File: analytics/summarize_trades.py

import os
import json
from collections import defaultdict
from datetime import datetime

OPEN_TRADES_PATH = "logs/open_trades.jsonl"
CLOSED_TRADES_PATH = "logs/closed_trades.jsonl"


def load_trades(path):
    trades = []
    if not os.path.exists(path):
        return trades
    with open(path, "r") as f:
        for line in f:
            try:
                trades.append(json.loads(line.strip()))
            except:
                continue
    return trades


def summarize_trades(trades):
    summary = defaultdict(lambda: {
        "total": 0,
        "wins": 0,
        "losses": 0,
        "pnl_total": 0.0,
        "avg_pnl": 0.0,
        "gpt_avg_conf": 0.0,
        "gpt_exit_count": 0
    })

    for t in trades:
        symbol = t.get("symbol", "UNKNOWN")
        root = symbol.split("O:")[-1][:3] if ":" in symbol else symbol[:3]  # SPY, AAPL, etc.
        pnl = float(t.get("pnl", 0))
        gpt_conf = float(t.get("gpt_confidence", 0))
        gpt_used = bool(t.get("gpt_exit_signal"))

        entry = summary[root]
        entry["total"] += 1
        entry["pnl_total"] += pnl
        if pnl > 0:
            entry["wins"] += 1
        else:
            entry["losses"] += 1
        if gpt_used:
            entry["gpt_exit_count"] += 1
            entry["gpt_avg_conf"] += gpt_conf

    for k, v in summary.items():
        v["avg_pnl"] = round(v["pnl_total"] / max(1, v["total"]), 4)
        if v["gpt_exit_count"]:
            v["gpt_avg_conf"] = round(v["gpt_avg_conf"] / v["gpt_exit_count"], 3)

    return summary


def print_summary(summary):
    print("\n📊 Trade Summary by Symbol Root:")
    for symbol, stats in summary.items():
        print(f"\n🔹 {symbol}")
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    open_trades = load_trades(OPEN_TRADES_PATH)
    closed_trades = load_trades(CLOSED_TRADES_PATH)
    summary = summarize_trades(open_trades + closed_trades)
    print_summary(summary)
