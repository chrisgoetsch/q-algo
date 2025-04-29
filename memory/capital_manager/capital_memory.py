# capital_memory.py
# Tracks daily capital allocation, scaling events, and net result updates

import json
from datetime import datetime
from pathlib import Path

STATE_PATH = Path("memory/capital_manager/capital_state.json")
LOG_PATH = Path("memory/capital_manager/performance_log.jsonl")


def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    return {
        "total_equity": 100000.0,
        "allocated_pct": 0.2,
        "drawdown_flag": False,
        "current_day_pnl": 0.0,
        "daily_result_log": []
    }

def save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def update_capital_on_result(trade_id: str, pnl: float):
    state = load_state()
    state["current_day_pnl"] += pnl
    state["daily_result_log"].append({
        "trade_id": trade_id,
        "pnl": pnl,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_state(state)
    log_daily_event(trade_id, pnl)


def log_daily_event(trade_id: str, pnl: float):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "trade_id": trade_id,
        "pnl": pnl
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


def fetch_daily_log(limit: int = 25):
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]


if __name__ == "__main__":
    update_capital_on_result("SPY438C_TEST", pnl=0.23)

