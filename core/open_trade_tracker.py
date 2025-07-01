# File: core/open_trade_tracker.py — PATCHED with full entry metadata enforcement + float32 fix

from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import requests
from polygon.polygon_websocket import SPY_LIVE_PRICE
from core.logger_setup import logger
from core.resilient_request import resilient_get

FILE = "logs/open_trades.jsonl"
RECONCILIATION_LOG_PATH = Path("logs/reconciliation_log.jsonl")

TRADIER_ACCESS_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN", "")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")
TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://sandbox.tradier.com/v1").rstrip("/")

OPEN_TRADES_PATH = Path("logs/open_trades.jsonl")
TRADIER_TOKEN_PROVIDER = lambda: TRADIER_ACCESS_TOKEN

def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TRADIER_TOKEN_PROVIDER()}",
        "Accept": "application/json",
    }

def _tradier_get(url: str, *, params: dict | None = None):
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

def _convert_floats(obj):
    if isinstance(obj, dict):
        return {k: _convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_floats(i) for i in obj]
    elif isinstance(obj, np.float32) or isinstance(obj, float):
        return float(obj)
    return obj

def fetch_open_tradier_orders() -> list[dict]:
    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    try:
        resp = _tradier_get(url)
        if not resp or resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} – {resp.text}")

        data = resp.json()
        raw = data.get("orders")
        if raw in (None, "null"):
            return []

        if isinstance(raw, dict):
            raw = [raw]

        return [o for o in raw if o.get("status") in ("filled", "open")]

    except Exception as e:
        logger.error({"event": "tradier_order_fetch_fail", "error": str(e)})
        return []

def sync_open_trades_with_tradier() -> None:
    synced: list[dict] = []
    current_open = load_open_trades()
    if len(current_open) >= 1:
        print(f"🚫 Sync skipped: already have open trade(s).")
        return

    for order in fetch_open_tradier_orders():
        opt_sym = order.get("option_symbol") or order.get("symbol")
        if not opt_sym:
            continue

        trade = {
            "trade_id": f"{opt_sym}_{order['id']}",
            "symbol": opt_sym,
            "quantity": int(order.get("quantity", 1)),
            "entry_time": order.get("create_date", datetime.utcnow().isoformat()),
            "status": order.get("status"),
            "order_id": order["id"],
        }
        _atomic_append_line(OPEN_TRADES_PATH, trade)
        synced.append(trade)
        print(f"✅ Synced trade {opt_sym} ×{trade['quantity']}")

    print(f"🔄 {len(synced)} open trades written to {OPEN_TRADES_PATH}")

def atomic_write_line(filepath, line_data):
    try:
        line_data = _convert_floats(line_data)
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(json.dumps(line_data) + "\n")
        with open(filepath, "a") as f:
            f.write(json.dumps(line_data) + "\n")
        os.replace(tmp_path, filepath)
    except Exception as e:
        print(f"❌ Failed to write open trade log: {e}")

def log_open_trade(option_symbol: str, agent: str, direction: str, strike: float | None, expiry: str | None, meta: dict):
    try:
        existing = load_open_trades()
        if existing:
            print(f"⏸️ Skipped log: position already open ({len(existing)} trades)")
            return

        entry = {
            "trade_id": f"{option_symbol}_{meta.get('entry_time')}",
            "option_symbol": option_symbol,
            "entry_time": meta.get("entry_time"),
            "entry_price": meta.get("entry_price", 0.0),
            "direction": direction,
            "agent": agent,
            "strike": strike,
            "expiry": expiry,
            "allocation": meta.get("allocation", 0.0),
            "contracts": meta.get("contracts", 0),
            "score": meta.get("score"),
            "regime": meta.get("regime", "unknown"),
            "rationale": meta.get("rationale", "N/A"),
            "mesh_score": meta.get("mesh_score"),
            "agent_signals": meta.get("agent_signals"),
            "mesh_context": meta.get("mesh_context"),
            "gpt_confidence": meta.get("gpt_confidence"),
            "gpt_reasoning": meta.get("gpt_reasoning"),
        }

        entry = _convert_floats(entry)
        tmp_path = FILE + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(json.dumps(entry) + "\n")
        with open(FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        os.replace(tmp_path, FILE)
    except Exception as e:
        print(f"❌ Failed to log open trade: {e}")

def load_open_trades() -> list[dict]:
    try:
        if not OPEN_TRADES_PATH.exists():
            return []
        with OPEN_TRADES_PATH.open("r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        logger.warning({"event": "load_open_trades_failed", "err": str(e)})
        return []


def remove_trade(trade_id: str) -> None:
    try:
        trades = load_open_trades()
        updated = [t for t in trades if t.get("trade_id") != trade_id]
        with OPEN_TRADES_PATH.open("w") as f:
            for entry in updated:
                f.write(json.dumps(entry) + "\n")
        print(f"🗑️ Removed trade {trade_id}")
    except Exception as e:
        logger.warning({"event": "remove_trade_failed", "trade_id": trade_id, "err": str(e)})

def log_reconciliation(source: str, matched: list[dict]):
    RECON_PATH = Path("logs/reconciliation_log.jsonl")
    try:
        RECON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with RECON_PATH.open("a") as f:
            for entry in matched:
                f.write(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": source,
                    "matched_trade": entry
                }) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to write reconciliation log: {e}")

def track_open_trade(*args, **kwargs):
    return log_open_trade(*args, **kwargs)
