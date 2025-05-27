# File: core/trade_engine.py

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


def open_position(symbol: str, quantity: int, call_put: str):
    """
    Run entry pipeline, calculate confidence, size trade based on capital allocation,
    and submit live order.
    """
    context = {
        "symbol": symbol,
        "price": get_current_spy_price(),
        "timestamp": datetime.utcnow().isoformat(),
        "call_put": call_put
    }

    # Mesh signals include score, triggered agents, agent scores, and signal_ids
    mesh_output = get_mesh_signal(context)
    context.update(mesh_output)

    # Inject primary signal_id (you can choose a strategy; here we take the top agent if any)
    top_agents = mesh_output.get("trigger_agents", [])
    signal_ids = mesh_output.get("signal_ids", {})

    if top_agents:
        context["signal_id"] = signal_ids.get(top_agents[0])

    features = build_entry_features(context)
    score, rationale = score_entry(context)
    allocation = get_current_allocation()

    print(f"[ENTRY] Score: {score:.2f} | Alloc: {allocation:.2f} | Rationale: {rationale}")

    if score >= get_entry_threshold():
        qty = quantity

        # Get Tradier-compliant ATM option symbol
        option_symbol = get_atm_option_symbol(symbol=symbol, call_put=call_put)
        context["option_symbol"] = option_symbol

        if not option_symbol:
            logger.warning({"event": "missing_option_symbol", "context": context})
            print("⚠️ No valid option symbol returned from get_atm_option_symbol().")
            return

        print(f"[ORDER] Submitting {qty} × {option_symbol}")
        order = submit_order(option_symbol=option_symbol, quantity=qty, action="buy_to_open")

        if order:
            print(f"✅ Order confirmed: {order}")
            context["capital_allocated"] = allocation
            track_open_trade(option_symbol, context)
        else:
            print("🛑 Order failed")


if __name__ == "__main__":
    open_position(SYMBOL, 1, "C")
    manage_positions()
