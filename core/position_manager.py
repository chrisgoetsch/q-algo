import os
import json
from datetime import datetime
import asyncio

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
from polygon.polygon_rest import get_option_metrics, get_dealer_flow_metrics
from core.alpha_decay_tracker import calculate_time_decay, calculate_mesh_decay
from analytics.qthink_feedback_loop import process_trade_for_learning
from core.gpt_exit_analyzer import analyze_exit_with_gpt
from polygon.polygon_websocket import SPY_LIVE_PRICE
from core.mesh_optimizer import evaluate_agents
from analytics.qthink_feedback_loop import load_reinforcement_profile

LOGS_DIR = "logs"
RUNTIME_STATE_PATH = os.path.join(LOGS_DIR, "runtime_state.json")
SYNC_LOG_PATH = os.path.join(LOGS_DIR, "sync_log.jsonl")
EXIT_ATTEMPTS_LOG = os.path.join(LOGS_DIR, "exit_attempts.jsonl")
OPEN_TRADES_PATH = os.path.join(LOGS_DIR, "open_trades.jsonl")
REINFORCEMENT_PROFILE_PATH = "assistants/reinforcement_profile.json"

# --- Utility Logging Functions ---

def get_price():
    return SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade") or 0.0

def log_exit_attempt(symbol, qty, response):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "quantity": qty,
        "response": response
    }
    try:
        with open(EXIT_ATTEMPTS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error({"event": "exit_log_fail", "error": str(e)})

def log_reinforcement_profile(entry: dict):
    try:
        os.makedirs(os.path.dirname(REINFORCEMENT_PROFILE_PATH), exist_ok=True)
        with open(REINFORCEMENT_PROFILE_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error({"event": "reinforcement_log_fail", "error": str(e)})

def get_open_positions():
    try:
        raw = get_positions().get("positions", [])
        return {"positions": [p for p in raw if isinstance(p, dict)]}
    except Exception as e:
        logger.error({"event": "get_positions_fail", "error": str(e)})
        return {"positions": []}

def update_sync_log_with_outcome(option_symbol, outcome):
    try:
        with open(SYNC_LOG_PATH, "a") as f:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "option_symbol": option_symbol,
                "exit_result": outcome
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error({"event": "sync_log_fail", "error": str(e)})

# --- Exit Evaluation with Mesh + GPT ---

def evaluate_exit(context, position):
    profile = load_reinforcement_profile()
    exit_cutoff = profile.get("suggested_exit_decay", 0.6)

    score_data = score_exit_signals(context, position)
    exit_signal = score_data.get("signal", "hold")
    exit_confidence = score_data.get("confidence", 0)

    pnl = position.get("pnl", 0.0)
    decay = context.get("alpha_decay", 0.0)

    simulated_context = simulate_market_scenario(context)
    regime = simulated_context.get("regime", "unknown")
    context.update({
        "regime": regime,
        "exit_signal": exit_signal,
        "exit_confidence": exit_confidence,
        "trade_id": position.get("trade_id")
    })

    async def decide():
        gpt_decision = await analyze_exit_with_gpt(context, context["trade_id"])
        gpt_signal = gpt_decision.get("signal", "hold")
        gpt_conf = gpt_decision.get("confidence", 0.5)

        context.update({
            "gpt_exit_signal": gpt_signal,
            "gpt_confidence": gpt_conf,
            "gpt_rationale": gpt_decision.get("rationale", "n/a"),
            "reinforcement_label": f"gpt_exit:{gpt_signal}"
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
        return should_exit, rationale

    return asyncio.run(decide())

def confirm_order_success(order_id):
    try:
        result = get_order_status(order_id)
        status = result.get("order", {}).get("status", "unknown")
        return status == "ok"
    except Exception as e:
        logger.error({"event": "confirm_order_failed", "error": str(e)})
        return False

def exit_trade(position):
    symbol = position.get("symbol")
    qty = position.get("quantity", 1)
    trade_id = position.get("trade_id", symbol)

    print(f"[EXIT] Closing position: {symbol} ×{qty}")
    response = submit_order(option_symbol=symbol, quantity=qty, action="sell_to_close")
    log_exit_attempt(symbol, qty, response)

    if response and response.get("status") == "ok":
        order_id = response.get("order_id")
        if confirm_order_success(order_id):
            rationale = label_exit_reason(
                pnl=position.get("pnl", 0),
                decay=position.get("alpha_decay", 0),
                mesh_signal="exit"
            )
            log_exit(position, reason=rationale)
            update_sync_log_with_outcome(symbol, outcome="closed")
            log_closed_trade(trade_id=trade_id, result="closed", context={"rationale": rationale})
            process_and_journal({
                "symbol": symbol,
                "pnl": position.get("pnl", 0.0),
                "alpha_decay": position.get("alpha_decay", 0.0),
                "exit_rationale": rationale,
                "mesh_score": position.get("mesh_score", 0),
                "quantity": qty,
                "timestamp": datetime.utcnow().isoformat()
            })
            process_trade_for_learning(position)
            log_reinforcement_profile(position)
            try:
                evaluate_agents()
                print("🧠 Mesh weights updated post-trade.")
            except Exception as e:
                print(f"⚠️ Mesh optimization failed: {e}")
            return True
        else:
            print("⚠️ Exit order submitted but not confirmed by Tradier.")
    else:
        print("🛑 Exit order failed.")

    logger.error({"event": "exit_order_failed", "symbol": symbol, "qty": qty, "response": response})
    return False

def manage_positions(vix_value=18.0):
    positions = get_open_positions()
    for position in positions.get("positions", []):
        if not isinstance(position, dict):
            logger.warning({"event": "invalid_position_object", "raw": str(position)})
            continue

        option_symbol = position.get("symbol", None)
        if not option_symbol:
            logger.warning({"event": "manage_positions_missing_option_symbol", "position": position})
            continue

        price = get_price("SPY")
        option_data = get_option_metrics(option_symbol)
        dealer_data = get_dealer_flow_metrics("SPY")

        entry_time = position.get("entry_time")
        mesh_score = position.get("mesh_score", 50)
        minutes_alive = position.get("minutes_alive", 30)

        decay_time = calculate_time_decay(entry_time) if entry_time else 0.0
        decay_mesh = calculate_mesh_decay(mesh_score, minutes_alive)
        alpha_decay = round((0.6 * decay_time + 0.4 * decay_mesh), 4)

        pnl = position.get("pnl", 0.0)
        rationale = "mesh exit pending" if alpha_decay > 0.5 else "holding"

        context = {
            "symbol": option_symbol,
            "price": price,
            "iv": option_data.get("iv", 0),
            "volume": option_data.get("volume", 0),
            "skew": option_data.get("skew", 0),
            "delta": option_data.get("delta", 0),
            "gamma": option_data.get("gamma", 0),
            "dealer_flow": dealer_data.get("score", 0) if dealer_data else 0,
            "vix": vix_value,
            "alpha_decay": alpha_decay,
            "mesh_score": mesh_score,
            "pnl": pnl
        }

        log_alpha_decay(
            trade_id=position.get("trade_id", option_symbol),
            symbol=option_symbol,
            time_decay=decay_time,
            mesh_decay=decay_mesh,
            alpha_decay=alpha_decay,
            pnl=pnl,
            rationale=rationale
        )

        should_exit, rationale = evaluate_exit(context, position)
        print(f"[EVAL] {option_symbol} | PnL: {pnl:.2f} | Decision: {rationale}")

        if should_exit:
            exit_trade(position)
            log_allocation_update(
                recommended=0.15,
                rationale="exit_triggered",
                qthink_label="exit:decay_or_drawdown",
                regime=context.get("regime", "unknown"),
                risk_profile="reduction",
                meta={"alpha_decay": alpha_decay, "pnl": pnl}
            )
