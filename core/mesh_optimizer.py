# File: core/mesh_optimizer.py

import os
import json
from datetime import datetime

# Paths
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
MESH_CONFIG_PATH = os.getenv("MESH_CONFIG_PATH", "mesh/mesh_config.json")
DYNAMIC_LOG_PATH = os.getenv("MESH_OPTIMIZER_LOG", "logs/mesh_optimizer.jsonl")

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def write_log(entry):
    os.makedirs(os.path.dirname(DYNAMIC_LOG_PATH), exist_ok=True)
    with open(DYNAMIC_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def load_agent_performance():
    """
    Load current agent scoring weights from mesh_config.json
    """
    if not os.path.exists(MESH_CONFIG_PATH):
        raise FileNotFoundError(f"{MESH_CONFIG_PATH} not found")

    with open(MESH_CONFIG_PATH, "r") as f:
        config = json.load(f)

    agents = config.get("agents", config)  # fallback for legacy format

    performance = {}
    for agent, info in agents.items():
        performance[agent] = {"score": info.get("base_score", 50)}
    return performance

def evaluate_agents():
    profile = load_json(REINFORCEMENT_PROFILE_PATH)
    config = load_json(MESH_CONFIG_PATH)

    agents = config.get("agents", config)  # fallback support
    updated_agents = []
    logs = []

    for agent, settings in agents.items():
        if not settings.get("dynamic_weight", False):
            continue

        base_score = settings.get("base_score", 50)
        decay_rate = settings.get("decay_on_loss", 0.05)

        # Penalties from reinforcement log
        penalties = sum(
            profile.get(f"{agent}:{label}", 0)
            for label in ["bad entry", "mesh conflict", "high regret"]
        )
        boosts = sum(
            profile.get(f"{agent}:{label}", 0)
            for label in ["profit target", "strong signal", "gpt_reinforced"]
        )

        delta = boosts * 1.5 - penalties
        adjusted = base_score + delta - (penalties * decay_rate * 100)

        new_score = max(10, min(int(adjusted), 100))  # clamp 10–100
        if new_score != base_score:
            settings["base_score"] = new_score
            updated_agents.append(agent)

            logs.append({
                "agent": agent,
                "old": base_score,
                "new": new_score,
                "delta": new_score - base_score,
                "penalties": penalties,
                "boosts": boosts
            })

    # Save and log
    if "agents" in config:
        config["agents"] = agents
    else:
        config = agents  # legacy fallback

    save_json(MESH_CONFIG_PATH, config)

    write_log({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "update_weights",
        "updated": logs
    })

if __name__ == "__main__":
    evaluate_agents()
