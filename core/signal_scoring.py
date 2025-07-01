# File: core/signal_scoring.py — upgraded for 10-agent mesh architecture

import json
import os

CONFIG_PATH = "mesh/mesh_config.json"

def load_agent_config():
    try:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError("mesh_config.json missing")

        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        return config.get("agents", {})

    except Exception as e:
        print(f"⚠️ Failed to load mesh_config: {e}")
        return {}


def score_signal(signal: dict, context: dict | None = None) -> float:
    """
    Scores a mesh agent signal using its base score + confidence weighting
    as defined in mesh_config.json.
    """
    try:
        agent = signal.get("agent", "unknown")
        raw_score = signal.get("score", 0.5)
        confidence = signal.get("confidence", 50) / 100  # normalize
        context = context or {}

        config = load_agent_config()
        agent_cfg = config.get(agent, {})

        if not agent_cfg.get("enabled", False):
            return 0.0

        base = agent_cfg.get("base_score", 50) / 100
        decay = agent_cfg.get("decay_on_loss", 0.0)

        # Simple weight: mix base + confidence
        final = 0.5 * base + 0.5 * confidence
        return round(final, 4)

    except Exception as e:
        print(f"❌ Signal scoring failed: {e}")
        return 0.0
