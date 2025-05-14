# File: core/trade_logger.py

import os
import json
from datetime import datetime

LOGS_DIR = "logs"
EXIT_LOG_PATH = os.path.join(LOGS_DIR, "trade_exit_log.jsonl")
DECAY_LOG_PATH = "logs/alpha_decay_log.jsonl"

def log_alpha_decay(trade_id, symbol, time_decay, mesh_decay, alpha_decay, pnl=None, rationale=None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "trade_id": trade_id,
        "symbol": symbol,
        "time_decay": round(time_decay, 4),
        "mesh_decay": round(mesh_decay, 4),
        "alpha_decay": round(alpha_decay, 4),
        "pnl": pnl,
        "rationale": rationale or "n/a"
    }

    try:
        os.makedirs(os.path.dirname(DECAY_LOG_PATH), exist_ok=True)
        with open(DECAY_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[Alpha Decay Logger] Failed to log: {e}")
        
def log_exit(position, reason="unspecified"):
    """
    Logs a trade exit event with metadata.
    """
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": position.get("symbol"),
        "quantity": position.get("quantity"),
        "pnl": position.get("pnl", 0.0),
        "exit_reason": reason,
        "trade_type": position.get("trade_type", "0DTE"),
        "mesh_context": position.get("mesh_context", {}),
    }

    with open(EXIT_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"📝 Logged exit: {log_entry['symbol']} | Reason: {reason}")
