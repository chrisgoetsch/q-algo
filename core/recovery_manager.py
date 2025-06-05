# recovery_manager.py
import json
import os
from datetime import datetime

OPEN_TRADES_PATH = "logs/open_trades.jsonl"

def load_open_trades():
    if not os.path.exists(OPEN_TRADES_PATH):
        print("🔍 No open trades log found.")
        return []

    trades = []
    try:
        with open(OPEN_TRADES_PATH, "r") as f:
            for line in f:
                trade = json.loads(line.strip())
                trades.append(trade)
        print(f"🔄 Loaded {len(trades)} open trades for recovery.")
        return trades
    except Exception as e:
        print(f"❌ Failed to load open trades: {e}")
        return []

def resume_trade_monitoring(trade):
    print(f"🔁 Resuming monitoring for: {trade['trade_id']}")
    # Hook into position manager or a direct trade monitor here in the future
    pass

def run_recovery():
    trades = load_open_trades()
    for trade in trades:
        resume_trade_monitoring(trade)

if __name__ == "__main__":
    run_recovery()
