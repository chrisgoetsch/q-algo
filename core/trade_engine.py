import os
from datetime import datetime
from core.entry_learner import score_entry, build_entry_features
from core.tradier_execution import submit_order, get_atm_option_symbol
from core.capital_manager import get_current_allocation
from core.live_price_tracker import get_current_spy_price
from core.position_manager import manage_positions
from core.mesh_router import get_mesh_signal
from core.open_trade_tracker import track_open_trade
from core.logger_setup import logger
from core.threshold_manager import get_entry_threshold

SYMBOL = "SPY"

def open_position(symbol: str, quantity: int, call_put: str = "C"):
    """
    Executes the full trade entry pipeline:
    1. Generate mesh signal
    2. Score entry
    3. Check capital and thresholds
    4. Submit order to Tradier
    5. Log to trade tracker
    """
    context = {
        "symbol": symbol,
        "price": get_current_spy_price(),
        "timestamp": datetime.utcnow().isoformat(),
        "call_put": call_put
    }

    mesh_output = get_mesh_signal(context)
    context.update(mesh_output)

    top_agents = mesh_output.get("trigger_agents", [])
    signal_ids = mesh_output.get("signal_ids", {})
    if top_agents:
        context["signal_id"] = signal_ids.get(top_agents[0])

    features = build_entry_features(context)
    score, rationale = score_entry(context)
    allocation = get_current_allocation()

    print(f"[ENTRY] Score: {score:.2f} | Alloc: {allocation:.2f} | Rationale: {rationale}")
    context.update({
        "score": score,
        "rationale": rationale,
        "allocation": allocation,
    })

    if score < get_entry_threshold():
        print("⚠️ Entry score below threshold — skipping trade.")
        logger.info({
            "event": "entry_skipped_low_score",
            "score": score,
            "threshold": get_entry_threshold(),
            "context": context
        })
        return

    option_symbol = get_atm_option_symbol(symbol=symbol, call_put=call_put)
    if not option_symbol:
        logger.warning({
            "event": "missing_option_symbol",
            "context": context
        })
        print("⚠️ No valid option symbol returned from get_atm_option_symbol().")
        return

    context["option_symbol"] = option_symbol
    action = "buy_to_open"

    print(f"[Q Algo] 🟢 Attempting to place order: {option_symbol} × {quantity} ({action})")

    order = submit_order(
        option_symbol=option_symbol,
        quantity=quantity,
        action=action,
        estimated_cost_per_contract=1.00  # optionally dynamic later
    )

    if order.get("status") == "ok":
        print(f"✅ Order confirmed: {order}")
        context["capital_allocated"] = allocation
        context["order_id"] = order.get("order_id")
        track_open_trade(context)
    else:
        print(f"🛑 Order not confirmed: {order}")
        logger.warning({
            "event": "order_not_confirmed",
            "reason": order.get("reason"),
            "details": order,
            "context": context
        })


if __name__ == "__main__":
    open_position(SYMBOL, 1, "C")
    manage_positions()
