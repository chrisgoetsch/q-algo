# File: core/qthink_capital.py

import os
import json
from datetime import datetime

REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
CAPITAL_TRACKER_PATH = os.getenv("CAPITAL_TRACKER_PATH", "logs/capital_tracker.json")

MIN_ALLOC = 0.2  # Never allocate less than 20%
MAX_ALLOC = 1.0  # Never allocate more than 100%


def load_profile():
    if not os.path.exists(REINFORCEMENT_PROFILE_PATH):
        return {}
    with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
        return json.load(f)


def decay_weights(profile: dict, decay: float = 0.95) -> dict:
    """Apply exponential decay to all reinforcement scores."""
    return {k: v * decay for k, v in profile.items()}


def calculate_qthink_allocation(profile: dict) -> float:
    """
    Calculate allocation multiplier (0.2 to 1.0) based on good/bad label frequencies.
    Penalizes regret and bad setups. Rewards high-confidence wins.
    """
    penalties = sum(profile.get(k, 0) for k in ["high regret", "bad entry", "mesh conflict"])
    rewards = sum(profile.get(k, 0) for k in ["profit target", "strong signal", "mesh alignment"])

    score = 1.0 + (0.05 * rewards) - (0.1 * penalties)
    allocation = max(MIN_ALLOC, min(MAX_ALLOC, score))
    return round(allocation, 2)


def update_capital_tracker(new_alloc: float):
    """Write current allocation to tracker log."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "recommended_allocation": new_alloc
    }
    os.makedirs(os.path.dirname(CAPITAL_TRACKER_PATH), exist_ok=True)
    with open(CAPITAL_TRACKER_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


if __name__ == "__main__":
    profile = load_profile()
    profile = decay_weights(profile)
    alloc = calculate_qthink_allocation(profile)
    update_capital_tracker(alloc)
    print(f"✅ QThink recommends capital multiplier: {alloc:.2f}")
