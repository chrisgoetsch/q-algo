# File: mesh/mesh_router.py

import random
import json
import os
from datetime import datetime
from utils.atomic_write import atomic_append_jsonl, atomic_write_json

MESH_LOGGER_PATH = "logs/mesh_logger.jsonl"
AGENT_PERFORMANCE_PATH = "logs/mesh_agent_performance.json"

AGENTS = ["q_trap", "q_quant", "q_block", "q_gamma", "q_shield"]

def write_mesh_log(entry):
    os.makedirs(os.path.dirname(MESH_LOGGER_PATH), exist_ok=True)
    atomic_append_jsonl(MESH_LOGGER_PATH, entry)

def initialize_agent_performance():
    os.makedirs(os.path.dirname(AGENT_PERFORMANCE_PATH), exist_ok=True)
    if not os.path.exists(AGENT_PERFORMANCE_PATH):
        perf = {agent: {"wins": 0, "losses": 0, "score": 50} for agent in AGENTS}
        atomic_write_json(AGENT_PERFORMANCE_PATH, perf)

def load_agent_performance():
    if not os.path.exists(AGENT_PERFORMANCE_PATH):
        initialize_agent_performance()
    with open(AGENT_PERFORMANCE_PATH, "r") as f:
        return json.load(f)

def save_agent_performance(perf_data):
    atomic_write_json(AGENT_PERFORMANCE_PATH, perf_data)

def score_mesh_signals(symbol="SPY"):
    """
    Score agent signals dynamically based on agent self-tuned scores.
    """
    perf = load_agent_performance()

    triggered = []
    for agent in AGENTS:
        agent_chance = perf[agent]["score"] / 100  # Normalize to 0–1
        if random.random() < agent_chance:
            triggered.append(agent)

    score = sum(perf[agent]["score"] for agent in triggered)
    score = min(score, 100)  # Normalize max

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "triggered_agents": triggered,
        "mesh_score": score
    }
    write_mesh_log(log_entry)

    return {
        "score": score,
        "trigger_agents": triggered
    }

def adjust_agent_performance(trigger_agents, outcome):
    """
    Adjust triggered agents based on trade outcome (profit or loss).
    """
    perf = load_agent_performance()

    for agent in trigger_agents:
        if agent not in perf:
            continue

        if outcome == "profit":
            perf[agent]["wins"] += 1
            perf[agent]["score"] = min(perf[agent]["score"] + 2, 100)
        else:
            perf[agent]["losses"] += 1
            perf[agent]["score"] = max(perf[agent]["score"] - 2, 0)

    save_agent_performance(perf)
