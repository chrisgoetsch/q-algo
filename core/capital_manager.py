# ─────────────────────────────────────────────────────────────────────────────
# File: core/capital_manager.py     (v3-HF-0DTE, rev-E 2025-06-13)
# ---------------------------------------------------------------------------
"""
Capital / risk utilities for Q-ALGO hedge-fund stack.

Key points
══════════
• Async httpx polling of Tradier balances (fast cadence for 0-DTE scalps).
• Stale-while-revalidate cache accessed by cheap synchronous getters.
• Graceful fallback to HTTP/1.1 when `h2` isn’t installed.
• Back-compat helpers preserved (_RISK_TABLE, log_allocation_update).
"""
from __future__ import annotations
import time
import asyncio, os, random, time
from typing import Dict

import httpx
from core.logger_setup import get_logger
from core.tradier_client import get_positions



# ─────────────────────────────── configuration
logger              = get_logger(__name__)
TRADIER_ACCOUNT_ID  = os.getenv("TRADIER_ACCOUNT_ID", "")
TRADIER_TOKEN       = os.getenv("TRADIER_ACCESS_TOKEN", "")
TRADIER_API_BASE    = os.getenv("TRADIER_API_BASE", "https://sandbox.tradier.com/v1").rstrip("/")
BAL_ENDPOINT        = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/balances"
POLL_BASE_SECS      = 5          # fast cadence for 0-DTE
POLL_MAX_SECS       = 60         # back-off ceiling

_timeout            = httpx.Timeout(8.0)        # finite, generous
HEADERS             = {
    "Authorization": f"Bearer {TRADIER_TOKEN}",
    "Accept":        "application/json",
}

# ─────────────────────────────── HTTP/2 graceful toggle
try:
    import h2                              # noqa: F401  (only presence matters)
    _HTTP2 = True
except ImportError:
    _HTTP2 = False
    logger.warning("h2 package missing – using HTTP/1.1 for Tradier polling")

# ─────────────────────────────── SWR balance cache
_balance: Dict[str, float] | None = None
_last_fetch: float = 0.0
_backoff:    float = POLL_BASE_SECS

def get_open_position_count() -> int:
    try:
        positions = get_positions().get("positions", [])
        return len([p for p in positions if isinstance(p, dict)])
    except Exception as e:
        logger.warning({"event": "position_count_fail", "err": str(e)})
        return 0
    
def safe_fetch_tradier_equity(retries: int = 2, delay: float = 0.5) -> float:
    for attempt in range(retries + 1):
        eq = fetch_tradier_equity()
        if eq > 0:
            return eq
        if attempt < retries:
            time.sleep(delay)
    return eq  # may still be 0

def safe_get_tradier_buying_power(retries: int = 2, delay: float = 0.5) -> float:
    for attempt in range(retries + 1):
        bp = get_tradier_buying_power()
        if bp > 0:
            return bp
        if attempt < retries:
            time.sleep(delay)
    return bp  # may still be 0

async def _refresh_balance(client: httpx.AsyncClient):
    """Fetch balances once, updating the shared SWR cache."""
    global _balance, _last_fetch, _backoff
    try:
        r = await client.get(BAL_ENDPOINT, headers=HEADERS, timeout=_timeout)
        r.raise_for_status()
        _balance    = r.json().get("balances", {}) or {}
        _last_fetch = time.time()

        if _backoff > POLL_BASE_SECS:
            logger.info("✅ Tradier recovered – polling cadence reset")
        _backoff = POLL_BASE_SECS
        logger.debug({"event": "balance_update",
                      "cash": _balance.get("total_cash"),
                      "equity": _balance.get("total_equity")})
    except Exception as e:
        logger.warning(f"🛑 Tradier balance fetch failed: {e}")
        _backoff = min(_backoff * 2, POLL_MAX_SECS)


async def poll_balance_loop():
    """Fire-and-forget task launched once at startup."""
    async with httpx.AsyncClient(http2=_HTTP2) as client:
        await _refresh_balance(client)          # initial fetch
        while True:
            await asyncio.sleep(_backoff * random.uniform(0.8, 1.2))
            await _refresh_balance(client)

# ─────────────────────────────── cached look-ups
def _val(field: str, default: float = 0.0) -> float:
    if _balance is None:
        return default
    try:
        return float(_balance.get(field, default))
    except (TypeError, ValueError):
        return default


def fetch_tradier_equity(*, verbose: bool = False) -> float:
    """Return cached equity; 0.0 if not yet fetched."""
    eq = _val("total_equity")
    if verbose:
        print(f"Tradier equity ${eq:,.2f}")
    return eq


def get_tradier_buying_power(*, verbose: bool = False) -> float:
    """Return cached buying-power (Tradier `total_cash`)."""
    bp = _val("total_cash")
    if verbose:
        print(f"Tradier buying power ${bp:,.2f}")
    return bp

# ─────────────────────────────── risk & sizing helpers
_RISK_TABLE = {10_000: 0.10, 25_000: 0.08, 50_000: 0.06,
               100_000: 0.05, 250_000: 0.04, 500_000: 0.03}


def _lookup_risk_pct(equity: float) -> float:
    for lvl in sorted(_RISK_TABLE):
        if equity <= lvl:
            return _RISK_TABLE[lvl]
    return _RISK_TABLE[max(_RISK_TABLE)]


def get_current_allocation() -> float:
    override = os.getenv("FORCED_ALLOCATION_OVERRIDE")
    if override:
        print(f"📐 Using FORCED_ALLOCATION_OVERRIDE = {override}")
        return float(override)



def evaluate_drawdown_throttle(equity: float, baseline: float) -> float:
    if not baseline:
        return 1.0
    dd = (equity - baseline) / baseline
    if dd >= 0:
        return 1.0
    if dd < -0.20:
        return 0.25
    if dd < -0.10:
        return 0.50
    return 0.75


def compute_position_size(allocation_pct: float, win_ratio: float, odds: float,
                          *, max_position_fraction: float = 0.5) -> float:
    edge  = (win_ratio * (odds + 1) - 1) / odds
    kelly = max(0.0, min(edge / (odds - 1e-9), max_position_fraction))
    return allocation_pct * kelly

# ─────────────────────────────── back-compat shims
def log_allocation_update(pct: float):
    logger.info({"event": "allocation_update", "allocation_pct": round(pct, 4)})

# alias old sync names in case legacy modules import them
fetch_tradier_equity_sync      = fetch_tradier_equity      # type: ignore
get_tradier_buying_power_sync  = get_tradier_buying_power  # type: ignore
