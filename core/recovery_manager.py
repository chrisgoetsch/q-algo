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
    # You can hook into position_manager here
    # For example, you could pass to manage_positions(trade)
    # But in most cases, manage_positions() already checks all active trades
    # This function is a placeholder to integrate deeper control later
    pass

def run_recovery():
    trades = load_open_trades()
    for trade in trades:
        resume_trade_monitoring(trade)

if __name__ == "__main__":
    run_recovery()
