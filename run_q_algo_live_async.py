# File: run_q_algo_live_async.py — FINALIZED for Quant-Grade Execution Loop
# Q-ALGO V2 Live Trading Orchestrator

from __future__ import annotations
import asyncio, signal, time, os
from datetime import datetime
from dotenv import load_dotenv

from core.env_validator import validate_env
from core.logger_setup import get_logger
from preflight_check import run_preflight_check
from core.reconciliation import reconcile_open_trades
from core.recovery_manager import run_recovery
from core.runtime_state import update_runtime_state
from core.capital_manager import (
    fetch_tradier_equity, get_tradier_buying_power,
    get_current_allocation, evaluate_drawdown_throttle,
    compute_position_size, poll_balance_loop
)
from core.position_manager import manage_positions
from core.entry_learner import evaluate_entry
from core.open_trade_tracker import log_open_trade, load_open_trades
from core.trade_engine import open_position
from core.telegram_alerts import send_telegram_alert
from core.tradier_execution import get_atm_option_symbol
from polygon.polygon_websocket import start_polygon_listener, SPY_LIVE_PRICE
from polygon.stocks_websocket import start_spy_price_listener
from core.market_hours import is_market_open_now, get_market_status_string, is_0dte_trading_window_now
from analytics.technical_indicators import get_rsi, is_vwap_reclaim
from core.mesh_router import summarize_votes
from mesh.q_think import _log_qthink_summary

logger = get_logger(__name__)

_HEARTBEAT_INTERVAL = 10
_CYCLE_PAUSE = 2
ENTRY_THRESHOLD = 0.55
MAX_WS_IDLE_SECONDS = 300

_shutdown = asyncio.Event()
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda *_: _shutdown.set())

async def _heartbeat():
    while not _shutdown.is_set():
        try:
            eq = fetch_tradier_equity()
            bp = get_tradier_buying_power()
            mid = SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade")
            ts = datetime.utcnow().strftime("%H:%M:%S")
            print(f"🎯 {ts} | eq ${eq:,.0f} bp ${bp:,.0f} mid {mid} | 0-DTE {'OPEN' if is_0dte_trading_window_now() else 'CLOSED'}")
        except Exception as e:
            logger.error({"event": "heartbeat_fail", "err": str(e)})
        await asyncio.sleep(_HEARTBEAT_INTERVAL)

async def _entry_cycle():
    print("\n🔍 Evaluating entry signal...")
    if not is_0dte_trading_window_now():
        print("⌛ Market closed or not within 0-DTE window.")
        return

    try:
        equity = fetch_tradier_equity()
    except Exception as e:
        print(f"⚠️ Failed to fetch equity: {e}")
        return

    if equity < 100:
        print("❌ Insufficient equity.")
        return

    try:
        open_trades = load_open_trades()
    except Exception as e:
        print(f"⚠️ Could not load open trades: {e}")
        open_trades = []

    if open_trades:
        print("⏳ Skipping entry: open position exists.")
        return

    meta = await evaluate_entry(default_threshold=ENTRY_THRESHOLD, want_meta=True)
    if not meta.get("passes"):
        print(f"⚪ Entry rejected: score {meta.get('score', 0):.2f}")
        return

    score = meta["score"]
    rationale = meta["rationale"]
    regime = meta.get("regime", "unknown")
    rsi = get_rsi("SPY")
    vwap = is_vwap_reclaim("SPY")
    mesh = meta.get("agent_signals", {})
    mesh_score = summarize_votes(mesh)
    gpt_bias = meta.get("gpt_reasoning", "n/a").lower()

    bullish_agents = sum(1 for v in mesh.values() if v > 0.5)
    bearish_agents = sum(1 for v in mesh.values() if v < -0.5)

    vote_call = 0
    vote_put = 0
    if rsi < 35: vote_call += 1
    elif rsi > 70: vote_put += 1
    if vwap: vote_call += 1
    else: vote_put += 1
    if bullish_agents > bearish_agents: vote_call += 1
    elif bearish_agents > bullish_agents: vote_put += 1
    if "bullish" in gpt_bias: vote_call += 1
    elif "bearish" in gpt_bias: vote_put += 1

    side = "CALL" if vote_call > vote_put else "PUT"
    option_type = "C" if side == "CALL" else "P"

    opt_symbol = get_atm_option_symbol("SPY", call_put=option_type)
    if not opt_symbol:
        print("❌ Failed to resolve ATM option.")
        return

    alloc = get_current_allocation()
    throttle = evaluate_drawdown_throttle(equity, equity)
    pos_size = compute_position_size(alloc * throttle, 1, 0.9)
    contracts = max(1, round(pos_size * 10 * (mesh_score / 100) * score))

    print(f"\n✅ Entry score: {score:.3f} | regime: {regime} | rationale: {rationale}")
    print(f"📊 {side} {contracts}x SPY | alloc={alloc:.2f} x throttle={throttle:.2f} → {alloc * throttle:.2f}")

    try:
        order = open_position(
            symbol=opt_symbol,
            contracts=contracts,
            option_type=option_type,
            score=score,
            rationale=rationale
        )
        print(f"🚀 Order submitted → {order.get('order_id')} | tracking {order.get('trade_id')}")

        update_runtime_state({
            "last_trade_attempt": datetime.utcnow().isoformat(),
            "mesh_score": mesh_score,
            "regime": regime,
            "entry_score": score
        })

        _log_qthink_summary({
            "agent": "q_think",
            "score": score,
            "direction": side.lower(),
            "rationale": rationale,
            "mesh_votes": mesh,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        print(f"❌ Order failed: {e}")

async def main():
    load_dotenv()
    validate_env()
    run_preflight_check()
    reconcile_open_trades()
    run_recovery()
    start_polygon_listener()
    start_spy_price_listener()
    asyncio.create_task(poll_balance_loop())
    asyncio.create_task(_heartbeat())

    while not _shutdown.is_set():
        start = time.time()
        if not is_market_open_now():
            print(f"⌛ {datetime.utcnow().isoformat()} - Market closed. Sleeping 30s...")
            await asyncio.sleep(30)
            continue

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(asyncio.to_thread(manage_positions))
                tg.create_task(_entry_cycle())

            last_ts = SPY_LIVE_PRICE.get("timestamp") or 0
            if (time.time() - last_ts) > MAX_WS_IDLE_SECONDS:
                print("⚠️ WebSocket stale. Restarting listener.")
                start_polygon_listener()

            print(f"✅ Loop cycle completed in {time.time() - start:.2f}s\n")
        except Exception as exc:
            print(f"⚠️ Loop error: {exc}")
            logger.exception({"event": "main_loop_exception", "err": str(exc)})
        await asyncio.sleep(_CYCLE_PAUSE)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Graceful shutdown initiated.")
