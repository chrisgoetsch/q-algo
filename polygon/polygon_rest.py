# ─────────────────────────────────────────────────────────────────────────────
# File: polygon/polygon_rest.py   (compatibility shim – sync first)
# ─────────────────────────────────────────────────────────────────────────────

"""
Compatibility layer so legacy imports work without hitting Polygon endpoints
that require a paid plan.

• get_option_metrics(symbol)           -> dict   (sync, thread-safe)
• async_get_option_metrics(symbol)     -> dict   (awaitable)
• get_dealer_flow_metrics*(symbol)     -> dict   (neutral score placeholder)
• get_last_price()                     -> float  (SPY mid/last fallback)
"""

from __future__ import annotations
from datetime import datetime
import asyncio
from typing import Dict
import os
import requests
from dotenv import load_dotenv
from core.live_price_tracker import (
    get_option_metrics      as _metrics_async,
    get_option_metrics_sync as _metrics_sync,
)

# Load environment variables
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Add to polygon_rest.py
# ---------------------------------------------------------------------------
# Historical bars fetcher (minute-based for intraday context)
# ---------------------------------------------------------------------------
def get_historic_bars(symbol: str = "SPY", multiplier: int = 1, timespan: str = "minute", 
                      from_date: str = None, to_date: str = None, limit: int = 50) -> list[dict]:
    """
    Fetches historical bars from Polygon.io REST API.
    
    Parameters:
    - symbol: ticker symbol (e.g., "SPY")
    - multiplier: size of each bar (1 = 1min, 5 = 5min)
    - timespan: "minute", "hour", "day"
    - from_date: ISO date (e.g., "2024-06-24") — required
    - to_date: ISO date (e.g., "2024-06-24") — optional
    - limit: number of bars to fetch
    
    Returns:
    - List of bar dicts with timestamp, open, high, low, close, volume
    """
    try:
        if not from_date:
            raise ValueError("from_date is required (e.g., '2024-06-24')")

        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date or from_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": limit,
            "apiKey": POLYGON_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    except Exception as e:
        print(f"[polygon_rest] get_historic_bars failed → {e}")
        return []

# ---------------------------------------------------------------------------
# Returns today's expiry in YYYYMMDD format
# ---------------------------------------------------------------------------
def get_today_expiry() -> str:
    return datetime.utcnow().strftime("%Y%m%d")

# ---------------------------------------------------------------------------
# Option snapshot fetch
# ---------------------------------------------------------------------------
def get_polygon_snapshot_options(symbol: str) -> list:
    try:
        url = f"https://api.polygon.io/v3/snapshot/options/{symbol}?apiKey={POLYGON_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"[polygon_rest] snapshot fetch error → {e}")
        return []

# ---------------------------------------------------------------------------
# Public: Get last SPY price (from underlying inside option snapshot)
# ---------------------------------------------------------------------------
def get_last_price(symbol: str = "SPY") -> float:
    try:
        url = f"https://api.polygon.io/v3/snapshot/options/{symbol}?apiKey={POLYGON_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        underlying = data.get("underlying_asset")
        if isinstance(underlying, dict):
            mid = underlying.get("mid") or (
                (underlying.get("ask") + underlying.get("bid")) / 2
                if underlying.get("ask") and underlying.get("bid") else None
            )
            return round(mid, 2) if mid else 0.0
        return 0.0
    except Exception as e:
        print(f"[polygon_rest] get_last_price failed: {e}")
        return 0.0

# ---------------------------------------------------------------------------
# Option metrics sync/async wrappers
# ---------------------------------------------------------------------------
def get_option_metrics(symbol: str = "SPY") -> Dict[str, float]:
    """SYNC helper used by entry_learner (runs in a thread)."""
    return _metrics_sync(symbol)

async def async_get_option_metrics(symbol: str = "SPY") -> Dict[str, float]:
    """ASYNC helper if anyone really needs await-style in the future."""
    return await _metrics_async(symbol)

# ---------------------------------------------------------------------------
# Dealer-flow score (stub: neutral)
# ---------------------------------------------------------------------------
def get_dealer_flow_metrics(symbol: str = "SPY") -> Dict[str, float]:
    return {"score": 0.0}

def get_historic_bars(symbol: str = "SPY", timespan="minute", limit=100) -> list:
    """Pulls historical bars for SPY intraday timeframe."""
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/{timespan}/today?adjusted=true&sort=asc&limit={limit}&apiKey={POLYGON_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"[polygon_rest] get_historic_bars error → {e}")
        return []
    
async def async_get_dealer_flow_metrics(symbol: str = "SPY") -> Dict[str, float]:
    return {"score": 0.0}

# ---------------------------------------------------------------------------
# Exportable interface
# ---------------------------------------------------------------------------

__all__ = [
    "get_option_metrics",
    "async_get_option_metrics",
    "get_dealer_flow_metrics",
    "async_get_dealer_flow_metrics",
    "get_last_price",
    "get_today_expiry",  # ← Add this
]
