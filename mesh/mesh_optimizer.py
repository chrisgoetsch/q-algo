# mesh_optimizer.py
# Adjusts mesh agent weights over time based on performance

import json
from pathlib import Path

WEIGHTS_PATH = Path("data/adaptive_weights.json")

def load_weights():
    try:
        with open(WEIGHTS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[mesh_optimizer] Failed to load weights: {e}")
        return {}

def save_weights(weights):
    try:
        WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(WEIGHTS_PATH, "w") as f:
            json.dump(weights, f, indent=2)
        print("[mesh_optimizer] Weights saved")
    except Exception as e:
        print(f"[mesh_optimizer] Failed to save weights: {e}")

def adjust_weight(agent, result, learning_rate=0.05):
    """
    Increments or decrements agent weight based on win/loss outcome
    """
    weights = load_weights()
    score = weights.get(agent, 0.5)
    score += learning_rate if result == "win" else -learning_rate
    score = max(0.0, min(1.0, round(score, 3)))
    weights[agent] = score
    save_weights(weights)
    return score

