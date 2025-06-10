# File: core/trade_engine.py  (v4-HF)
"""Async-safe order executor for Tradier-powered 0-DTE SPY flow.

Why a rewrite?
---------------
* **Single source of truth for thresholds** – the caller (run_q_algo_live_async)
  now passes the *evaluated* entry score & rationale so we never re-score /
  re-threshold inside the trade engine.
* **Async-aware but sync-compatible** – `open_position()` remains a blocking
  helper (so legacy `asyncio.to_thread(open_position, …)` calls keep working),
  but internally we use an async client & then bridge back to the caller.
* **Robust error handling** – every Tradier response is JSON-parsed & checked;
  we raise `TradeEngineError` with a full context payload on failure.
* **Integrated open-trade tracking** – success automatically calls
  `core.open_trade_tracker.track_open_trade()` so the logs stay in sync.
* **Configurable via env** – account ID, endpoint, default time-in-force, etc.
* **Reduced logging noise** – INFO on success, WARNING on recoverable errors,
  ERROR on fatal.
"""
from __future__ import annotations

import os, json, asyncio, time
from datetime import datetime, timezone
from typing import Dict, Any, Literal

import httpx

from core.logger_setup import get_logger
from core.open_trade_tracker import track_open_trade
from core.tradier_execution import _headers  # re-use token-refresh helper
from core.resilient_request import backoff_retry

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Config / constants
# ---------------------------------------------------------------------------
TRADIER_BASE_URL   = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")
DEFAULT_TIF        = os.getenv("TRADIER_ORDER_TIF", "day")
ENTRY_THRESHOLD    = float(os.getenv("ENTRY_SCORE_THRESHOLD", "0.60"))  # unified!

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class TradeEngineError(RuntimeError):
    """Raised on unrecoverable order submission failures."""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _place_order_async(
    symbol: str,
    contracts: int,
    direction: Literal["C", "P"],
    limit_price: float | None,
) -> dict:
    # Tradier option symbol must include expiry / strike / type – we let the
    # upstream contract selector handle that; here we assume *symbol* is fully
    # qualified (e.g. "SPY240606C00475000").
    payload = {
        "class": "option",
        "symbol": symbol,
        "side": "buy_to_open",
        "quantity": contracts,
        "type": "market" if limit_price is None else "limit",
        "price": limit_price,
        "duration": DEFAULT_TIF,
    }
    url = f"{TRADIER_BASE_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders"

    async with httpx.AsyncClient(timeout=10) as cli:
        r = await cli.post(url, headers=_headers(), data=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TradeEngineError(f"HTTP {e.response.status_code}: {e.response.text}") from e

        data = r.json()
        # Tradier returns {'order': {'id': '...', 'status': 'ok', ...}}
        order = data.get("order") or data.get("orders")
        if not order or order.get("status") not in {"ok", "filled", "open"}:
            raise TradeEngineError(f"Bad response: {json.dumps(data)[:400]}")
        return order

# ---------------------------------------------------------------------------
# Public facade (sync)
# ---------------------------------------------------------------------------

def open_position(
    symbol: str,
    contracts: int,
    option_type: Literal["C", "P"],
    *,
    score: float,
    rationale: str,
    limit_price: float | None = None,
) -> Dict[str, Any]:
    """Blocking helper to submit an opening order & synchronise logs.

    Parameters
    ----------
    symbol       Fully-qualified option symbol (e.g. *SPY240606C00475000*).
    contracts    Number of contracts to buy.
    option_type  "C" or "P" – used only for downstream logging.
    score        Pre-computed entry score from *entry_learner*.
    rationale    Human readable breakdown (for audit logs / CSV export).
    limit_price  Optional price cap; *None* → market order.

    Returns
    -------
    Tradier order dict (subset) augmented with *trade_id* & *timestamp*.
    """
    if score < ENTRY_THRESHOLD:
        raise TradeEngineError(
            f"Attempted to place order with score {score:.2f} < threshold {ENTRY_THRESHOLD:.2f}")

    # run the async routine in current thread (blocking)
    order = asyncio.run(_place_order_async(symbol, contracts, option_type, limit_price))

    trade_id = f"{symbol}_{order.get('id') or int(time.time())}"

    # Structured context for open_trade_tracker
    ctx = {
        "trade_id": trade_id,
        "option_symbol": symbol,
        "contracts": contracts,
        "order_id": order.get("id"),
        "score": score,
        "trigger_agents": [],  # placeholder – mesh_router can populate later
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rationale": rationale,
    }
    track_open_trade(ctx)

    logger.info({
        "event": "order_submitted",
        "symbol": symbol,
        "contracts": contracts,
        "score": score,
        "order_id": order.get("id"),
    })

    order.update({"trade_id": trade_id, "timestamp": ctx["timestamp"]})
    return order
