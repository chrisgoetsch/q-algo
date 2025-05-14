# File: core/position_manager.py

import os
import json
from datetime import datetime

from core.tradier_client import submit_order, get_positions
from analytics.qthink_log_labeler import label_exit_reason, process_and_journal
from core.trade_logger import log_exit, log_alpha_decay
from core.mesh_router import score_exit_signals
from core.qthink_scenario_planner import simulate_market_scenario
from core.close_trade_tracker import log_closed_trade
from core.capital_manager import log_allocation_update
from core.logger_setup import logger

from polygon.polygon_rest import get_live_price, get_option_metrics, get_dealer_flow_metrics
from core.alpha_decay_tracker import calculate_time_decay, calculate_mesh_decay
from analytics.qthink_feedback_loop import process_trade_for_learning

LOGS_DIR = "logs"
RUNTIME_STATE_PATH = os.path.join(LOGS_DIR, "runtime_state.json")
SYNC_LOG_PATH = os.path.join(LOGS_DIR, "sync_log.jsonl")
REINFORCEMENT_PROFILE_PATH = "assistants/reinforcement_profile.json"

def load_reinforcement_profile():
    if not os.path.exists(REINFORCEMENT_PROFILE_PATH):
        return {}
    try:
        with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load reinforcement profile: {e}")
        return {}

def get_open_positions():
    """
    Ensures returned trades are all dictionaries to prevent runtime crashes.
    """
    raw = get_positions()
    clean = [p for p in raw.get("positions", []) if isinstance(p, dict)]
    if len(clean) < len(raw.get("positions", [])):
        logger.warning({
            "event": "filtered_invalid_positions",
            "original_count": len(raw.get("positions", [])),
            "valid_count": len(clean)
        })
    return {"positions": clean}

def write_daily_alpha_log(pnl_percentage, trade_result):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_path = os.path.join(LOGS_DIR, f"daily_alpha_log_{today}.json")
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "pnl": pnl_percentage,
        "result": trade_result,
    }
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

def update_sync_log_with_outcome(option_symbol, outcome):
    if not os.path.exists(SYNC_LOG_PATH):
        return
    with open(SYNC_LOG_PATH, "a") as f:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "option_symbol": option_symbol,
            "exit_result": outcome
        }
        f.write(json.dumps(log_entry) + "\n")

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
    context["regime"] = regime
    context["exit_signal"] = exit_signal
    context["exit_confidence"] = exit_confidence

    print(f"[REGIME] Simulated regime: {regime} | Mesh: {exit_signal} @ {exit_confidence:.2f}")

    if exit_signal == "exit" or pnl < -0.3 or decay > exit_cutoff or regime in ["panic", "compressing"]:
        rationale = label_exit_reason(pnl=pnl, decay=decay, mesh_signal=exit_signal)
        return True, rationale
    return False, "Hold"

def exit_trade(position):
    symbol = position.get("symbol")
    qty = position.get("quantity", 1)
    trade_id = position.get("trade_id", symbol)

    print(f"[EXIT] Closing position: {symbol} ×{qty}")
    response = submit_order(option_symbol=symbol, quantity=qty, action="sell_to_close")

    if response:
        rationale = label_exit_reason(
            pnl=position.get("pnl", 0),
            decay=position.get("alpha_decay", 0),
            mesh_signal="exit"
        )
        log_exit(position, reason="manual_or_triggered_exit")
        update_sync_log_with_outcome(symbol, outcome="closed")
        log_closed_trade(trade_id=trade_id, result="closed", context={"rationale": rationale})
        trade_record = {
            "symbol": symbol,
            "pnl": position.get("pnl", 0.0),
            "alpha_decay": position.get("alpha_decay", 0.0),
            "exit_rationale": rationale,
            "mesh_score": position.get("mesh_score", 0),
            "quantity": qty,
            "timestamp": datetime.utcnow().isoformat()
        }
        process_and_journal(trade_record)
        process_trade_for_learning(trade_record)  # 🔁 GPT feedback loop
        return True
    else:
        print("🛑 Exit order failed.")
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

        price = get_live_price("SPY") or 0
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
        else:
            print(f"[HOLD] Retaining position: {option_symbol}")
