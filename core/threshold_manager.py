# File: core/threshold_manager.py  (refactored)
"""Adaptive entry/exit threshold management.

New features
============
* Threshold file rolls daily but loader gracefully falls back to latest present
  file if today's file missing.
* Structured logger usage via core.logger_setup.
* Helper `update_daily_thresholds(signal_stats)` for intraday recalculation.
* Environment override via ENTRY_THRESHOLD_OVERRIDE / EXIT_THRESHOLD_OVERRIDE.
"""
from __future__ import annotations

import os, json, glob
from datetime import datetime, timedelta
from typing import Dict

from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Defaults & paths
# ---------------------------------------------------------------------------
DATA_PATH = os.getenv("THRESHOLD_DATA_DIR", "data")
DEFAULT_ENTRY_THRESHOLD = float(os.getenv("DEFAULT_ENTRY_THRESHOLD", 0.7))
DEFAULT_EXIT_THRESHOLD = float(os.getenv("DEFAULT_EXIT_THRESHOLD", 0.5))

ENTRY_OVERRIDE = os.getenv("ENTRY_THRESHOLD_OVERRIDE")
EXIT_OVERRIDE = os.getenv("EXIT_THRESHOLD_OVERRIDE")

# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def _file_for(date: datetime) -> str:
    return os.path.join(DATA_PATH, f"thresholds_{date.strftime('%Y%m%d')}.json")


def _latest_file() -> str | None:
    files = sorted(glob.glob(os.path.join(DATA_PATH, "thresholds_*.json")), reverse=True)
    return files[0] if files else None

# ---------------------------------------------------------------------------
# Core calculators
# ---------------------------------------------------------------------------

def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(val, hi))


def compute_adaptive_thresholds(signal_stats: Dict[str, Dict]) -> Dict[str, float]:
    if not signal_stats:
        return {
            "entry_threshold": DEFAULT_ENTRY_THRESHOLD,
            "exit_threshold": DEFAULT_EXIT_THRESHOLD,
        }
    avg_hit = sum(v["hit_rate"] for v in signal_stats.values()) / len(signal_stats)
    avg_ret = sum(v["avg_return"] for v in signal_stats.values()) / len(signal_stats)

    entry = _clamp(DEFAULT_ENTRY_THRESHOLD + 0.1 * (0.6 - avg_hit), 0.5, 0.9)
    exit_ = _clamp(DEFAULT_EXIT_THRESHOLD + 0.1 * (0.1 - avg_ret), 0.3, 0.8)

    return {
        "entry_threshold": round(entry, 3),
        "exit_threshold": round(exit_, 3),
        "hit_rate": round(avg_hit, 3),
        "avg_return": round(avg_ret, 3),
    }

# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def _save_thresholds(th: Dict):
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(_file_for(datetime.utcnow()), "w") as fh:
        json.dump(th, fh, indent=2)


def _load_thresholds() -> Dict[str, float]:
    today_file = _file_for(datetime.utcnow())
    candidate = today_file if os.path.exists(today_file) else _latest_file()
    if candidate and os.path.exists(candidate):
        try:
            return json.load(open(candidate))
        except Exception as e:
            logger.error({"event": "threshold_read_fail", "err": str(e)})
    return {
        "entry_threshold": DEFAULT_ENTRY_THRESHOLD,
        "exit_threshold": DEFAULT_EXIT_THRESHOLD,
    }

# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------

def get_entry_threshold() -> float:
    if ENTRY_OVERRIDE:
        return float(ENTRY_OVERRIDE)
    return _load_thresholds().get("entry_threshold", DEFAULT_ENTRY_THRESHOLD)


def get_exit_threshold() -> float:
    if EXIT_OVERRIDE:
        return float(EXIT_OVERRIDE)
    return _load_thresholds().get("exit_threshold", DEFAULT_EXIT_THRESHOLD)


def update_daily_thresholds(signal_stats: Dict[str, Dict]):
    th = compute_adaptive_thresholds(signal_stats)
    _save_thresholds(th)
    logger.info({"event": "thresholds_updated", **th})

# ---------------------------------------------------------------------------
# CLI self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Fake stats to test adaptive calc
    fake_stats = {
        "agent1": {"hit_rate": 0.55, "avg_return": 0.12},
        "agent2": {"hit_rate": 0.65, "avg_return": 0.08},
    }
    update_daily_thresholds(fake_stats)
    print("Current entry threshold →", get_entry_threshold())
