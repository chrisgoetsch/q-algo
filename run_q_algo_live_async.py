# ─────────────────────────────────────────────────────────────────────────────
# File: run_q_algo_live_async.py           (v2-HF, no tuple unpack)
# ─────────────────────────────────────────────────────────────────────────────
"""
Async live-trading loop for Q-ALGO v2-HF (hedge-fund tuned)
"""

from __future__ import annotations
import os, sys, json, asyncio, backoff, openai
from datetime import datetime, timedelta
from contextlib import suppress
from dotenv import load_dotenv

from core.env_validator import validate_env
from core.trade_engine import open_position
from core.position_manager import manage_positions
from core.entry_learner import evaluate_entry
from core.open_trade_tracker import log_open_trade, sync_open_trades_with_tradier
from core.recovery_manager import run_recovery
from core.runtime_state import load_runtime_state
from core.market_hours import is_market_open_now, is_0dte_trading_window_now
from polygon.websocket_manager import start_polygon_listener
from core.capital_manager import (
    fetch_tradier_equity,
    get_tradier_buying_power,
    get_current_allocation,
    save_equity_baseline,
    evaluate_drawdown_throttle,
    compute_position_size,
)
from core.logger_setup  import get_logger
logger = get_logger(__name__)

# ── py3.10 TaskGroup shim ────────────────────────────────────────────────────
if sys.version_info < (3, 11):
    class _TG:                        # minimal shim
        def __init__(self): self._tasks=[]
        async def __aenter__(self): return self
        async def __aexit__(self, *_): await asyncio.gather(*self._tasks, return_exceptions=True)
        def create_task(self, coro):  self._tasks.append(asyncio.create_task(coro))
    asyncio.TaskGroup = _TG           # type: ignore

# ── Paths / constants ────────────────────────────────────────────────────────
STATUS_PATH          = "logs/status.json"
ASYNC_DELAY_MARKET   = 15   # s
ASYNC_DELAY_OFF      = 60   # s
SEND_GPT_EVERY       = 600  # s

openai.api_key = os.getenv("OPENAI_API_KEY", "")

# ── resilient equity fetch wrapped in back-off ───────────────────────────────
@backoff.on_exception(backoff.expo, Exception, max_time=30)
def _fetch_equity() -> float:
    return fetch_tradier_equity()

def _jload(path: str):
    with suppress(Exception):
        return json.load(open(path))
    return {}

# ── GPT heartbeat ────────────────────────────────────────────────────────────
async def _send_gpt_summary(runtime: dict, bp: float, eq: float):
    if not openai.api_key:
        return
    msg = f"q-algo heartbeat – eq ${eq:,.0f}, bp ${bp:,.0f}, open {len(runtime.get('open_trades', []))}"
    try:
        if hasattr(openai, "chat"):   # client ≥1.0
            await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": msg}],
            )
        else:                         # client 0.x
            await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": msg}],
            )
    except Exception as e:
        logger.warning({"event": "gpt_summary_fail", "err": str(e)})

# ── entry worker (runs inside TaskGroup) ─────────────────────────────────────
async def _entry_worker(acct_eq: float, baseline: float):
    if not await evaluate_entry("SPY"):
        return
    base_alloc = get_current_allocation()
    throttle   = evaluate_drawdown_throttle(acct_eq, baseline)
    alloc_pct  = compute_position_size(round(base_alloc * throttle, 3), 1.0, 0.9)
    contracts  = max(1, int(alloc_pct * 10))
    trade_id   = f"SPY_{datetime.utcnow().isoformat()}"

    order = await asyncio.to_thread(open_position, "SPY", contracts, "C")
    logger.info({"event": "order_submitted", "resp": order})

    log_open_trade(
        trade_id,
        agent="qthink",
        direction="long",
        strike=0,
        expiry="0DTE",
        meta={"allocation": alloc_pct, "contracts": contracts},
    )

# ── main async loop ──────────────────────────────────────────────────────────
async def main_loop():
    print("[Q-ALGO] Hedge-Fund loop booting…")
    load_dotenv();  validate_env()

    # one-time start-up
    _fetch_equity()
    sync_open_trades_with_tradier()
    run_recovery()
    asyncio.create_task(start_polygon_listener(["Q.SPY", "T.SPY"]))

    equity_baseline = 0.0
    last_gpt_push   = datetime.utcnow() - timedelta(seconds=SEND_GPT_EVERY)

    while True:
        runtime = load_runtime_state()
        status  = _jload(STATUS_PATH)

        eq = _fetch_equity()
        bp = get_tradier_buying_power()

        if not equity_baseline and eq:
            equity_baseline = eq
            save_equity_baseline(eq)

        # kill-switch
        if status.get("kill_switch"):
            logger.warning({"event": "kill_switch_active"})
            await asyncio.sleep(ASYNC_DELAY_OFF)
            continue

        market_open = is_market_open_now()
        loop_delay  = ASYNC_DELAY_MARKET if market_open else ASYNC_DELAY_OFF

        # TaskGroup: manage exits + maybe check entries
        async with asyncio.TaskGroup() as tg:
            tg.create_task(asyncio.to_thread(manage_positions))
            if market_open and is_0dte_trading_window_now():
                tg.create_task(_entry_worker(eq, equity_baseline))

        # GPT summary
        now = datetime.utcnow()
        if (now - last_gpt_push).total_seconds() >= SEND_GPT_EVERY:
            asyncio.create_task(_send_gpt_summary(runtime, bp, eq))
            last_gpt_push = now

        await asyncio.sleep(loop_delay)

# ── entry-point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main_loop())
