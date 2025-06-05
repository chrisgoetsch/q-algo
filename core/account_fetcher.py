# File: core/account_fetcher.py
"""Fetches Tradier account buying‑power & equity and syncs logs/open_trades.jsonl.

This module now relies exclusively on the refreshed helpers in core.tradier_client
and core.open_trade_tracker so it maps cleanly onto the new Tradier flow.
"""
from __future__ import annotations

import os, json
from datetime import datetime
from typing import Tuple

from core.env_validator import validate_env
from core.capital_manager import get_tradier_buying_power
from core.logger_setup import logger
from core.open_trade_tracker import sync_open_trades_with_tradier

# Validate env once on import (masked output)
validate_env(mask=True)

ACCOUNT_SUMMARY_PATH = "logs/account_summary.json"

# ---------------------------------------------------------------------------
# Equity / buying‑power fetch
# ---------------------------------------------------------------------------

def fetch_tradier_equity() -> Tuple[float, float]:
    """Pulls buying power & equity, writes logs/account_summary.json, returns tuple.
    Will raise if Tradier call fails inside get_tradier_buying_power()."""
    buying_power, equity = get_tradier_buying_power(verbose=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "equity": equity,
        "buying_power": buying_power,
    }
    os.makedirs(os.path.dirname(ACCOUNT_SUMMARY_PATH), exist_ok=True)
    with open(ACCOUNT_SUMMARY_PATH, "w") as fh:
        json.dump(entry, fh, indent=2)

    logger.info({"event": "balance_check", "equity": equity, "buying_power": buying_power})
    print(f"✅ Equity ${equity:,.2f} | BP ${buying_power:,.2f}")
    return buying_power, equity

# ---------------------------------------------------------------------------
# Helper to reconcile local open_trades with live broker positions
# ---------------------------------------------------------------------------

def reconcile_open_trades():
    """Delegates to core.open_trade_tracker.sync_open_trades_with_tradier()."""
    print("🔄 Reconciling open_trades.jsonl with live Tradier positions…")
    sync_open_trades_with_tradier()

# ---------------------------------------------------------------------------
# CLI test harness
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fetch_tradier_equity()
    reconcile_open_trades()
    print("✨ account_fetcher.py self‑test complete.")
