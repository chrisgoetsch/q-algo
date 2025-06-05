# File: run_q_algo_live_async.py
"""Async live‑trading loop for Q‑ALGO v2
-------------------------------------------------
Responsible for:
• Bootstrapping Tradier/Polygon connectivity
• Real‑time entry evaluation and order submission
• Position management / exits
• High‑resolution runtime logging & heartbeat
"""

import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

from core.env_validator import validate_env  # validates & prints masked vars
from core.trade_engine import open_position  # submits live orders
from core.position_manager import manage_positions  # handles exits / PnL
from core.entry_learner import evaluate_entry  # scores new entries
from core.open_trade_tracker import (
    log_open_trade,
    sync_open_trades_with_tradier,
)
from core.recovery_manager import run_recovery
from core.runtime_state import update_runtime_state, load_runtime_state
from core.market_hours import is_market_open_now, get_market_status_string
from polygon.websocket_manager import start_polygon_listener
from core.capital_manager import (
    get_current_allocation,
    save_equity_baseline,
    evaluate_drawdown_throttle,
    compute_position_size,
)
from core.account_fetcher import fetch_tradier_equity

STATUS_PATH = "logs/status.json"
ACCOUNT_SUMMARY_PATH = "logs/account_summary.json"

# -----------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------

aSYNC_DELAY = 60  # seconds between loops

def load_json(path: str):
    """Safe JSON loader returning an empty dict on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        print(f"⚠️ Failed to load {path}. Initializing default.")
        return {}

async def async_sleep(seconds: int):
    await asyncio.sleep(seconds)

# -----------------------------------------------------------
# Main async loop
# -----------------------------------------------------------

async def main_loop():
    print("[Q Algo] Async Trading Session **Starting** with Tradier…")

    # 1️⃣  Environment / credential sanity‑check
    load_dotenv()
    validate_env(mask=True)  # will display masked keys

    # 2️⃣  One‑time boot actions
    fetch_tradier_equity()
    sync_open_trades_with_tradier()
    run_recovery()

    # 3️⃣  Start Polygon WebSocket listener (non‑blocking)
    asyncio.create_task(start_polygon_listener(["Q.SPY", "T.SPY"]))

    equity_baseline: float = 0

    # 4️⃣  Live loop
    while True:
        loop_ts = datetime.utcnow().isoformat(timespec="seconds")
        try:
            symbol = "SPY"
            status = load_json(STATUS_PATH)
            runtime_state = load_runtime_state()
            account = load_json(ACCOUNT_SUMMARY_PATH)
            acct_equity = fetch_tradier_equity() or 0

            # ─── Initialise equity baseline ────────────────────────
            if not equity_baseline and acct_equity > 0:
                equity_baseline = acct_equity
                save_equity_baseline(equity_baseline)

            # ─── Heart‑beat banner ─────────────────────────────────
            open_ct = len(runtime_state.get("open_trades", []))
            print(
                f"[Heartbeat] {loop_ts}  eq={acct_equity:,.0f}  open={open_ct}  mode={runtime_state.get('mode','init')}"
            )

            # ─── Safety: equity must not be 0 ──────────────────────
            if acct_equity == 0:
                print("❌ Tradier equity returned 0 – pausing until fixed.")
                update_runtime_state({"mesh_health": "halted", "error": "equity_zero"})
                await async_sleep(aSYNC_DELAY * 5)
                continue

            # ─── Kill‑switch / market hours checks ─────────────────
            if status.get("kill_switch", False):
                print("[Q Algo] 🚨 Kill switch is active. Pausing…")
                update_runtime_state({"mode": "paused", "mesh_health": "halted"})
                await async_sleep(aSYNC_DELAY)
                continue

            if not is_market_open_now():
                print(f"⏳ Market is {get_market_status_string()}. Waiting…")
                update_runtime_state({"mode": "waiting", "mesh_health": "idle"})
                await async_sleep(aSYNC_DELAY)
                continue

            # ─── Entry evaluation ─────────────────────────────────
            entry_score = await evaluate_entry(symbol)
            if entry_score:
                print("[Q Algo] ✅ Entry condition met. Opening position…")

                # Allocation & sizing
                base_alloc = get_current_allocation()
                throttle = evaluate_drawdown_throttle(acct_equity, equity_baseline)
                adjusted_alloc = compute_position_size(
                    round(base_alloc * throttle, 3), 1.0, 0.9, max_position_fraction=0.5
                )
                contracts = max(1, int(adjusted_alloc * 10))
                trade_id = f"{symbol}_{datetime.utcnow().isoformat()}"

                # Submit order via trade_engine (running in thread)
                order_resp = await asyncio.to_thread(open_position, symbol, contracts, "C")
                print(f"[ORDER] response ⇒ {order_resp}")

                # Log placeholder trade immediately (updated later by open_trade_tracker)
                log_open_trade(
                    trade_id,
                    agent="qthink",
                    direction="long",
                    strike=0,
                    expiry="0DTE",
                    meta={"allocation": adjusted_alloc, "contracts": contracts},
                )

                update_runtime_state(
                    {
                        "mode": "live",
                        "active_agents": ["qthink", "run_q_algo_live_async"],
                        "last_entry": datetime.utcnow().isoformat(),
                        "mesh_health": "stable",
                    }
                )

            # ─── Exit / position management ───────────────────────
            await asyncio.to_thread(manage_positions)
            update_runtime_state(
                {
                    "last_exit": datetime.utcnow().isoformat(),
                    "mesh_health": "stable",
                }
            )

        except Exception as e:
            print(f"[Q Algo Async] ❌ Exception: {e}")
            update_runtime_state(
                {
                    "mesh_health": "exception",
                    "error": f"{type(e).__name__}: {str(e)}",
                }
            )

        await async_sleep(aSYNC_DELAY)


# -----------------------------------------------------------
# Entry‑point
# -----------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main_loop())
