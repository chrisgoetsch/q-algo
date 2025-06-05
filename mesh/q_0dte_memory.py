# File: mesh/q_0dte_memory.py
# Purpose: Persistent memory for Q-0DTE pattern recognition snapshots

import os
import json
from datetime import datetime

MEMORY_LOG_PATH = "logs/q_0dte_memory.jsonl"

def store_snapshot(state_vector: dict, pattern_tag: str = "unknown"):
    """
    Stores a snapshot of the current 0DTE market state with an optional pattern tag.
    """
    os.makedirs(os.path.dirname(MEMORY_LOG_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "pattern_tag": pattern_tag,
        "state_vector": state_vector
    }

    with open(MEMORY_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def fetch_recent_snapshots(limit: int = 20):
    """
    Retrieves the most recent N memory snapshots from the memory log.
    """
    if not os.path.exists(MEMORY_LOG_PATH):
        return []

    with open(MEMORY_LOG_PATH, "r") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    return lines[-limit:] if len(lines) >= limit else lines

def summarize_patterns_with_outcomes():
    """
    Builds a summary of all known pattern tags and their recorded outcomes (PnL, results, regret, etc.).
    Assumes `result` field is written back into snapshots post-trade.
    """
    if not os.path.exists(MEMORY_LOG_PATH):
        return {}

    with open(MEMORY_LOG_PATH, "r") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    summary = {}
    for snap in lines:
        tag = snap.get("pattern_tag", "unknown")
        result = snap.get("result", None)  # Expects "win", "loss", or score

        if tag not in summary:
            summary[tag] = {"count": 0, "wins": 0, "losses": 0, "others": 0}

        summary[tag]["count"] += 1
        if result == "win":
            summary[tag]["wins"] += 1
        elif result == "loss":
            summary[tag]["losses"] += 1
        else:
            summary[tag]["others"] += 1

    return summary
