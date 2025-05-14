# File: core/open_trade_tracker.py
# Q-ALGO v2 — Tracks open trades with atomic write + recovery fallback

import json
import os
from datetime import datetime

FILE = os.getenv("OPEN_TRADES_FILE_PATH", "logs/open_trades.jsonl")

def atomic_write_line(filepath, line_data):
    """
    Atomically appends a single JSON line to the file,
    and writes a backup .tmp file in case of interruption.
    """
    try:
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(json.dumps(line_data) + "\n")
        os.replace(tmp_path, filepath)
        with open(filepath, "a") as f:
            f.write(json.dumps(line_data) + "\n")
    except Exception as e:
        print(f"❌ Failed to write open trade log: {e}")

def log_open_trade(trade_id, agent, direction, strike, expiry):
    """
    Legacy-compatible entry tracker.
    """
    entry = {
        "trade_id": trade_id,
        "agent": agent,
        "direction": direction,
        "strike": strike,
        "expiry": expiry,
        "timestamp": datetime.utcnow().isoformat()
    }
    atomic_write_line(FILE, entry)

def track_open_trade(symbol, context):
    """
    Mesh-aware trade tracker for entry logs.
    Writes rich entry context including required fields for recovery.
    """
    try:
        trade_id = context.get("trade_id", f"{symbol}_{datetime.utcnow().isoformat()}")
        direction = context.get("direction", "long")
        mesh_score = context.get("mesh_score", 100)
        pnl = context.get("pnl", 0.0)
        entry_time = context.get("timestamp", datetime.utcnow().isoformat())

        # Ensure minimum fields are present for manage_positions recovery
        entry = {
            "trade_id": trade_id,
            "symbol": symbol,
            "entry_time": entry_time,
            "direction": direction,
            "mesh_score": mesh_score,
            "pnl": pnl,
            "quantity": 1,
            "entry_context": context
        }

        atomic_write_line(FILE, entry)
        print(f"🟢 Tracked open trade: {symbol} (ID: {trade_id})")
    except Exception as e:
        print(f"⚠️ Failed to track open trade: {e}")

def load_open_trades():
    """
    Loads the list of open trades from file.
    Automatically resets corrupted file.
    """
    try:
        if not os.path.exists(FILE):
            return []
        with open(FILE, "r") as f:
            return [json.loads(line) for line in f if line.strip()]
    except json.JSONDecodeError:
        print(f"⚠️ JSON decode error in {FILE}, resetting...")
        with open(FILE, "w") as f:
            f.write("")
        return []
    except Exception as e:
        print(f"❌ Failed to load open trades: {e}")
        return []

def remove_trade(trade_id):
    """
    Removes a trade entry by its ID.
    """
    trades = load_open_trades()
    updated = [t for t in trades if t.get("trade_id") != trade_id]
    try:
        with open(FILE, "w") as f:
            for t in updated:
                f.write(json.dumps(t) + "\n")
        print(f"🧹 Removed trade: {trade_id}")
    except Exception as e:
        print(f"⚠️ Failed to rewrite open_trades.jsonl: {e}")
