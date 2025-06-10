# ─────────────────────────────────────────────────────────────────────────────
# File: core/account_fetcher.py         (HF-compatible)
# ─────────────────────────────────────────────────────────────────────────────
"""
Pulls the latest Tradier equity / buying-power snapshot and reconciles
logs/open_trades.jsonl with live broker positions.
"""
from __future__ import annotations

import json, os
from datetime import datetime
from pathlib import Path

from core.env_validator   import validate_env
from core.capital_manager import (
    fetch_tradier_equity,
    get_tradier_buying_power,
)
from core.logger_setup     import logger
from core.open_trade_tracker import sync_open_trades_with_tradier

# Validate env once on import (masked output)
validate_env()

ACCOUNT_SUMMARY_PATH = Path("logs/account_summary.json")

# ---------------------------------------------------------------------------
# Equity + BP fetch
# ---------------------------------------------------------------------------
def fetch_tradier_snapshot(verbose: bool = False) -> dict:
    """
    Return {"equity": float, "buying_power": float} and write
    logs/account_summary.json.  Caches values <= 30 s old.
    """
    equity = fetch_tradier_equity(force_refresh=True)   # triggers async refresh if stale
    bp     = get_tradier_buying_power()                 # cached value (same refresh)

    summary = {
        "timestamp":    datetime.utcnow().isoformat(),
        "equity":       equity,
        "buying_power": bp,
    }

    ACCOUNT_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNT_SUMMARY_PATH.write_text(json.dumps(summary, indent=2))

    logger.info({"event": "balance_check", "equity": equity, "buying_power": bp})
    if verbose:
        print(f"✅ Equity ${equity:,.2f} | BP ${bp:,.2f}")

    return summary

# ---------------------------------------------------------------------------
# Helper to reconcile local open_trades with live broker positions
# ---------------------------------------------------------------------------
def reconcile_open_trades() -> None:
    """Brings logs/open_trades.jsonl in sync with Tradier account positions."""
    print("🔄 Reconciling open_trades.jsonl with live Tradier positions…")
    sync_open_trades_with_tradier()

# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    fetch_tradier_snapshot(verbose=True)
    reconcile_open_trades()
    print("✨ account_fetcher.py self-test complete.")
