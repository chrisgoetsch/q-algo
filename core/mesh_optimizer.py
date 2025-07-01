# core/mesh_optimizer.py
# Q-ALGO v2 - Mesh Agent Reinforcement Optimizer (10-agent upgrade, GPT-aligned)

import os, json, shutil
from datetime import datetime
from typing import Dict, List

from core.logger_setup import logger

REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
MESH_CONFIG_PATH = os.getenv("MESH_CONFIG_PATH", "mesh/mesh_config.json")
MESH_OPT_LOG = os.getenv("MESH_OPTIMIZER_LOG", "logs/mesh_optimizer.jsonl")

def _load_json(path: str, default: dict | None = None) -> dict:
    if not os.path.exists(path):
        return default or {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error({"event": "json_load_fail", "path": path, "err": str(e)})
        return default or {}

def _save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def _append_log(entry: dict):
    os.makedirs(os.path.dirname(MESH_OPT_LOG), exist_ok=True)
    with open(MESH_OPT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def _normalize_config(cfg: dict) -> dict:
    return {"agents": cfg.get("agents", cfg)}

def _backup_config(path: str):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.{ts}.bak"
    try:
        shutil.copy2(path, backup_path)
        logger.info({"event": "mesh_config_backup", "path": backup_path})
    except Exception as e:
        logger.warning({"event": "backup_fail", "err": str(e)})

def evaluate_agents() -> None:
    profile = _load_json(REINFORCEMENT_PROFILE_PATH)
    cfg = _normalize_config(_load_json(MESH_CONFIG_PATH))
    agents = cfg["agents"]
    updated: List[dict] = []

    for name, config in agents.items():
        if not config.get("dynamic_weight", False):
            continue

        base = config.get("base_score", 50)
        decay_rate = config.get("decay_on_loss", 0.05)

        penalties = sum(profile.get(f"{name}:{label}", 0) for label in ["bad", "conflict", "regret"])
        boosts = sum(profile.get(f"{name}:{label}", 0) for label in ["profit", "strong", "gpt_reinforced"])

        delta = boosts * 1.5 - penalties
        adjusted = base + delta - (penalties * decay_rate * 100)
        new_base = max(10, min(int(adjusted), 100))

        if new_base != base:
            config["base_score"] = new_base
            updated.append({
                "agent": name,
                "old": base,
                "new": new_base,
                "penalties": penalties,
                "boosts": boosts
            })
            logger.info({
                "event": "mesh_agent_update",
                "agent": name,
                "old": base,
                "new": new_base
            })

    if updated:
        _backup_config(MESH_CONFIG_PATH)
        _save_json(MESH_CONFIG_PATH, cfg)
        _append_log({
            "timestamp": datetime.utcnow().isoformat(),
            "updated": updated
        })
    else:
        logger.info({"event": "mesh_no_change"})

def load_agent_performance() -> dict:
    """Returns {agent: {"score": base_score}} for mesh_router legacy use."""
    cfg = _normalize_config(_load_json(MESH_CONFIG_PATH))
    return {a: {"score": info.get("base_score", 50)} for a, info in cfg["agents"].items()}

if __name__ == "__main__":
    evaluate_agents()
    print("✅ Mesh optimizer self-test complete.")
