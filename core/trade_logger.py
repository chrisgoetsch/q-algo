# File: core/trade_logger.py — PATCHED with GPT/mesh metadata

import os
import json
from datetime import datetime

LOGS_DIR = "logs"
EXIT_LOG_PATH = os.path.join(LOGS_DIR, "trade_exit_log.jsonl")
DECAY_LOG_PATH = os.path.join(LOGS_DIR, "alpha_decay_log.jsonl")


def log_alpha_decay(trade_id, symbol, time_decay, mesh_decay, alpha_decay, pnl=None, rationale=None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "trade_id": trade_id,
        "symbol": symbol,
        "time_decay": round(time_decay, 4),
        "mesh_decay": round(mesh_decay, 4),
        "alpha_decay": round(alpha_decay, 4),
        "pnl": pnl,
        "rationale": rationale or "n/a"
    }

    try:
        os.makedirs(os.path.dirname(DECAY_LOG_PATH), exist_ok=True)
        with open(DECAY_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[Alpha Decay Logger] Failed to log: {e}")


def log_exit(position, reason="unspecified"):
    """
    Logs a trade exit event with metadata.
    """
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    regime = position.get("regime")
    if not regime or regime == "unknown":
        if isinstance(position.get("gpt_rationale"), str):
            rationale_text = position["gpt_rationale"].lower()
            if "bullish" in rationale_text:
                regime = "bullish"
            elif "bearish" in rationale_text:
                regime = "bearish"
            elif "panic" in rationale_text:
                regime = "panic"
            elif "choppy" in rationale_text:
                regime = "choppy"
            elif "stable" in rationale_text:
                regime = "stable"
            elif "trending" in rationale_text:
                regime = "trending"

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": position.get("symbol"),
        "quantity": position.get("quantity"),
        "pnl": position.get("pnl", 0.0),
        "exit_reason": reason,
        "trade_type": position.get("trade_type", "0DTE"),
        "mesh_context": position.get("mesh_context", {}),
        "gpt_exit_signal": position.get("gpt_exit_signal"),
        "gpt_confidence": position.get("gpt_confidence"),
        "gpt_rationale": position.get("gpt_rationale"),
        "regime": regime,
        "alpha_decay": position.get("alpha_decay"),
    }

    with open(EXIT_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"📝 EXIT LOGGED → {log_entry['symbol']} | reason: {reason} | regime: {log_entry.get('regime')} | gpt: {log_entry.get('gpt_exit_signal')} ({log_entry.get('gpt_confidence')})")
