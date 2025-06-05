# File: core/live_price_tracker.py  (refactored)
"""Light‑weight price fetcher with staleness guard.

It prefers the mid‑price from the websocket cache, falls back to last trade,
then to Polygon REST (one quick call) if both cache values are zero or stale.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

from polygon.polygon_websocket import SPY_LIVE_PRICE
from polygon.polygon_rest import get_underlying_snapshot
from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
_STALE_AFTER_SEC = 15  # websocket price considered stale after 15s
_last_rest_fetch: float = 0.0
_last_rest_price: float = 0.0

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _websocket_price() -> Optional[float]:
    ts = SPY_LIVE_PRICE.get("timestamp")  # assume ws code fills this in epoch sec
    if ts and time.time() - ts > _STALE_AFTER_SEC:
        return None  # stale
    return SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade")


def _rest_price() -> float:
    global _last_rest_fetch, _last_rest_price
    if time.time() - _last_rest_fetch < _STALE_AFTER_SEC:
        return _last_rest_price  # return cached REST price
    try:
        snap = get_underlying_snapshot("SPY")
        _last_rest_price = float(snap.get("mid", 0) or snap.get("lastPrice", 0))
        _last_rest_fetch = time.time()
    except Exception as e:
        logger.error({"event": "rest_price_fail", "err": str(e)})
        _last_rest_price = 0.0
    return _last_rest_price

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_current_spy_price() -> float:
    """Return best‑available SPY price (mid preferred)."""
    price = _websocket_price()
    if price:
        return price
    return _rest_price()

# CLI test
if __name__ == "__main__":
    print("SPY price →", get_current_spy_price())
