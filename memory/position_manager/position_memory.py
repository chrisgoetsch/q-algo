# position_memory.py
# Logs position exit decisions, trailing logic, and PnL performance for 
reinforcement

import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("memory/position_manager/pnl_decay_analysis.jsonl")


def log_exit_analysis(trade_id: str, exit_reason: str, pnl: float, 
max_pnl: float, trailing_stop_triggered: bool):
    """Logs metadata on how a trade exited and how much alpha decayed."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "trade_id": trade_id,
        "exit_reason": exit_reason,
        "pnl": pnl,
        "max_pnl": max_pnl,
        "trailing_stop_triggered": trailing_stop_triggered,
        "decay": round((max_pnl - pnl) / max_pnl, 3) if max_pnl > 0 else 0
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def fetch_recent_exits(limit: int = 20):
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]


if __name__ == "__main__":
    print(log_exit_analysis("SPY437C_20250423", "trailing stop hit", 0.42, 
0.71, True))

