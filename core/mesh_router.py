# mesh_router.py
# Q-ALGO v2 Mesh Agent Router (full integration with q_think and all agents, optimized for 10-agent strategy)

import os
import uuid
import json
import random
from datetime import datetime
from typing import Dict, List

from core.logger_setup import get_logger

from mesh.q_block import get_block_signal
from mesh.q_quant import get_quant_signal
from mesh.q_trap import get_trap_signal
from mesh.q_shield import get_shield_signal
from mesh.q_shadow import get_shadow_signal
from mesh.q_gamma import get_gamma_signal
from mesh.q_precision import sniper_entry_signal
from mesh.q_scout import get_scout_signal
from mesh.q_0dte_brain import score_and_log as score_q_brain
from mesh.q_think import synthesize_mesh_signals

logger = get_logger(__name__)
MESH_LOG_PATH = os.getenv("MESH_LOG_PATH", "logs/mesh_logger.jsonl")

AGENTS = [
    "q_block",
    "q_quant",
    "q_trap",
    "q_shield",
    "q_shadow",
    "q_gamma",
    "q_precision",
    "q_scout",
    "q_0dte_brain",
    "q_think"
]

SIGNAL_PATH = "logs/mesh_signals.jsonl"

AGENT_CALLS = [
    get_block_signal,
    get_quant_signal,
    get_trap_signal,
    lambda: {"agent": "q_shield", **get_shield_signal()},
    get_shadow_signal,
    get_gamma_signal,
    sniper_entry_signal,
    get_scout_signal,
    lambda: {"agent": "q_0dte_brain", **score_q_brain({
        "spy_price": 443.12,
        "vix": 15.2,
        "gex": -800_000_000,
        "dex": 900_000_000,
        "vwap_diff": -0.08,
        "skew": 1.11
    })}
]

def write_mesh_log(entry: dict):
    """
    Writes a mesh-related event or signal to persistent log.
    Safe for use across agents or exit evaluators.

    Format: JSONL with timestamp field auto-patched if missing.
    """
    try:
        os.makedirs(os.path.dirname(MESH_LOG_PATH), exist_ok=True)
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.utcnow().isoformat()

        with open(MESH_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

    except Exception as e:
        from core.logger_setup import logger
        logger.warning({
            "event": "mesh_log_write_fail",
            "err": str(e),
            "fallback_entry": entry
        })

def _log_signal(entry):
    os.makedirs(os.path.dirname(SIGNAL_PATH), exist_ok=True)
    with open(SIGNAL_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_all_agent_signals() -> List[dict]:
    """Calls each mesh agent to retrieve a directional signal."""
    signals = []
    for fn in AGENT_CALLS:
        try:
            result = fn()
            if result and isinstance(result, dict) and result.get("score", 0) >= 0.4:
                sig_id = str(uuid.uuid4())
                result["signal_id"] = sig_id
                result["timestamp"] = result.get("timestamp") or datetime.utcnow().isoformat()
                signals.append(result)
                _log_signal(result)
                logger.info({"event": "mesh_agent_signal", "agent": result["agent"], "score": result["score"], "direction": result["direction"]})
        except Exception as e:
            logger.warning({"event": "mesh_agent_fail", "agent": getattr(fn, "__name__", str(fn)), "err": str(e)})
    return signals

def summarize_votes(signals: List[dict]) -> str:
    votes = []
    for s in signals:
        direction = s.get("direction")
        agent = s.get("agent")
        score = s.get("score", 0)
        if direction:
            status = "✅" if score >= 0.5 else "⚠️"
            votes.append(f"   {agent:<12}: {direction.upper():<4} ({score:.2f}) {status}")
    final_score = round(sum(s.get("score", 0) for s in signals) / max(1, len(signals)), 3)
    print("\n🔍 MESH VOTES:")
    print("\n".join(votes))
    print(f"→ Final mesh_score: {final_score}\n")
    return final_score

def get_mesh_signal(context: dict = None) -> dict:
    """Wrapper to get signals and return GPT-synthesized mesh score."""
    agent_signals = get_all_agent_signals()
    mesh_result = synthesize_mesh_signals(agent_signals)
    summarize_votes(agent_signals)
    return mesh_result

if __name__ == "__main__":
    all_signals = get_all_agent_signals()
    summarize_votes(all_signals)

def score_exit_signals(context: dict, position: dict) -> dict:
    """
    Computes exit decision based on mesh agent divergence, decay, and PnL.
    Returns:
        {
            "signal": "exit" | "hold",
            "confidence": float,
            "votes": list of diverging agents,
            "agent_signals": {...},
            "mesh_score": float,
            "alpha_decay": float,
            "pnl": float
        }
    """
    try:
        alpha_decay = context.get("alpha_decay", 0.0)
        mesh_score = context.get("mesh_score", 50)
        pnl = context.get("pnl", 0.0)

        agent_signals = position.get("agent_signals") or {}
        if not agent_signals:
            logger.warning({
                "event": "exit_signal_missing_agents",
                "position": position.get("symbol")
            })

        # Agents with confidence < 0.5 are considered diverging
        exit_votes = [agent for agent, score in agent_signals.items() if score < 0.5]

        # Composite exit confidence
        exit_confidence = round(min(1.0, (len(exit_votes) / (len(agent_signals) or 1)) + alpha_decay), 3)

        signal = "exit" if exit_confidence >= 0.65 or pnl < -0.25 else "hold"

        result = {
            "signal": signal,
            "confidence": exit_confidence,
            "votes": exit_votes,
            "agent_signals": agent_signals,
            "mesh_score": mesh_score,
            "alpha_decay": alpha_decay,
            "pnl": pnl
        }

        logger.info({
            "event": "exit_signal_scored",
            "symbol": position.get("symbol"),
            **result
        })

        if write_mesh_log:
            write_mesh_log({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "exit_eval",
                "symbol": position.get("symbol"),
                **result
            })

        return result

    except Exception as e:
        logger.error({
            "event": "exit_signal_score_failed",
            "err": str(e),
            "position": position.get("symbol")
        })
        return {
            "signal": "hold",
            "confidence": 0.0,
            "votes": [],
            "agent_signals": {},
            "mesh_score": 0,
            "alpha_decay": 0,
            "pnl": 0.0
        }
