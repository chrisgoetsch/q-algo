# signal_scoring.py
# Q-ALGO v2 - Scores agent signals using mesh_config weights

import json
import os

CONFIG_PATH = "mesh/mesh_config.json"

def load_agent_weights():
    try:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError("mesh_config.json missing")

        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        weights = {}
        for agent, data in config.get("agents", {}).items():
            if data.get("enabled", False):
                weights[agent] = data.get("weight", 0.5)

        return weights

    except Exception as e:
        print(f"⚠️ Failed to load mesh weights: {e}")
        return {}

def score_signal(signal):
    try:
        agent = signal.get("agent", "unknown")
        raw_score = signal.get("score", 0.5)
        confidence = signal.get("confidence", 0.5)

        weights = load_agent_weights()
        weight = weights.get(agent, 0.5)

        final_score = weight * ((raw_score + confidence) / 2)
        return round(final_score, 4)

    except Exception as e:
        print(f"❌ Scoring error: {e}")
        return 0.0

