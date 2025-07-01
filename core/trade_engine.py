# File: core/trade_engine.py — RESTORED for quant-grade order lifecycle
"""
This module executes entry orders with score enforcement, async-safe Tradier integration,
and structured logging. Designed to be called from run_q_algo_live_async.py.
"""

import os, json, asyncio, time
from datetime import datetime, timezone
from typing import Dict, Any, Literal
import httpx

from core.logger_setup import get_logger
from core.open_trade_tracker import track_open_trade
from core.tradier_execution import _headers  # token-refresh safe

logger = get_logger(__name__)

TRADIER_BASE_URL   = os.getenv("TRADIER_API_BASE", "https://sandbox.tradier.com/v1").rstrip("/")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")
DEFAULT_TIF        = os.getenv("TRADIER_ORDER_TIF", "day")
ENTRY_THRESHOLD    = float(os.getenv("ENTRY_SCORE_THRESHOLD", "0.60"))

class TradeEngineError(RuntimeError):
    pass

async def _place_order_async(
    symbol: str,
    contracts: int,
    option_type: Literal["C", "P"],
    limit_price: float | None = None,
) -> dict:
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
        order = data.get("order") or data.get("orders")
        if not order or order.get("status") not in {"ok", "filled", "open"}:
            raise TradeEngineError(f"Bad response: {json.dumps(data)[:400]}")
        return order

def open_position(
    symbol: str,
    contracts: int,
    option_type: Literal["C", "P"],
    *,
    score: float,
    rationale: str,
    limit_price: float | None = None,
) -> Dict[str, Any]:
    if score < ENTRY_THRESHOLD:
        raise TradeEngineError(
            f"Attempted to place order with score {score:.2f} < threshold {ENTRY_THRESHOLD:.2f}")
    order = asyncio.run(_place_order_async(symbol, contracts, option_type, limit_price))
    trade_id = f"{symbol}_{order.get('id') or int(time.time())}"
    ctx = {
        "trade_id": trade_id,
        "option_symbol": symbol,
        "contracts": contracts,
        "order_id": order.get("id"),
        "score": score,
        "trigger_agents": [],
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
