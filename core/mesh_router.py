# File: core/mesh_router.py  (refactored for v2 logging)
"""Central hub that fuses individual agent signals into a single mesh score.

Highlights
----------
• Uses `core.logger_setup.get_logger(__name__)` instead of atomic_append_json.
• Writes mesh-signal details via logger at INFO level (JSON format).
• Keeps compatibility with legacy `log_manager.write_mesh_log` if present.
• Ensures deterministic mesh_score scaling (sum of triggered base_scores capped at 100).
"""
from __future__ import annotations

import random, uuid, json, os
from datetime import datetime
from typing import Dict, List

from core.mesh_optimizer import load_agent_performance
from core.logger_setup import get_logger

try:
    from core.log_manager import write_mesh_log  # legacy util
except ImportError:
    write_mesh_log = None  # type: ignore

from mesh.q_0dte_brain import score_and_log as brain_score

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------
MESH_SIGNAL_LOG = os.getenv("MESH_SIGNAL_LOG", "logs/mesh_signals.jsonl")
AGENTS: List[str] = [
    "q_block",
    "q_trap",
    "q_quant",
    "q_precision",
    "q_scout",
    "q_0dte_brain",
]

# ---------------------------------------------------------------------------
# Internal helper to persist per-agent signals
# ---------------------------------------------------------------------------

def _persist_signal(entry: dict):
    os.makedirs(os.path.dirname(MESH_SIGNAL_LOG), exist_ok=True)
    with open(MESH_SIGNAL_LOG, "a") as fh:
        fh.write(json.dumps(entry) + "\n")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_mesh_signal(context: Dict) -> Dict:
    symbol = context.get("symbol", "SPY")
    return _score_mesh_signals(symbol, context)

# ---------------------------------------------------------------------------
# Core scoring routine
# ---------------------------------------------------------------------------

def _score_mesh_signals(symbol: str, context: Dict | None = None) -> Dict:
    context = context or {}
    perf = {
    "q_block": {"score": 90},
    "q_trap": {"score": 92},
    "q_quant": {"score": 95},
    "q_precision": {"score": 93},
    "q_scout": {"score": 91},
    "q_0dte_brain": {"score": 85}
}


    triggered: List[str] = []
    agent_scores: Dict[str, float] = {}
    signal_ids: Dict[str, str] = {}

    # Pull commonly used context vars once
    iv = context.get("iv", 0)
    delta = context.get("delta", 0)
    gamma = context.get("gamma", 0)
    skew = context.get("skew", 0)
    dealer_flow = context.get("dealer_flow", 0)

    for agent in AGENTS:
        base = perf.get(agent, {}).get("score", 0) / 100  # convert to 0–1

        # Agent-specific modifiers
        if agent == "q_0dte_brain":
            state = {
                "spy_price": context.get("price"),
                "vwap_diff": context.get("vwap_diff", 0),
                "skew": skew or 1.0,
                "gex": context.get("gex", 0),
                "vix": context.get("vix", 0),
            }
            brain = brain_score(state)
            context.update({
                "q_brain_pattern": brain["pattern_tag"],
                "q_brain_suggestion": brain["suggested_action"],
            })
            score = round(brain["confidence"], 2)
        elif agent == "q_block":
            score = round(min(1.0, base + gamma * 0.5 + skew * 0.2), 2)
        elif agent == "q_trap":
            score = round(min(1.0, base + iv * 0.3 + dealer_flow * 0.4), 2)
        elif agent == "q_quant":
            score = round(min(1.0, base + delta * 0.6 + iv * 0.2), 2)
        elif agent == "q_precision":
            score = round(min(1.0, base + gamma * 0.3 + skew * 0.3), 2)
        elif agent == "q_scout":
            score = round(min(1.0, base + dealer_flow * 0.3 + iv * 0.2), 2)
        else:
            score = base

        agent_scores[agent] = score
        if random.random() < score:
            triggered.append(agent)

    mesh_score = min(sum(perf.get(a, {}).get("score", 0) for a in triggered), 100)

    # Persist individual agent signals
    for agent in AGENTS:
        sid = str(uuid.uuid4())
        signal_ids[agent] = sid
        _persist_signal({
            "signal_id": sid,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "agent_score": agent_scores[agent],
            "combined_score": mesh_score,
            "context": {
                "symbol": symbol,
                "iv": iv,
                "delta": delta,
                "gamma": gamma,
                "skew": skew,
                "dealer_flow": dealer_flow,
            },
        })

    # Structured log
    logger.info({
        "event": "mesh_score",
        "symbol": symbol,
        "mesh_score": mesh_score,
        "triggered": triggered,
    })

    # Legacy log manager if available
    if write_mesh_log:
        write_mesh_log({
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "triggered_agents": triggered,
            "mesh_score": mesh_score,
            "agent_signals": agent_scores,
        })

    return {
        "score": mesh_score,
        "trigger_agents": triggered,
        "agent_signals": agent_scores,
        "signal_ids": signal_ids,
    }

# ---------------------------------------------------------------------------
# Exit-signal scoring (unchanged except logger)
# ---------------------------------------------------------------------------

def score_exit_signals(context: Dict, position: Dict) -> Dict:
    perf = load_agent_performance()
    triggered: List[str] = []

    iv = context.get("iv", 0)
    delta = context.get("delta", 0)
    gamma = context.get("gamma", 0)
    skew = context.get("skew", 0)
    dealer_flow = context.get("dealer_flow", 0)
    pnl = position.get("pnl", 0)

    for agent in AGENTS:
        base = perf.get(agent, {}).get("score", 0) / 100

        if agent == "q_0dte_brain":
            state = {
                "spy_price": context.get("price"),
                "vwap_diff": context.get("vwap_diff", 0),
                "skew": skew or 1.0,
                "gex": context.get("gex", 0),
                "vix": context.get("vix", 0),
            }
            score = round(brain_score(state)["confidence"], 2)
        elif agent == "q_block":
            score = round(min(1.0, base + skew * 0.3 - pnl * 0.05), 2)
        elif agent == "q_trap":
            score = round(min(1.0, base + iv * 0.2 + dealer_flow * 0.3), 2)
        elif agent == "q_quant":
            score = round(min(1.0, base + delta * 0.5 + pnl * 0.1), 2)
        elif agent == "q_precision":
            score = round(min(1.0, base + gamma * 0.4 - pnl * 0.05), 2)
        elif agent == "q_scout":
            score = round(min(1.0, base + dealer_flow * 0.3 + iv * 0.1), 2)
        else:
            score = base

        if random.random() < score:
            triggered.append(agent)

    confidence = (
        min(sum(perf.get(a, {}).get("score", 0) for a in triggered) / 100, 1.0)
        if triggered
        else 0.0
    )
    signal = "exit" if confidence > 0.6 else "hold"

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "trigger_agents": triggered,
        "rationale": f"{len(triggered)} agents triggered: {', '.join(triggered)}",
    }
