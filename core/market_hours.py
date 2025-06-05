# File: core/market_hours.py  (refactored for 0‑DTE optimisation)
"""Market‑hours utilities with 0‑DTE trading windows
===================================================
Functions exported
------------------
* `is_market_open_now(kind="regular")`  → bool  (kind in {"regular","extended"})
* `is_0dte_trading_window_now()`          → bool  (09:35–15:45 ET)
* `get_market_status_string()`            → str   (pre‑market, open, post‑market, closed, holiday)
* `next_market_open()`                    → datetime in UTC

All times are evaluated in **US/Eastern** and auto‑respect US market holidays
(using *pandas_market_calendars* if available; otherwise a static holiday list
is used as fallback).
"""
from __future__ import annotations

import os
from datetime import datetime, time, timedelta
from functools import lru_cache

import pytz
from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------
_eastern = pytz.timezone("US/Eastern")


def _now_et() -> datetime:
    return datetime.now(pytz.utc).astimezone(_eastern)

# ---------------------------------------------------------------------------
# Holiday checker (NYSE calendar via pandas_market_calendars if available)
# ---------------------------------------------------------------------------

try:
    import pandas_market_calendars as mcal

    _nyse = mcal.get_calendar("NYSE")

    @lru_cache(maxsize=64)
    def _is_holiday(dt: datetime.date) -> bool:
        sched = _nyse.schedule(start_date=dt, end_date=dt)
        return sched.empty
except Exception:
    _static_holidays = {
        # minimal 2025 list (extend as needed)
        "2025-01-01",
        "2025-01-20",
        "2025-02-17",
        "2025-04-18",
        "2025-05-26",
        "2025-07-04",
        "2025-09-01",
        "2025-11-27",
        "2025-12-25",
    }

    def _is_holiday(dt: datetime.date) -> bool:  # type: ignore[override]
        return dt.isoformat() in _static_holidays

# ---------------------------------------------------------------------------
# Session boundaries
# ---------------------------------------------------------------------------
_regular_open = time(9, 30)
_regular_close = time(16, 0)
_premarket_open = time(4, 0)
_postmarket_close = time(20, 0)

# 0‑DTE window (skip first 5 mins, last 15 mins)
_0dte_open = time(9, 35)
_0dte_close = time(15, 45)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_market_open_now(kind: str = "regular") -> bool:
    """Return True if current ET time is within the specified session.

    kind="regular"    → 09:30–16:00
    kind="extended"   → 04:00–20:00 (pre + post)
    """
    now = _now_et().time()
    if _is_holiday(_now_et().date()):
        return False

    if kind == "regular":
        return _regular_open <= now <= _regular_close
    elif kind == "extended":
        return _premarket_open <= now <= _postmarket_close
    else:
        raise ValueError("kind must be 'regular' or 'extended'")


def is_0dte_trading_window_now() -> bool:
    """Return True during the preferred intraday window for 0‑DTE strategies."""
    now = _now_et().time()
    return not _is_holiday(_now_et().date()) and _0dte_open <= now <= _0dte_close


def get_market_status_string() -> str:
    if _is_holiday(_now_et().date()):
        return "holiday"
    t = _now_et().time()
    if t < _premarket_open or t > _postmarket_close:
        return "closed"
    if _premarket_open <= t < _regular_open:
        return "pre‑market"
    if _regular_open <= t <= _regular_close:
        return "open"
    return "post‑market"


def next_market_open() -> datetime:
    """Return next regular‑session open as an aware UTC datetime."""
    dt = _now_et()
    while True:
        dt += timedelta(days=1)
        if not _is_holiday(dt.date()):
            open_dt = datetime.combine(dt.date(), _regular_open, tzinfo=_eastern)
            return open_dt.astimezone(pytz.utc)
