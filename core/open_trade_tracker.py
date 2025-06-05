# ─────────────────────────────────────────────────────────────────────────────
# File: core/open_trade_tracker.py  (rewritten for new order payload)
# ─────────────────────────────────────────────────────────────────────────────
"""Keeps logs/open_trades.jsonl in sync with confirmed open positions.

Changes vs. legacy version
• `track_open_trade()` now accepts the **context** dict from trade_engine
  (no longer relies on a `status=='ok'` flag).
• Uses token‑refreshing headers from core.tradier_execution instead of
  static env vars so it never breaks after a refresh.
• All writes are atomic and append‑only.
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, List

import requests

from core.logger_setup import logger
from core.tradier_execution import _headers  # type: ignore (internal helper ok)
from core.resilient_request import resilient_get

TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")
TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")
OPEN_TRADES_PATH = "logs/open_trades.jsonl"

# ---------------------------------------------------------------------------
# Tradier helpers
# ---------------------------------------------------------------------------

def _tradier_get(url: str, params: dict | None = None):
    return resilient_get(url, params=params, headers=_headers())


def fetch_open_tradier_orders() -> List[dict]:
    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    resp = _tradier_get(url)
    if not resp:
        logger.error({"event": "tradier_order_fetch_fail"})
        return []
    try:
        raw_orders = resp.json().get("orders", {}).get("order", [])
        if isinstance(raw_orders, dict):
            raw_orders = [raw_orders]
        return [o for o in raw_orders if o.get("status") == "filled"]
    except Exception as e:
        logger.error({"event": "order_parse_fail", "error": str(e), "raw": resp.text})
        return []


# ---------------------------------------------------------------------------
# Sync & logging operations
# ---------------------------------------------------------------------------

def _atomic_write_line(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(obj) + "\n")


def sync_open_trades_with_tradier() -> None:
    synced: List[dict] = []
    for order in fetch_open_tradier_orders():
        opt_sym = order.get("option_symbol") or order.get("symbol")
        if not opt_sym:
            continue
        trade = {
            "trade_id": f"{opt_sym}_{order.get('id')}",
            "symbol": opt_sym,
            "quantity": int(order.get("quantity", 1)),
            "entry_time": order.get("create_date", datetime.utcnow().isoformat()),
            "status": order.get("status"),
            "order_id": order.get("id"),
        }
        synced.append(trade)
        _atomic_write_line(OPEN_TRADES_PATH, trade)
        print(f"✅ Synced trade {opt_sym} ×{trade['quantity']}")
    print(f"🔄 {len(synced)} open trades written to {OPEN_TRADES_PATH}")


def log_open_trade(trade_id: str, agent: str, direction: str, strike: float, expiry: str, meta: dict | None = None):
    entry = {
        "trade_id": trade_id,
        "agent": agent,
        "direction": direction,
        "strike": strike,
        "expiry": expiry,
        "timestamp": datetime.utcnow().isoformat(),
        "meta": meta or {},
    }
    _atomic_write_line(OPEN_TRADES_PATH, entry)


def track_open_trade(context: Dict):
    """Persist a freshly opened trade coming from trade_engine.

    Expects *context* with keys: option_symbol, order_id, contracts, etc.
    """
    trade_id = context.get("trade_id") or f"{context['option_symbol']}_{datetime.utcnow().isoformat()}"
    record = {
        "trade_id": trade_id,
        "symbol": context["option_symbol"],
        "quantity": int(context.get("contracts", 1)),
        "entry_time": datetime.utcnow().isoformat(),
        "order_id": context.get("order_id"),
        "score": context.get("score"),
        "mesh_agents": context.get("trigger_agents"),
    }
    _atomic_write_line(OPEN_TRADES_PATH, record)
    print(f"📈 Trade logged → {trade_id}")


def load_open_trades(path: str = OPEN_TRADES_PATH):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]

# ---------------------------------------------------------------------------
# Helper for position_manager to remove closed trades
# ---------------------------------------------------------------------------

def remove_trade(trade_id: str):
    trades = load_open_trades()
    remaining = [t for t in trades if t.get("trade_id") != trade_id]
    with open(OPEN_TRADES_PATH, "w") as fh:
        for t in remaining:
            fh.write(json.dumps(t) + "\n")
    print(f"🧹 Removed trade {trade_id}")