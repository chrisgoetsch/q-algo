# File: run_q_algo_live_async.py

import asyncio
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
from polygon.websocket_manager import start_polygon_listener
from core.open_trade_tracker import sync_open_trades_with_tradier
from core.capital_manager import (
    get_current_allocation,
    save_equity_baseline,
    load_equity_baseline,
    evaluate_drawdown_throttle,
    compute_position_size
)
from core.account_fetcher import fetch_tradier_equity

STATUS_PATH = "logs/status.json"
ACCOUNT_SUMMARY_PATH = "logs/account_summary.json"

async def async_sleep(seconds):
    await asyncio.sleep(seconds)

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        print(f"⚠️ Failed to load {path}. Initializing default.")
        return {}

async def main_loop():
    print("[Q Algo] Async Trading Session Starting with Tradier...")
    load_dotenv()

    # Initial sync before loop
    fetch_tradier_equity()
    sync_open_trades_with_tradier()
    run_recovery()

    # Start real-time Polygon WebSocket (SPY trades + quotes)
    asyncio.create_task(start_polygon_listener(["Q.SPY", "T.SPY"]))

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

            if status.get("kill_switch", False):
                print("[Q Algo] 🚨 Kill switch is active. Pausing...")
                update_runtime_state({"mode": "paused", "mesh_health": "halted"})
                await async_sleep(60)
                continue

            if not is_market_open_now():
                print(f"⏳ Market is {get_market_status_string()}. Waiting...")
                update_runtime_state({"mode": "waiting", "mesh_health": "idle"})
                await async_sleep(60)
                continue

            entry_score = await evaluate_entry(symbol)
            if entry_score:
                print("[Q Algo] ✅ Entry condition met. Opening position.")
                base_alloc = get_current_allocation()
                equity_now = account.get("equity", 0)
                throttle = evaluate_drawdown_throttle(equity_now, equity_baseline)
                adjusted_alloc = round(base_alloc * throttle, 3)

                adjusted_alloc = compute_position_size(
                    adjusted_alloc, 1.0, 0.9, max_position_fraction=0.5
                )
                contracts = max(1, int(adjusted_alloc * 10))
                trade_id = f"{symbol}_{datetime.utcnow().isoformat()}"

                print(f"[Q Algo] 🟢 Placing order: {symbol} × {contracts} contracts")

                await asyncio.to_thread(open_position, symbol, contracts, "C")
                log_open_trade(
                    trade_id,
                    agent="qthink",
                    direction="long",
                    strike=0,
                    expiry="0DTE",
                    meta={"allocation": adjusted_alloc, "contracts": contracts}
                )
                update_runtime_state({
                    "mode": "live",
                    "active_agents": ["qthink", "run_q_algo_live_async"],
                    "last_entry": datetime.utcnow().isoformat(),
                    "mesh_health": "stable"
                })

            await asyncio.to_thread(manage_positions)
            update_runtime_state({
                "last_exit": datetime.utcnow().isoformat(),
                "mesh_health": "stable"
            })

        except Exception as e:
            print(f"[Q Algo Async] ❌ Exception: {e}")
            update_runtime_state({
                "mesh_health": "exception",
                "error": f"{type(e).__name__}: {str(e)}"
            })

        await async_sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop())
