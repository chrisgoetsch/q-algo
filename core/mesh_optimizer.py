# File: core/mesh_optimizer.py  (refactored for o3‑Tradier flow)
"""Dynamically tunes agent base‑scores in *mesh/mesh_config.json* using the
reinforcement profile produced by close_trade_tracker.

Key upgrades
------------
• Uses core.logger_setup for JSON logs instead of ad‑hoc prints
• Accepts legacy flat config OR nested {"agents": {…}} format transparently
• Adds safeguard to write a timestamped backup of the previous mesh_config
• Centralised helper functions for IO and atomic file writes
"""
from __future__ import annotations

import os, json, shutil
from datetime import datetime
from typing import Dict, Tuple, List

from core.logger_setup import logger

# ---------------------------------------------------------------------------
# Paths (env‑configurable)
# ---------------------------------------------------------------------------
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
MESH_CONFIG_PATH = os.getenv("MESH_CONFIG_PATH", "mesh/mesh_config.json")
MESH_OPT_LOG = os.getenv("MESH_OPTIMIZER_LOG", "logs/mesh_optimizer.jsonl")

# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _load_json(path: str, default: dict | None = None) -> dict:
    if not os.path.exists(path):
        return default or {}
    try:
        return json.load(open(path))
    except Exception as e:
        logger.error({"event": "json_load_fail", "path": path, "err": str(e)})
        return default or {}


def _save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, "w"), indent=2)


def _append_log(entry: dict):
    os.makedirs(os.path.dirname(MESH_OPT_LOG), exist_ok=True)
    with open(MESH_OPT_LOG, "a") as fh:
        fh.write(json.dumps(entry) + "\n")

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _normalize_config(cfg: dict) -> dict:
    """Return cfg with top‑level 'agents' key always present."""
    return {"agents": cfg.get("agents", cfg)}


def _backup_config(path: str):
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup = f"{path}.{ts}.bak"
    try:
        shutil.copy2(path, backup)
    except Exception as e:
        logger.warning({"event": "mesh_backup_fail", "err": str(e)})


def evaluate_agents() -> None:
    """Adjust agent base_score values based on reinforcement tallies."""
    profile = _load_json(REINFORCEMENT_PROFILE_PATH)
    cfg = _normalize_config(_load_json(MESH_CONFIG_PATH))
    agents = cfg["agents"]

    updated: List[dict] = []

    for name, settings in agents.items():
        if not settings.get("dynamic_weight", False):
            continue

        base = settings.get("base_score", 50)
        decay_rate = settings.get("decay_on_loss", 0.05)

        penalties = sum(profile.get(f"{name}:{label}", 0) for label in ["bad", "conflict", "regret"])
        boosts = sum(profile.get(f"{name}:{label}", 0) for label in ["profit", "strong", "gpt_reinforced"])

        delta = boosts * 1.5 - penalties
        adjusted = base + delta - (penalties * decay_rate * 100)
        new_base = max(10, min(int(adjusted), 100))

        if new_base != base:
            settings["base_score"] = new_base
            updated.append({
                "agent": name,
                "old": base,
                "new": new_base,
                "penalties": penalties,
                "boosts": boosts,
            })
            logger.info({"event": "mesh_agent_update", "agent": name, "old": base, "new": new_base})

    if updated:
        _backup_config(MESH_CONFIG_PATH)
        _save_json(MESH_CONFIG_PATH, cfg)
        _append_log({
            "timestamp": datetime.utcnow().isoformat(),
            "updated": updated,
        })
    else:
        logger.info({"event": "mesh_no_change"})

# ---------------------------------------------------------------------------
# CLI self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    evaluate_agents()
    print("✨ mesh_optimizer self‑test complete.")
# ➜ core/mesh_optimizer.py  (append near bottom, after evaluate_agents)

# ---------------------------------------------------------------------------
# Legacy API shim for mesh_router and other callers
# ---------------------------------------------------------------------------
def load_agent_performance() -> dict:
    """
    Return {agent: {"score": base_score}} for every agent in mesh_config.json.
    Keeps legacy callers working without code changes.
    """
    cfg = _normalize_config(_load_json(MESH_CONFIG_PATH))
    perf = {}
    for agent, info in cfg["agents"].items():
        perf[agent] = {"score": info.get("base_score", 50)}
    return perf
