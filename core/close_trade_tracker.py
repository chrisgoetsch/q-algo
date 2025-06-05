# File: core/close_trade_tracker.py
"""Tracks closed trades, removes them from the open‑trades log, and updates the
reinforcement profile so Q‑ALGO can learn from outcomes.
"""
from __future__ import annotations

import os, json
from datetime import datetime
from typing import List

from core.open_trade_tracker import load_open_trades, remove_trade
from core.logger_setup import logger

CLOSE_LOG_PATH = os.getenv("CLOSE_TRADES_FILE_PATH", "logs/closed_trades.jsonl")
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")

# Simple keyword buckets for now — you can refine later
POS_LABELS: List[str] = ["profit", "target", "strong", "alignment", "momentum"]
NEG_LABELS: List[str] = ["bad", "conflict", "regret", "late", "slippage"]

# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _atomic_append(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(obj) + "\n")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_closed_trade(trade_id: str, result: str, context: dict):
    """Append a closed‑trade entry and trigger reinforcement update."""
    entry = {
        "trade_id": trade_id,
        "result": result,
        "exit_context": context,
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        _atomic_append(CLOSE_LOG_PATH, entry)
        remove_trade(trade_id)  # from open_trades.jsonl
        print(f"🔴 Closed trade logged → {trade_id}")
        _update_reinforcement_profile(context.get("rationale", ""))
    except Exception as e:
        logger.error({"event": "close_trade_log_fail", "err": str(e), "trade": trade_id})

# ---------------------------------------------------------------------------
# Reinforcement profile logic
# ---------------------------------------------------------------------------

def _update_reinforcement_profile(label_text: str):
    text = label_text.lower()
    try:
        profile = json.load(open(REINFORCEMENT_PROFILE_PATH)) if os.path.exists(REINFORCEMENT_PROFILE_PATH) else {}
    except Exception:
        profile = {}

    # Increment buckets
    for kw in POS_LABELS + NEG_LABELS:
        if kw in text:
            profile[kw] = profile.get(kw, 0) + 1

    try:
        os.makedirs(os.path.dirname(REINFORCEMENT_PROFILE_PATH), exist_ok=True)
        json.dump(profile, open(REINFORCEMENT_PROFILE_PATH, "w"), indent=2)
        print("🧠 Reinforcement profile updated.")
    except Exception as e:
        logger.error({"event": "reinforcement_write_fail", "err": str(e)})

# ---------------------------------------------------------------------------
# CLI test harness
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_ctx = {"rationale": "Profit target hit – strong alignment with mesh."}
    log_closed_trade("TEST123", "closed", sample_ctx)
    print("✨ close_trade_tracker self‑test complete.")
