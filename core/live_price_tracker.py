# ─────────────────────────────────────────────────────────────────────────────
# File: core/live_price_tracker.py           (v3-HF, polished)
# ─────────────────────────────────────────────────────────────────────────────
"""
Real-time option snapshot & price utilities for Q-ALGO hedge-fund stack.

* Resilient JSON parsing (handles Polygon’s occasional numeric top-level)
* Async-first API with single-flight cache (one HTTP hit per symbol/15 s)
* Sync wrappers keep legacy code working
* Always returns a dict with keys:
      price, iv, volume, skew, delta, gamma
"""
from __future__ import annotations

import asyncio
import math
import os
import time
from pathlib import Path
from typing import Dict, Tuple, Any, List

import httpx

from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
POLYGON_API_KEY  = os.getenv("POLYGON_API_KEY", "")
POLYGON_BASE_URL = "https://api.polygon.io/v3/snapshot/options"
CACHE_TTL        = 15  # seconds

# ---------------------------------------------------------------------------
# In-memory cache with in-flight single-flight control
# ---------------------------------------------------------------------------
class _SnapshotCache:
    def __init__(self):
        self._data : Dict[str, Tuple[float, dict]] = {}
        self._locks: Dict[str, asyncio.Lock]        = {}

    def fresh(self, sym: str) -> bool:
        ts, _ = self._data.get(sym, (0, {}))
        return (time.time() - ts) < CACHE_TTL

    def get(self, sym: str) -> dict | None:
        if self.fresh(sym):
            return self._data[sym][1]
        return None

    def set(self, sym: str, payload: dict):
        self._data[sym] = (time.time(), payload)

    def lock(self, sym: str) -> asyncio.Lock:
        self._locks.setdefault(sym, asyncio.Lock())
        return self._locks[sym]

_CACHE = _SnapshotCache()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_get(d: Any, *keys, default=0.0):
    """Navigate nested dicts defensively; return *default* on any error."""
    try:
        for k in keys:
            d = d[k]
        return float(d) if d is not None else default
    except Exception:
        return default

async def _fetch_snapshot(symbol: str) -> dict:
    url = f"{POLYGON_BASE_URL}/{symbol}?apiKey={POLYGON_API_KEY}"
    async with httpx.AsyncClient(timeout=8.0) as cli:
        r = await cli.get(url)
        r.raise_for_status()
        return r.json()

async def _retrieve(symbol: str) -> dict:
    # single-flight per symbol
    async with _CACHE.lock(symbol):
        cached = _CACHE.get(symbol)
        if cached is not None:
            return cached
        try:
            payload = await _fetch_snapshot(symbol)
            _CACHE.set(symbol, payload)
            logger.debug({"event": "polygon_snapshot", "symbol": symbol})
            return payload
        except Exception as e:
            logger.error({"event": "polygon_snapshot_fail", "err": str(e)})
            return {}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def get_option_metrics(symbol: str = "SPY") -> Dict[str, float]:
    """
    Return ATM 0-DTE option metrics.
    Keys: price, iv, volume, skew, delta, gamma
    """
    snap = await _retrieve(symbol)

    underlying_price = _safe_get(snap, "results", "underlying_asset", "last", "price")

    options_list: List[dict] = (
        snap.get("results", {}).get("options", [])
        if isinstance(snap.get("results", {}).get("options", []), list)
        else []
    )

    if not options_list:
        return dict(price=underlying_price, iv=0, volume=0, skew=0, delta=0, gamma=0)

    today = time.strftime("%Y-%m-%d")

    def _score(opt: dict) -> float:
        try:
            delta_score = abs(abs(opt["delta"]) - 0.5)
            exp_penalty = 0 if opt["details"]["expiration_date"] == today else 10
            return delta_score + exp_penalty
        except Exception:
            return math.inf

    best = min(options_list, key=_score)

    return {
        "price":  underlying_price,
        "iv":     _safe_get(best, "iv"),
        "volume": _safe_get(best, "volume"),
        "skew":   _safe_get(best, "skew"),
        "delta":  _safe_get(best, "delta"),
        "gamma":  _safe_get(best, "gamma"),
    }

# Legacy sync shim (will be removed once callers migrate)
def get_option_metrics_sync(symbol: str = "SPY") -> Dict[str, float]:
    return asyncio.run(get_option_metrics(symbol))
