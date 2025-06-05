# File: core/async_live_price_tracker.py  (refactored)
"""Async‑friendly price helper.

Primary source: `polygon.async_polygon_websocket.SPY_LIVE_PRICE` (mid preferred)
Fallback: synchronous Tradier REST quote via `core.tradier_client.get_quote`.
Adds a 15‑second staleness guard so stale ws values trigger REST fetch.
"""
from __future__ import annotations

import time, asyncio
from typing import Optional

from polygon.async_polygon_websocket import SPY_LIVE_PRICE  # populated by ws listener
from core.tradier_client import get_quote
from core.logger_setup import get_logger

logger = get_logger(__name__)

# -------------------------------------------------------------
# Constants / globals
# -------------------------------------------------------------
_STALE_AFTER = 15  # seconds
_last_tradier_fetch = 0.0
_last_tradier_price: float = 0.0

# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def _ws_price() -> Optional[float]:
    price = SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("price")
    ts = SPY_LIVE_PRICE.get("timestamp")
    if price and ts and time.time() - ts < _STALE_AFTER:
        return price
    return None


def _tradier_price_sync() -> float:
    """Blocking Tradier REST quote, cached for STALE_AFTER sec."""
    global _last_tradier_fetch, _last_tradier_price
    if time.time() - _last_tradier_fetch < _STALE_AFTER and _last_tradier_price:
        return _last_tradier_price
    try:
        q = get_quote("SPY")
        _last_tradier_price = float(q["quotes"]["quote"]["last"])
    except Exception as e:
        logger.error({"event": "tradier_quote_fail", "err": str(e)})
        _last_tradier_price = 0.0
    _last_tradier_fetch = time.time()
    return _last_tradier_price

# -------------------------------------------------------------
# Public async API
# -------------------------------------------------------------

async def get_current_spy_price() -> float:
    """Return best SPY price, await if we must do REST fetch in executor."""
    price = _ws_price()
    if price:
        return price
    # Run sync REST fetch in thread to avoid blocking event loop
    return await asyncio.to_thread(_tradier_price_sync)

# -------------------------------------------------------------
# Async CLI test
# -------------------------------------------------------------
if __name__ == "__main__":
    async def _test():
        p = await get_current_spy_price()
        print("SPY async price →", p)
    asyncio.run(_test())
