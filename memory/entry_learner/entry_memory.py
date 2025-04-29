# entry_memory.py
# Logs feature vectors and model-predicted entries for reinforcement 
learning

import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("memory/entry_learner/edge_tagged_set.jsonl")


def log_entry_features(state_vector: dict, score: float, decision: str, 
label: str = None):
    """Logs entry features, model decision, and optional GPT label for 
training."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "features": state_vector,
        "entry_score": score,
        "decision": decision,  # enter / skip / pass
        "label": label  # Optional supervised outcome (win/loss/neutral)
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def fetch_recent_entries(limit: int = 25):
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]


if __name__ == "__main__":
    test_vec = {
        "spy_price": 435.2,
        "vix": 16.1,
        "gex": -820000000,
        "dex": 910000000,
        "vwap_diff": -0.12,
        "skew": 1.12,
        "time_of_day_bin": 2
    }
    log_entry_features(test_vec, score=0.87, decision="enter", 
label="win")

