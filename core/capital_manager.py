# ─────────────────────────────────────────────────────────────────────────────
# File: core/capital_manager.py        (v2-HF + back-compat shims, rev-B)
# ---------------------------------------------------------------------------
"""
Capital / risk utilities for Q-ALGO hedge-fund stack.

* Stale-while-revalidate Tradier balance cache
* Auth-token safe – pulls `_headers()` lazily to avoid import cycles
* Jittered polling, quiet logger
* Back-compat shims: `get_tradier_buying_power()`, `log_allocation_update()`
"""
from __future__ import annotations

import asyncio, json, os, random, time
from datetime import datetime
from typing import Dict

import backoff, requests
from core.logger_setup import get_logger
from core.tradier_execution import _headers   # dynamic token hdr

logger = get_logger(__name__)

TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")
TRADIER_API_BASE   = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")
BALANCE_ENDPOINT   = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/balances"
CACHE_TTL_SECONDS  = 30

# ── SWR cache ----------------------------------------------------------------
class _BalanceCache:
    data: dict | None = None
    ts:   float       = 0.0
    last_bp: float    = -1.0
BAL_CACHE = _BalanceCache()

# ── Helpers ------------------------------------------------------------------
def _cache_fresh() -> bool:
    return (time.time() - BAL_CACHE.ts) < CACHE_TTL_SECONDS

def _jitter(x: float, pct: float = 0.25) -> float:
    import random
    return x * random.uniform(1 - pct, 1 + pct)

@backoff.on_exception(backoff.expo, Exception, max_time=15, jitter=_jitter)
def _get_balance() -> dict:
    r = requests.get(BALANCE_ENDPOINT, headers=_headers(), timeout=8)
    r.raise_for_status()
    return r.json().get("balances", {})

async def _async_refresh_balance():
    try:
        BAL_CACHE.data = await asyncio.to_thread(_get_balance)
        BAL_CACHE.ts   = time.time()

        bp = float(BAL_CACHE.data.get("total_cash", 0))
        if bp != BAL_CACHE.last_bp:
            BAL_CACHE.last_bp = bp
            logger.info({"event": "balance_update", "buying_power": bp})
    except Exception as e:
        logger.error({"event": "balance_fetch_fail", "err": str(e)})

def _balance_value(field: str, default: float = 0.0) -> float:
    if not _cache_fresh():
        try:
            asyncio.get_running_loop().create_task(_async_refresh_balance())
        except RuntimeError:
            asyncio.run(_async_refresh_balance())

    if BAL_CACHE.data:
        return float(BAL_CACHE.data.get(field, default))
    return default


# ── Public helpers -----------------------------------------------------------
def fetch_tradier_equity(force_refresh: bool = False, verbose: bool = False) -> float:
    if force_refresh or not _cache_fresh():
        try:
            asyncio.get_running_loop().create_task(_async_refresh_balance())
        except RuntimeError:            # called before any loop exists
            asyncio.run(_async_refresh_balance())
    equity = _balance_value("total_equity")
    if verbose:
        print(f"Tradier equity ${equity:,.2f}")
    return equity

def get_tradier_buying_power(force_refresh: bool = False, *, verbose: bool = False) -> float:
    if force_refresh or not _cache_fresh():
        try:
            asyncio.get_running_loop().create_task(_async_refresh_balance())
        except RuntimeError:
            asyncio.run(_async_refresh_balance())
    bp = _balance_value("total_cash")
    if verbose:
        print(f"Tradier buying power ${bp:,.2f}")
    return bp


# back-compat log shim
def log_allocation_update(pct: float):
    logger.info({"event": "allocation_update", "allocation_pct": round(pct, 4)})

# ── Risk sizing --------------------------------------------------------------
_RISK_TABLE = {10_000:0.10, 25_000:0.08, 50_000:0.06, 100_000:0.05, 250_000:0.04, 500_000:0.03}

def _lookup_risk_pct(equity: float) -> float:
    for lvl in sorted(_RISK_TABLE):
        if equity <= lvl:
            return _RISK_TABLE[lvl]
    return _RISK_TABLE[max(_RISK_TABLE)]

def get_current_allocation() -> float:
    return _lookup_risk_pct(fetch_tradier_equity())

def evaluate_drawdown_throttle(equity: float, baseline: float) -> float:
    if not baseline: return 1.0
    dd = (equity - baseline) / baseline
    if dd >= 0:      return 1.0
    if dd < -0.20:   return 0.25
    if dd < -0.10:   return 0.50
    return 0.75

def save_equity_baseline(equity: float, path: str = "logs/equity_baseline.json"):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump({"baseline": equity, "ts": datetime.utcnow().isoformat()}, open(path,"w"))
    except Exception as e:
        logger.error({"event": "baseline_save_fail", "err": str(e)})

def compute_position_size(allocation_pct: float, win_ratio: float, odds: float, *,
                           max_position_fraction: float = 0.5) -> float:
    edge   = (win_ratio * (odds + 1) - 1) / odds
    kelly  = max(0.0, min(edge / (odds - 1e-9), max_position_fraction))
    return allocation_pct * kelly

# optional background loop
async def poll_balance_loop(interval: int = 25):
    while True:
        await _async_refresh_balance()
        await asyncio.sleep(interval * random.uniform(0.8, 1.2))
