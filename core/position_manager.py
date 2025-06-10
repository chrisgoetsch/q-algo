# ─────────────────────────────────────────────────────────────────────────────
# File: core/position_manager.py  — FULL VERSION (final)
# ─────────────────────────────────────────────────────────────────────────────
"""Real‑time position supervision for Q‑ALGO v2
================================================
Fetches live positions, computes decay & PnL, evaluates mesh + GPT exit triggers,
submits sell‑to‑close orders, and logs everything for reinforcement learning and
UI dashboards.
"""
from __future__ import annotations

import os, json, asyncio
from datetime import datetime
from typing import Dict, List

from core.tradier_execution import submit_order
from core.tradier_client import get_positions, get_order_status
from analytics.qthink_log_labeler import label_exit_reason, process_and_journal
from core.trade_logger import log_exit, log_alpha_decay
from core.mesh_router import score_exit_signals
from core.qthink_scenario_planner import simulate_market_scenario
from core.close_trade_tracker import log_closed_trade
from core.capital_manager import log_allocation_update
from core.logger_setup import logger
from core.threshold_manager import get_exit_threshold
from core.alpha_decay_tracker import calculate_time_decay, calculate_mesh_decay
from analytics.qthink_feedback_loop import (
    process_trade_for_learning,
    load_reinforcement_profile,
)
from core.gpt_exit_analyzer import analyze_exit_with_gpt
from polygon.polygon_rest import get_option_metrics, get_dealer_flow_metrics
from polygon.polygon_websocket import SPY_LIVE_PRICE
from core.mesh_optimizer import evaluate_agents

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
LOGS_DIR = "logs"
SYNC_LOG_PATH = os.path.join(LOGS_DIR, "sync_log.jsonl")
EXIT_ATTEMPTS_LOG = os.path.join(LOGS_DIR, "exit_attempts.jsonl")
OPEN_TRADES_PATH = os.path.join(LOGS_DIR, "open_trades.jsonl")
REINFORCEMENT_PROFILE_PATH = "assistants/reinforcement_profile.json"

# ---------------------------------------------------------------------------
# Low‑level helpers
# ---------------------------------------------------------------------------

def _atomic_log(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(obj) + "\n")


def get_price() -> float:
    return SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade") or 0.0


def log_exit_attempt(symbol: str, qty: int, response: Dict):
    _atomic_log(EXIT_ATTEMPTS_LOG, {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "quantity": qty,
        "response": response,
    })


def update_sync_log_with_outcome(option_symbol: str, outcome: str):
    _atomic_log(SYNC_LOG_PATH, {
        "timestamp": datetime.utcnow().isoformat(),
        "option_symbol": option_symbol,
        "exit_result": outcome,
    })

# ---------------------------------------------------------------------------
# Tradier wrappers
# ---------------------------------------------------------------------------

def get_open_positions() -> Dict[str, List[dict]]:
    try:
        raw = get_positions().get("positions", [])
        return {"positions": [p for p in raw if isinstance(p, dict)]}
    except Exception as e:
        logger.error({"event": "get_positions_fail", "error": str(e)})
        return {"positions": []}


def confirm_order_success(order_id: str) -> bool:
    try:
        status = get_order_status(order_id).get("order", {}).get("status", "unknown")
        return status == "ok"
    except Exception as e:
        logger.error({"event": "confirm_order_failed", "error": str(e)})
        return False

# ---------------------------------------------------------------------------
# GPT + mesh exit evaluation
# ---------------------------------------------------------------------------

def evaluate_exit(context: dict, position: dict):
    profile = load_reinforcement_profile()
    exit_cutoff = profile.get("suggested_exit_decay", 0.6)

    score_data = score_exit_signals(context, position)
    exit_signal = score_data.get("signal", "hold")
    exit_confidence = score_data.get("confidence", 0.0)

    pnl = position.get("pnl", 0.0)
    decay = context.get("alpha_decay", 0.0)

    simulated_context = simulate_market_scenario(context)
    regime = simulated_context.get("regime", "unknown")
    context.update({
        "regime": regime,
        "exit_signal": exit_signal,
        "exit_confidence": exit_confidence,
        "trade_id": position.get("trade_id"),
    })

    async def decide():
        gpt_decision = await analyze_exit_with_gpt(context, context["trade_id"])
        gpt_signal = gpt_decision.get("signal", "hold")
        gpt_conf = gpt_decision.get("confidence", 0.5)
        context.update({
            "gpt_exit_signal": gpt_signal,
            "gpt_confidence": gpt_conf,
            "gpt_rationale": gpt_decision.get("rationale", "n/a"),
            "reinforcement_label": f"gpt_exit:{gpt_signal}",
        })

        exit_thresh = get_exit_threshold()
        should_exit = (
            (exit_signal == "exit" and exit_confidence >= exit_thresh)
            or pnl < -0.3
            or decay > exit_cutoff
            or regime in ["panic", "compressing"]
            or (gpt_signal == "exit" and gpt_conf >= 0.65)
        )
        rationale = label_exit_reason(pnl=pnl, decay=decay, mesh_signal=exit_signal)
        return should_exit, rationale, regime

    return asyncio.run(decide())

# ---------------------------------------------------------------------------
# Exit workflow
# ---------------------------------------------------------------------------

def exit_trade(position: Dict, regime: str) -> bool:
    symbol = position.get("symbol")
    qty = int(position.get("quantity", 1))
    trade_id = position.get("trade_id", symbol)

    print(f"[EXIT] Closing position {symbol} ×{qty}")
    response = submit_order(option_symbol=symbol, qty=qty, side="sell_to_close")
    log_exit_attempt(symbol, qty, response)

    if response.get("status") == "rejected":
        print(f"🛑 Tradier rejected exit order: {response}")
        return False

    order_id = response.get("order", {}).get("id") or response.get("order_id")
    if not order_id or not confirm_order_success(order_id):
        logger.error({"event": "exit_order_unconfirmed", "resp": response})
        return False

    rationale = label_exit_reason(pnl=position.get("pnl", 0), decay=position.get("alpha_decay", 0), mesh_signal="exit")
    log_exit(position, reason=rationale)
    update_sync_log_with_outcome(symbol, outcome="closed")
    log_closed_trade(trade_id, result="closed", context={"rationale": rationale})
    process_and_journal({
        "symbol": symbol,
        "pnl": position.get("pnl", 0.0),
        "alpha_decay": position.get("alpha_decay", 0.0),
        "exit_rationale": rationale,
        "mesh_score": position.get("mesh_score", 0),
        "quantity": qty,
        "timestamp": datetime.utcnow().isoformat(),
    })
    process_trade_for_learning(position)
    evaluate_agents()
    print(f"✅ Exit order confirmed & trade logged ({trade_id})")
    log_allocation_update(
        recommended=0.15,
        rationale="exit_triggered",
        qthink_label="exit:decay_or_drawdown",
        regime=regime,
        risk_profile="reduction",
        meta={"alpha_decay": position.get("alpha_decay", 0.0), "pnl": position.get("pnl", 0.0)},
    )
    return True

# ---------------------------------------------------------------------------
# Main loop (called by run_q_algo_live_async)
# ---------------------------------------------------------------------------

def manage_positions(vix_value: float = 18.0):
    """Periodic loop called by run_q_algo_live_async.
    Iterates over all open option positions and decides whether to exit.
    """
    positions = get_open_positions().get("positions", [])
    for position in positions:
        if not isinstance(position, dict):
            logger.warning({"event": "invalid_position_object", "raw": str(position)})
            continue

        option_symbol = position.get("symbol")
        if not option_symbol:
            logger.warning({"event": "manage_pos_missing_symbol", "pos": position})
            continue

        # ----- Market + option metrics -------------------------------------
        price = get_price()
        option_data = get_option_metrics(option_symbol) or {}
        dealer_data = get_dealer_flow_metrics("SPY") or {}

        # ----- Alpha‑decay computation -------------------------------------
        entry_time = position.get("entry_time")
        mesh_score = position.get("mesh_score", 50)
        minutes_alive = position.get("minutes_alive", 30)

        decay_time = calculate_time_decay(entry_time) if entry_time else 0.0
        decay_mesh = calculate_mesh_decay(mesh_score, minutes_alive)
        alpha_decay = round(0.6 * decay_time + 0.4 * decay_mesh, 4)

        pnl = position.get("pnl", 0.0)
        context = {
            "symbol": option_symbol,
            "price": price,
            "iv": option_data.get("iv", 0),
            "volume": option_data.get("volume", 0),
            "skew": option_data.get("skew", 0),
            "delta": option_data.get("delta", 0),
            "gamma": option_data.get("gamma", 0),
            "dealer_flow": dealer_data.get("score", 0),
            "vix": vix_value,
            "alpha_decay": alpha_decay,
            "mesh_score": mesh_score,
            "pnl": pnl,
        }

        # Log decay update
        log_alpha_decay(
            trade_id=position.get("trade_id", option_symbol),
            symbol=option_symbol,
            time_decay=decay_time,
            mesh_decay=decay_mesh,
            alpha_decay=alpha_decay,
            pnl=pnl,
            rationale="decay_update",
        )

        # ----- Exit decision ------------------------------------------------
        should_exit, rationale, regime = evaluate_exit(context, position)
        print(f"[EVAL] {option_symbol} | PnL {pnl:+.2f} | Decision: {rationale}")

        if should_exit:
            exit_success = exit_trade(position, regime)
            if exit_success:
                log_allocation_update(
                    recommended=0.15,
                    rationale="exit_triggered",
                    qthink_label="exit:decay_or_drawdown",
                    regime=regime,
                    risk_profile="reduction",
                    meta={"alpha_decay": alpha_decay, "pnl": pnl},
                )
