# File: analytics/model_audit.py

import os
import json
from collections import defaultdict
from datetime import datetime

REINFORCEMENT_PATH = "assistants/reinforcement_profile.jsonl"


def load_trades():
    if not os.path.exists(REINFORCEMENT_PATH):
        print("⚠️ No reinforcement profile found.")
        return []
    trades = []
    with open(REINFORCEMENT_PATH, "r") as f:
        for line in f:
            try:
                trades.append(json.loads(line.strip()))
            except:
                continue
    return trades


def analyze_by_model(trades):
    summary = defaultdict(lambda: {
        "total": 0,
        "wins": 0,
        "losses": 0,
        "pnl_total": 0.0,
        "avg_pnl": 0.0
    })

    for t in trades:
        version = t.get("model_version", "unknown")
        pnl = float(t.get("pnl", 0))
        entry = summary[version]
        entry["total"] += 1
        entry["pnl_total"] += pnl
        if pnl > 0:
            entry["wins"] += 1
        else:
            entry["losses"] += 1

    for version, stats in summary.items():
        stats["avg_pnl"] = round(stats["pnl_total"] / max(1, stats["total"]), 3)
        stats["win_rate"] = round(stats["wins"] / max(1, stats["total"]), 3)

    return summary


def print_summary(summary):
    print("\n📊 Model Performance Summary:")
    for version, stats in summary.items():
        print(f"\n🔹 {version}")
        for k, v in stats.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    trades = load_trades()
    summary = analyze_by_model(trades)
    print_summary(summary)
