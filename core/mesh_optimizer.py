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

    performance = {}
    for agent, info in config.items():
        performance[agent] = {"score": info.get("score", 50)}  # default score = 50
    return performance

def evaluate_agents():
    profile = load_json(REINFORCEMENT_PROFILE_PATH)
    config = load_json(MESH_CONFIG_PATH)

    penalized_labels = ["bad entry", "mesh conflict", "high regret"]
    threshold = 3
    flagged_agents = []

    for agent, settings in config.items():
        penalty_score = sum(profile.get(f"{agent}:{label}", 0) for label in penalized_labels)

        if penalty_score >= threshold:
            settings["enabled"] = False
            flagged_agents.append({"agent": agent, "penalty": penalty_score})

    save_json(MESH_CONFIG_PATH, config)

    write_log({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "optimize_mesh",
        "disabled_agents": flagged_agents
    })

if __name__ == "__main__":
    evaluate_agents()
