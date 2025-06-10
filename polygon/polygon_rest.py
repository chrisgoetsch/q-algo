# ─────────────────────────────────────────────────────────────────────────────
# File: polygon/polygon_rest.py   (compatibility shim – sync first)
# ─────────────────────────────────────────────────────────────────────────────
"""
Compatibility layer so legacy imports work without hitting Polygon endpoints
that require a paid plan.

• get_option_metrics(symbol)           -> dict   (sync, thread-safe)
• async_get_option_metrics(symbol)     -> dict   (awaitable)
• get_dealer_flow_metrics*(symbol)     -> dict   (neutral score placeholder)
"""

from __future__ import annotations
import asyncio
from typing import Dict

from core.live_price_tracker import (
    get_option_metrics      as _metrics_async,
    get_option_metrics_sync as _metrics_sync,
)

# ---------------------------------------------------------------------------
# Option metrics
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

async def async_get_dealer_flow_metrics(symbol: str = "SPY") -> Dict[str, float]:
    return {"score": 0.0}

# What other modules expect to import
__all__ = [
    "get_option_metrics",
    "async_get_option_metrics",
    "get_dealer_flow_metrics",
    "async_get_dealer_flow_metrics",
]
