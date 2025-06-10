# ─────────────────────────────────────────────────────────────────────────────
# File: core/open_trade_tracker.py                (v2-HF, cycle-safe revision)
# ─────────────────────────────────────────────────────────────────────────────
"""
Keeps logs/open_trades.jsonl in sync with *confirmed* open Tradier orders.

Key upgrades
============
1. **No more circular import.**
   We no longer import `_headers` from `core.tradier_execution`; instead we
   build headers locally.  Nothing in this module is imported by
   `tradier_execution`, so the cycle is eliminated.

2. **Config pulled once at module-load.**
   • `TRADIER_ACCESS_TOKEN` is read up-front; if you do token-refreshing
     elsewhere, point `TRADIER_TOKEN_PROVIDER()` to your helper.

3. **Single resilient GET helper** that already plugs correct headers.

4. **Strict typing & small clean-ups** (f-strings, path handling, etc.).
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests

from core.logger_setup import logger
from core.resilient_request import resilient_get

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
TRADIER_ACCESS_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN", "")
TRADIER_ACCOUNT_ID   = os.getenv("TRADIER_ACCOUNT_ID", "")
TRADIER_API_BASE     = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")

OPEN_TRADES_PATH = Path("logs/open_trades.jsonl")

# If you have a refresh-flow, expose it here; else returns cached token
def TRADIER_TOKEN_PROVIDER() -> str:        # noqa: N802  (constant-like name intentional)
    return TRADIER_ACCESS_TOKEN             # plug in refresh helper if needed

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _headers() -> dict[str, str]:
    """Always build fresh headers so token refreshes propagate automatically."""
    return {
        "Authorization": f"Bearer {TRADIER_TOKEN_PROVIDER()}",
        "Accept": "application/json",
    }

def _tradier_get(url: str, *, params: dict | None = None):
    """Centralised GET with retries & auth headers."""
    return resilient_get(url, params=params, headers=_headers())

def _atomic_append_line(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(obj, separators=(",", ":")) + "\n")

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]

# ─────────────────────────────────────────────────────────────────────────────
# Tradier order sync
# ─────────────────────────────────────────────────────────────────────────────
def fetch_open_tradier_orders() -> list[dict]:
    """Return a *list* of open/filled Tradier option-orders."""
    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    try:
        resp = _tradier_get(url)
        if not resp or resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} – {resp.text}")

        data = resp.json()
        raw = data.get("orders")
        # Tradier returns {"orders":"null"} when there are none
        if raw in (None, "null"):
            return []

        # ensure iterable
        if isinstance(raw, dict):
            raw = [raw]

        # filter on status
        return [o for o in raw if o.get("status") in ("filled", "open")]

    except Exception as e:
        logger.error({"event": "tradier_order_fetch_fail", "error": str(e)})
        return []

def sync_open_trades_with_tradier() -> None:
    """Write **one line per trade** to logs/open_trades.jsonl, append-only."""
    synced: list[dict] = []
    for order in fetch_open_tradier_orders():
        opt_sym = order.get("option_symbol") or order.get("symbol")
        if not opt_sym:
            continue

        trade = {
            "trade_id": f"{opt_sym}_{order['id']}",
            "symbol":   opt_sym,
            "quantity": int(order.get("quantity", 1)),
            "entry_time": order.get("create_date", datetime.utcnow().isoformat()),
            "status": order.get("status"),
            "order_id": order["id"],
        }
        _atomic_append_line(OPEN_TRADES_PATH, trade)
        synced.append(trade)
        print(f"✅ Synced trade {opt_sym} ×{trade['quantity']}")

    print(f"🔄 {len(synced)} open trades written to {OPEN_TRADES_PATH}")

# ─────────────────────────────────────────────────────────────────────────────
# Public helpers used by trade_engine / position_manager
# ─────────────────────────────────────────────────────────────────────────────
def log_open_trade(
    trade_id: str,
    agent: str,
    direction: str,
    strike: float,
    expiry: str,
    meta: dict | None = None,
) -> None:
    entry = {
        "trade_id":  trade_id,
        "agent":     agent,
        "direction": direction,
        "strike":    strike,
        "expiry":    expiry,
        "timestamp": datetime.utcnow().isoformat(),
        "meta":      meta or {},
    }
    _atomic_append_line(OPEN_TRADES_PATH, entry)

def track_open_trade(context: Dict) -> None:
    """
    Persist a freshly opened trade coming from trade_engine.
    Expects *context* with keys: option_symbol, order_id, contracts, etc.
    """
    trade_id = context.get("trade_id") or f"{context['option_symbol']}_{datetime.utcnow().isoformat()}"
    record = {
        "trade_id":   trade_id,
        "symbol":     context["option_symbol"],
        "quantity":   int(context.get("contracts", 1)),
        "entry_time": datetime.utcnow().isoformat(),
        "order_id":   context.get("order_id"),
        "score":      context.get("score"),
        "mesh_agents": context.get("trigger_agents"),
    }
    _atomic_append_line(OPEN_TRADES_PATH, record)
    print(f"📈 Trade logged → {trade_id}")

def load_open_trades(path: Path | str = OPEN_TRADES_PATH) -> list[dict]:
    return _load_jsonl(Path(path))

def remove_trade(trade_id: str) -> None:
    """Used by position_manager when a leg is fully closed."""
    trades   = load_open_trades()
    remain   = [t for t in trades if t.get("trade_id") != trade_id]
    OPEN_TRADES_PATH.write_text(
        "\n".join(json.dumps(t, separators=(",", ":")) for t in remain) + ("\n" if remain else "")
    )
    print(f"🧹 Removed trade {trade_id}")
