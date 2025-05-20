# File: run_q_algo_live.py

import traceback
import time
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from core.trade_engine import open_position
from core.position_manager import manage_positions
from core.entry_learner import evaluate_entry
from core.open_trade_tracker import log_open_trade
from core.recovery_manager import run_recovery
from core.runtime_state import update_runtime_state, load_runtime_state
from core.market_hours import is_market_open_now, get_market_status_string
from core.capital_manager import (
    get_current_allocation,
    save_equity_baseline,
    load_equity_baseline,
    evaluate_drawdown_throttle,
    compute_position_size
)
from core.account_fetcher import fetch_tradier_equity  # ✅ NEW: auto-fetch equity

sys.path = [p for p in sys.path if not p.endswith('/memory')]

STATUS_PATH = "logs/status.json"
ACCOUNT_SUMMARY_PATH = "logs/account_summary.json"
MESH_LOGGER_PATH = "logs/mesh_logger.jsonl"
QTHINK_DIALOGS_PATH = "logs/qthink_dialogs.jsonl"

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

def get_latest_gpt_confidence():
    try:
        with open(QTHINK_DIALOGS_PATH, "r") as f:
            lines = f.readlines()
            if lines:
                latest = json.loads(lines[-1])
                return float(latest.get("confidence", 0.5))
    except Exception as e:
        print(f"⚠️ Failed to read GPT confidence: {e}")
    return 0.5

def get_latest_mesh_score():
    try:
        with open(MESH_LOGGER_PATH, "r") as f:
            lines = f.readlines()
            if lines:
                latest = json.loads(lines[-1])
                return float(latest.get("mesh_score", 0.5))
    except Exception as e:
        print(f"⚠️ Failed to read mesh score: {e}")
    return 0.5

def main_loop():
    print("[Q Algo] Live Trading Session Starting with Tradier...")
    load_dotenv()
    run_recovery()
    fetch_tradier_equity()  # ✅ NEW: populate logs/account_summary.json if missing

    equity_baseline = 0

    while True:
        try:
            symbol = "SPY"
            status = load_json(STATUS_PATH)
            runtime_state = load_runtime_state()
            account = load_json(ACCOUNT_SUMMARY_PATH)

            if not equity_baseline and account.get("equity", 0) > 0:
                equity_baseline = account["equity"]
                save_equity_baseline(equity_baseline)

            if not status:
                status = {"kill_switch": False}
            if status.get("kill_switch", True):
                print("[Q Algo] Kill switch is active. Pausing trade loop.")
                update_runtime_state({"mode": "paused", "mesh_health": "halted"})
                time.sleep(60)
                continue

            if not is_market_open_now():
                print(f"⏳ Market is currently {get_market_status_string()}. Waiting for open...")
                update_runtime_state({"mode": "waiting", "mesh_health": "idle"})
                time.sleep(60)
                continue

            try:
                entry_score = evaluate_entry(symbol)
                with open("logs/entry_trace.jsonl", "a") as f:
                    f.write(json.dumps({
                        "timestamp": datetime.utcnow().isoformat(),
                        "symbol": symbol,
                        "entry_decision": bool(entry_score),
                        "confidence": float(entry_score) if isinstance(entry_score, (float, int)) else None
                    }) + "\n")
            except Exception as e:
                print(f"⚠️ Failed to log entry evaluation: {e}")

            if entry_score:
                print("[Q Algo] Entry condition met. Opening position.")
                base_allocation = get_current_allocation()
                equity_now = account.get("equity", 0)
                throttle = evaluate_drawdown_throttle(equity_now, equity_baseline)
                adjusted_allocation = round(base_allocation * throttle, 3)

                mesh_score = get_latest_mesh_score()
                gpt_confidence = get_latest_gpt_confidence()
                adjusted_allocation = compute_position_size(
                    adjusted_allocation,
                    mesh_score,
                    gpt_confidence,
                    max_position_fraction=0.5
                )

                print(f"[Capital Manager] Final capital allocation after tiers: {adjusted_allocation * 100:.1f}%")
                contracts = max(1, int(adjusted_allocation * 10))

                trade_id = f"{symbol}_{datetime.utcnow().isoformat()}"

                try:
                    open_position(symbol, contracts, "C")
                except Exception as e:
                    print(f"❌ Failed to open position: {e}")
                    with open("logs/trade_errors.jsonl", "a") as err_log:
                        err_log.write(json.dumps({
                            "timestamp": datetime.utcnow().isoformat(),
                            "symbol": symbol,
                            "allocation": adjusted_allocation,
                            "contracts": contracts,
                            "error": str(e)
                        }) + "\n")
                    continue

                sync_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "contracts": contracts,
                    "allocation": adjusted_allocation,
                    "mesh_score": mesh_score,
                    "gpt_confidence": gpt_confidence,
                    "source": "run_q_algo_live",
                    "agent": "qthink",
                    "action": "entry"
                }
                try:
                    with open("logs/sync_log.jsonl", "a") as sync_log:
                        sync_log.write(json.dumps(sync_entry) + "\n")
                except Exception as e:
                    print(f"⚠️ Failed to write to sync_log.jsonl: {e}")

                log_open_trade(
                    trade_id,
                    agent="qthink",
                    direction="long",
                    strike=0,
                    expiry="0DTE",
                    meta={
                        "mesh_score": mesh_score,
                        "gpt_confidence": gpt_confidence,
                        "allocation": adjusted_allocation,
                        "contracts": contracts
                    }
                )

                update_runtime_state({
                    "mode": "live",
                    "active_agents": ["qthink", "run_q_algo_live"],
                    "last_entry": datetime.utcnow().isoformat(),
                    "mesh_health": "stable"
                })

            try:
                manage_positions()
                try:
                    with open("logs/open_trades.jsonl", "r") as f:
                        trades = [json.loads(line.strip()) for line in f.readlines()]
                except:
                    trades = []

                for trade in trades:
                    if trade.get("status") == "closed":
                        sync_entry = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "trade_id": trade.get("trade_id"),
                            "symbol": trade.get("symbol", "SPY"),
                            "action": "exit",
                            "exit_price": trade.get("exit_price"),
                            "exit_reason": trade.get("exit_reason", "n/a"),
                            "pnl": trade.get("pnl", 0),
                            "mesh_score": trade.get("meta", {}).get("mesh_score"),
                            "gpt_confidence": trade.get("meta", {}).get("gpt_confidence"),
                            "allocation": trade.get("meta", {}).get("allocation"),
                            "contracts": trade.get("meta", {}).get("contracts"),
                            "agent": trade.get("agent", "qthink")
                        }
                        with open("logs/sync_log.jsonl", "a") as f:
                            f.write(json.dumps(sync_entry) + "\n")

                update_runtime_state({
                    "last_exit": datetime.utcnow().isoformat(),
                    "mesh_health": "stable"
                })
            except Exception as e:
                print(f"[Q Algo] ⚠️ manage_positions error: {e}")
                update_runtime_state({"mesh_health": "error", "error_detail": str(e)})

            time.sleep(60)

        except Exception as e:
            print(f"[Q Algo] Exception caught in main loop:\n{traceback.format_exc()}")
            update_runtime_state({
                "mesh_health": "exception",
                "error": f"{type(e).__name__}: {str(e)}"
            })

        time.sleep(60)

if __name__ == "__main__":
    main_loop()
