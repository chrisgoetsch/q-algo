# File: core/tradier_execution.py
"""Thin Tradier wrapper (options‑only) with retry & structured logging.

Exports
-------
get_atm_option_symbol()   →  "SPY250606C00580000"
submit_order()           →  full Tradier JSON response (or raises)

This version aligns with the new trade_engine signature:
    submit_order(option_symbol, qty, side)

All outbound calls are logged via core.logger_setup.logger so they can be
replayed instantly when something fails.
"""
from __future__ import annotations

import os
import json
import requests
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List

from core.logger_setup import logger
from core.resilient_request import resilient_get
from core.capital_manager import get_tradier_buying_power

# ---------------------------------------------------------------------------
# Config & session helpers
# ---------------------------------------------------------------------------

TRADIER_API_KEY = os.getenv("TRADIER_ACCESS_TOKEN", "")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")
TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")

_session = requests.Session()


def _log(event: str, **kv):
    logger.info({"src": "tradier_exec", "event": event, **kv})


# --- token‑refresh stub ------------------------------------------------------

def _token_is_expired() -> bool:
    """Return True if the env var TRADIER_TOKEN_EXPIRES_AT is in the past."""
    ts = os.getenv("TRADIER_TOKEN_EXPIRES_AT")
    if not ts:
        return False
    try:
        return datetime.utcnow() > datetime.fromisoformat(ts)
    except Exception:
        return False


def _refresh_tradier_token() -> None:  # placeholder, depends on your refresh flow
    _log("token_refresh", note="stub_called")
    # TODO: call your refresh_token.py util here and update env vars.


def _headers() -> Dict[str, str]:
    global TRADIER_API_KEY
    if _token_is_expired():
        _refresh_tradier_token()
        TRADIER_API_KEY = os.getenv("TRADIER_ACCESS_TOKEN", "")
    return {
        "Authorization": f"Bearer {TRADIER_API_KEY}",
        "Accept": "application/json",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nearest(items: List[float], target: float) -> float:
    return min(items, key=lambda x: abs(x - target))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_atm_option_symbol(symbol: str = "SPY", call_put: str = "C") -> Optional[str]:
    """Resolve an ATM 0‑DTE (or next‑DTE fallback) Tradier OCC option symbol."""

    # 1️⃣  Get underlying price via Tradier (cheaper than Polygon for options‑only)
    quote_url = f"{TRADIER_API_BASE}/markets/quotes"
    q_resp = resilient_get(quote_url, params={"symbols": symbol}, headers=_headers())
    if not q_resp:
        _log("missing_price", symbol=symbol)
        return None
    try:
        price = float(q_resp.json()["quotes"]["quote"]["last"])
    except Exception as e:
        _log("price_parse_fail", error=str(e), raw=q_resp.text)
        return None

    # 2️⃣  Loop today + tomorrow until we get strikes
    today = date.today()
    for day_offset in (0, 1):
        expiry_date = today + timedelta(days=day_offset)
        expiry_str = expiry_date.strftime("%Y-%m-%d")
        expiry_occ = expiry_date.strftime("%y%m%d")

        chain_url = f"{TRADIER_API_BASE}/markets/options/strikes"
        params = {"symbol": symbol, "expiration": expiry_str}
        _log("chain_lookup_req", url=chain_url, params=params)
        resp = resilient_get(chain_url, params=params, headers=_headers())
        if not resp:
            continue
        try:
            strikes_raw = resp.json().get("strikes", {}).get("strike", [])
            strikes = [float(s) for s in strikes_raw]
        except Exception as e:
            _log("strike_parse_fail", error=str(e), raw=resp.text)
            continue

        if not strikes:
            continue

        atm_strike = _nearest(strikes, price)
        strike_code = f"{int(atm_strike * 1000):08d}"
        occ_symbol = f"{symbol}{expiry_occ}{call_put.upper()}{strike_code}"

        _log("atm_option_resolved", price=price, strike=atm_strike, option_symbol=occ_symbol)
        return occ_symbol

    _log("atm_option_symbol_failed", symbol=symbol)
    return None


def submit_order(option_symbol: str, qty: int, side: str) -> Dict[str, Any]:
    """Submit a market order to Tradier. Raises on HTTP errors."""

    if os.getenv("ALLOW_ORDER_SUBMISSION", "1") == "0":
        _log("order_skipped_test_mode", option_symbol=option_symbol)
        print(f"❌ Test‑mode: skipped order for {option_symbol}")
        return {"status": "skipped", "reason": "test_mode"}

    if qty < 1:
        print("⚠️ Invalid order quantity (must be ≥1)")
        return {"status": "skipped", "reason": "invalid_qty"}

    # Buying‑power check (soft stop – we still let Tradier reject if race condition)
    bp = get_tradier_buying_power()
    if bp and bp < 1:  # you can refine with est cost per contract if desired
        _log("low_buying_power", buying_power=bp)
        print("🛑 Buying power too low – order blocked locally")
        return {"status": "blocked", "reason": "low_bp"}

    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    payload = {
        "class": "option",
        "symbol": "SPY",  # underlying ticker, always SPY
        "option_symbol": option_symbol,
        "side": side,          # buy_to_open / sell_to_close
        "quantity": str(int(qty)),
        "type": "market",
        "duration": "day",
    }

    _log("submit_order_req", payload=payload)

    resp = _session.post(url, headers=_headers(), data=payload, timeout=15)
    _log("submit_order_resp", status=resp.status_code, body=resp.text)

    if resp.status_code != 201:
        raise RuntimeError(f"Tradier order HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    if "errors" in data:
        _log("tradier_order_rejected", errors=data["errors"], raw=resp.text)
        return {"status": "rejected", "errors": data["errors"], "raw": resp.text}

    return data
