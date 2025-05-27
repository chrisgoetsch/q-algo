# File: core/threshold_manager.py

import os
import json
from datetime import datetime, timedelta

DEFAULT_ENTRY_THRESHOLD = 0.7
DEFAULT_EXIT_THRESHOLD = 0.5
DATA_PATH = "data"
THRESHOLD_FILE = os.path.join(DATA_PATH, f"thresholds_{datetime.now().strftime('%Y%m%d')}.json")

def compute_adaptive_thresholds(signal_stats: dict) -> dict:
    """
    Compute new entry/exit thresholds based on agent hit rate and return profile.
    """
    avg_hit_rate = sum(a["hit_rate"] for a in signal_stats.values()) / len(signal_stats)
    avg_return = sum(a["avg_return"] for a in signal_stats.values()) / len(signal_stats)

    entry_thresh = DEFAULT_ENTRY_THRESHOLD + 0.1 * (0.6 - avg_hit_rate)
    exit_thresh = DEFAULT_EXIT_THRESHOLD + 0.1 * (0.1 - avg_return)

    entry_thresh = max(0.5, min(entry_thresh, 0.9))
    exit_thresh = max(0.3, min(exit_thresh, 0.8))

    return {
        "entry_threshold": round(entry_thresh, 3),
        "exit_threshold": round(exit_thresh, 3),
        "hit_rate": round(avg_hit_rate, 3),
        "avg_return": round(avg_return, 3)
    }


def load_signal_stats_from_file(yesterday_file: str) -> dict:
    try:
        with open(yesterday_file, "r") as f:
            return json.load(f)
    except:
        return {}


def save_thresholds(thresh: dict):
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(THRESHOLD_FILE, "w") as f:
        json.dump(thresh, f, indent=2)


def load_thresholds() -> dict:
    try:
        if os.path.exists(THRESHOLD_FILE):
            with open(THRESHOLD_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {
        "entry_threshold": DEFAULT_ENTRY_THRESHOLD,
        "exit_threshold": DEFAULT_EXIT_THRESHOLD
    }


# 🔓 Public APIs

def get_entry_threshold():
    return load_thresholds().get("entry_threshold", DEFAULT_ENTRY_THRESHOLD)

def get_exit_threshold():
    return load_thresholds().get("exit_threshold", DEFAULT_EXIT_THRESHOLD)


def generate_thresholds_from_signal_summary():
    """
    Optional nightly call to read yesterday's signal performance log and recalculate thresholds.
    Assumes analytics/signal_performance.py outputs to data/signal_stats_YYYYMMDD.json
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    stats_file = os.path.join(DATA_PATH, f"signal_stats_{yesterday}.json")
    signal_stats = load_signal_stats_from_file(stats_file)

    if signal_stats:
        updated = compute_adaptive_thresholds(signal_stats)
        save_thresholds(updated)
        print(f"✅ Adaptive thresholds saved: {updated}")
    else:
        print(f"⚠️ No signal stats found in {stats_file}, using defaults.")
