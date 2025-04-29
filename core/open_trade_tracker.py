# open_trade_tracker.py
# Q-ALGO v2 - Tracks open trades with atomic write + recovery fallback

import json
import os
from datetime import datetime

FILE = "logs/open_trades.jsonl"

def atomic_write_line(filepath, line_data):
    try:
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(json.dumps(line_data) + "\n")
        with open(filepath, "a") as f:
            f.write(json.dumps(line_data) + "\n")
        os.replace(tmp_path, filepath)
    except Exception as e:
        print(f"❌ Failed to write open trade log: {e}")

def log_open_trade(trade_id, agent, direction, strike, expiry):
    entry = {
        "trade_id": trade_id,
        "agent": agent,
        "direction": direction,
        "strike": strike,
        "expiry": expiry,
        "timestamp": datetime.utcnow().isoformat()
    }
    atomic_write_line(FILE, entry)

def load_open_trades():
    try:
        if not os.path.exists(FILE):
            return []
        with open(FILE, "r") as f:
            return [json.loads(line) for line in f if line.strip()]
    except json.JSONDecodeError:
        print(f"⚠️ JSON decode error in {FILE}, resetting...")
        with open(FILE, "w") as f:
            f.write("")  # Reset corrupted file
        return []
    except Exception as e:
        print(f"❌ Failed to load open trades: {e}")
        return []

def remove_trade(trade_id):
    trades = load_open_trades()
    updated = [t for t in trades if t.get("trade_id") != trade_id]
    try:
        with open(FILE, "w") as f:
            for t in updated:
                f.write(json.dumps(t) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to rewrite open_trades.jsonl: {e}")

