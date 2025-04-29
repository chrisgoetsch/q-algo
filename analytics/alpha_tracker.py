# alpha_tracker.py
# Logs and analyzes alpha decay over time for reinforcement

import json
import os
import datetime
from pathlib import Path

LOG_PATH = Path("logs/alpha_decay_log.jsonl")

def log_alpha_decay(symbol, decay_score, agent_summary=None):
    """
    Logs current alpha score for trade regime tracking and decay trends.
    """
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "symbol": symbol,
        "decay_score": round(decay_score, 4),
        "agent_summary": agent_summary or {}
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[alpha_tracker] Failed to log decay: {e}")

def get_decay_score(symbol):
    """
    Returns a simple mock decay score from memory/logs.
    Replace this with live model or journal-based decay scoring.
    """
    try:
        with open(LOG_PATH, "r") as f:
            entries = [json.loads(line) for line in f if symbol in line]
        if not entries:
            return 0.0
        latest = entries[-1]
        return latest.get("decay_score", 0.0)
    except Exception as e:
        print(f"[alpha_tracker] No decay score found: {e}")
        return 0.0

