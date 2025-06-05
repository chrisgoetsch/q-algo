# File: core/trade_engine.py
"""Trade entry engine for Q‑ALGO v2
-------------------------------------------------
This module is invoked by run_q_algo_live_async whenever an entry
condition is satisfied.  It runs synchronously (inside a thread
pool) so must complete quickly and raise exceptions back to the
caller.  Key responsibilities:
1. Build the live *context* (price, mesh signals, score, etc.)
2. Decide whether an entry is allowed (thresholds, capital rules)
3. Find an at‑the‑money 0‑DTE option symbol via Tradier
4. Submit the order with `submit_order()`
5. Persist the new position to `open_trades.jsonl`
6. Return the full Tradier order payload so the caller can print it.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any, Tuple

from core.entry_learner import score_entry, build_entry_features
from core.tradier_execution import submit_order, get_atm_option_symbol
from core.capital_manager import get_current_allocation
from core.live_price_tracker import get_current_spy_price
from core.mesh_router import get_mesh_signal
from core.open_trade_tracker import track_open_trade
from core.logger_setup import logger
from core.threshold_manager import get_entry_threshold

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SYMBOL = "SPY"
ORDER_SIDE = "buy_to_open"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(event: str, **kv):
    """Shorthand for structured logger calls."""
    logger.info({"src": "trade_engine", "event": event, **kv})

# ---------------------------------------------------------------------------
# Main entry function (called from async loop)
# ---------------------------------------------------------------------------

def open_position(symbol: str = DEFAULT_SYMBOL, contracts: int = 1, call_put: str = "C") -> Dict[str, Any]:
    """End‑to‑end pipeline to open a new option position.

    Parameters
    ----------
    symbol : str
        Underlying ticker (defaults to SPY)
    contracts : int
        Number of option contracts to buy
    call_put : str
        "C" for Call, "P" for Put

    Returns
    -------
    dict
        Full JSON response from Tradier `submit_order`.  Caller prints it
        and handles any raised exception.
    """

    # 1️⃣  Build initial context ------------------------------------------------
    context: Dict[str, Any] = {
        "symbol": symbol,
        "price": get_current_spy_price(),
        "timestamp": datetime.utcnow().isoformat(),
        "call_put": call_put,
    }
    print(f"[ENTRY] Starting position logic for {symbol} {call_put} …")

    # 2️⃣  Mesh signal & feature vector ----------------------------------------
    mesh_output = get_mesh_signal(context)
    context.update(mesh_output)

    top_agents = mesh_output.get("trigger_agents", [])
    if top_agents:
        context["signal_id"] = mesh_output.get("signal_ids", {}).get(top_agents[0])

    features = build_entry_features(context)
    score, rationale = score_entry(context)

    allocation = get_current_allocation()

    print(f"[ENTRY] Score={score:.2f}  Alloc={allocation:.2f}  Rationale={rationale}")
    context.update({
        "score": score,
        "rationale": rationale,
        "allocation": allocation,
    })

    # 3️⃣  Threshold gate --------------------------------------------------------
    threshold = get_entry_threshold()
    if score < threshold:
        print("⚠️ Entry score below threshold — skipping trade.")
        _log("entry_skipped_low_score", score=score, threshold=threshold)
        return {}

    # 4️⃣  Option‑symbol lookup --------------------------------------------------
    option_symbol = get_atm_option_symbol(symbol=symbol, call_put=call_put)
    if not option_symbol:
        print("⚠️ No valid option symbol returned from get_atm_option_symbol().")
        _log("missing_option_symbol", context=context)
        return {}

    context["option_symbol"] = option_symbol

    print(f"[ENTRY] Submitting order: {option_symbol} × {contracts} ({ORDER_SIDE})")

    # 5️⃣  Submit order ----------------------------------------------------------
    try:
        order_resp = submit_order(option_symbol=option_symbol, qty=contracts, side=ORDER_SIDE)
        _log("order_submit_resp", body=order_resp)
    except Exception as exc:
        print(f"🛑 Order submission raised exception: {exc}")
        _log("order_submit_exception", error=str(exc), context=context)
        raise

    # 6️⃣  Persist new trade -----------------------------------------------------
    if order_resp.get("status") == "ok":
        context.update({
            "capital_allocated": allocation,
            "order_id": order_resp.get("order", {}).get("id"),
            "contracts": contracts,
        })
        track_open_trade(context)  # writes to open_trades.jsonl
        print(f"✅ Order confirmed. ID={context['order_id']}")
    else:
        print(f"🛑 Order not confirmed: {order_resp}")
        _log("order_not_confirmed", reason=order_resp.get("message"), body=order_resp, context=context)

    return order_resp

# ---------------------------------------------------------------------------
# CLI test harness -----------------------------------------------------------
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("[TEST] Triggering manual open_position() call…")
    response = open_position(DEFAULT_SYMBOL, 1, "C")
    print("[TEST] Response:", response)
