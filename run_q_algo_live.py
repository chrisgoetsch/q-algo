# File: run_q_algo_live.py

import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from core.trade_engine import open_position
from core.position_manager import manage_positions
from core.entry_learner import evaluate_entry
from core.open_trade_tracker import log_open_trade
from core.recovery_manager import run_recovery
from core.runtime_state import update_runtime_state, load_runtime_state

sys.path = [p for p in sys.path if not p.endswith('/memory')]

STATUS_PATH = "logs/status.json"

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        print(f"⚠️ Failed to load {path}. Initializing default.")
        return {}

def write_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Q Algo] Failed to write {path}: {e}")

def main_loop():
    print("[Q Algo] Live Trading Session Starting with Tradier...")

    load_dotenv()
    run_recovery()

    while True:
        try:
            symbol = "SPY"
            status = load_json(STATUS_PATH)
            runtime_state = load_runtime_state()

            if not status:
                status = {"kill_switch": False}
            if status.get("kill_switch", True):
                print("[Q Algo] Kill switch is active. Pausing trade loop.")
                update_runtime_state({"mode": "paused", "mesh_health": "halted"})
                time.sleep(60)
                continue

            if evaluate_entry(symbol):
                print("[Q Algo] Entry condition met. Opening position.")
                open_position(symbol, 1, "C")

                trade_id = f"{symbol}_{datetime.utcnow().isoformat()}"
                log_open_trade(trade_id, agent="qthink", direction="long", strike=0, expiry="0DTE")

                update_runtime_state({
                    "mode": "live",
                    "active_agents": ["qthink", "run_q_algo_live"],
                    "last_entry": datetime.utcnow().isoformat(),
                    "mesh_health": "stable"
                })

            try:
                manage_positions()
                update_runtime_state({
                    "last_exit": datetime.utcnow().isoformat(),
                    "mesh_health": "stable"
                })
            except Exception as e:
                print(f"[Q Algo] ⚠️ manage_positions error: {e}")
                update_runtime_state({"mesh_health": "error", "error_detail": str(e)})

            time.sleep(60)

        except Exception as e:
            print(f"[Q Algo] Exception caught in main loop: {e}")
            update_runtime_state({"mesh_health": "exception", "error": str(e)})
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
