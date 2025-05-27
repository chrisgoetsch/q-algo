# File: core/mesh_router.py

import random
import uuid
import json
from datetime import datetime
from core.mesh_optimizer import load_agent_performance
from core.log_manager import write_mesh_log
from core.logger_setup import atomic_append_json
from mesh.q_0dte_brain import score_and_log as brain_score

MESH_SIGNAL_LOG = "logs/mesh_signals.jsonl"

AGENTS = ["q_block", "q_trap", "q_quant", "q_precision", "q_scout", "q_0dte_brain"]

def log_mesh_signal(agent_name, agent_score, mesh_score, context):
    signal_id = str(uuid.uuid4())
    entry = {
        "signal_id": signal_id,
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "agent_score": agent_score,
        "combined_score": mesh_score,
        "context": context
    }
    atomic_append_json(MESH_SIGNAL_LOG, entry)
    return signal_id

def get_mesh_signal(context):
    symbol = context.get("symbol", "SPY")
    return score_mesh_signals(symbol, context)

def score_mesh_signals(symbol="SPY", context=None):
    if context is None:
        context = {}

    perf = load_agent_performance()
    triggered = []
    agent_signals = {}
    signal_ids = {}

    iv = context.get("iv", 0)
    delta = context.get("delta", 0)
    gamma = context.get("gamma", 0)
    skew = context.get("skew", 0)
    dealer_flow = context.get("dealer_flow", 0)

    for agent in AGENTS:
        base_score = perf.get(agent, {}).get("score", 0) / 100

        if agent == "q_0dte_brain":
            state_vector = {
                "spy_price": context.get("price"),
                "vwap_diff": context.get("vwap_diff", 0),
                "skew": context.get("skew", 1.0),
                "gex": context.get("gex", 0),
                "vix": context.get("vix", 0)
            }
            brain_result = brain_score(state_vector)
            context["q_brain_pattern"] = brain_result["pattern_tag"]
            context["q_brain_suggestion"] = brain_result["suggested_action"]
            score = round(brain_result["confidence"], 2)
        elif agent == "q_block":
            mod = gamma * 0.5 + skew * 0.2
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_trap":
            mod = iv * 0.3 + dealer_flow * 0.4
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_quant":
            mod = delta * 0.6 + iv * 0.2
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_precision":
            mod = gamma * 0.3 + skew * 0.3
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_scout":
            mod = dealer_flow * 0.3 + iv * 0.2
            score = round(min(1.0, base_score + mod), 2)
        else:
            score = base_score

        agent_signals[agent] = score

        if random.random() < score:
            triggered.append(agent)

    mesh_score = min(sum(perf.get(agent, {}).get("score", 0) for agent in triggered), 100)

    for agent in AGENTS:
        signal_id = log_mesh_signal(agent, agent_signals[agent], mesh_score, context)
        signal_ids[agent] = signal_id

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "triggered_agents": triggered,
        "mesh_score": mesh_score,
        "agent_signals": agent_signals,
        "context_used": {
            "iv": iv,
            "delta": delta,
            "gamma": gamma,
            "skew": skew,
            "dealer_flow": dealer_flow
        }
    }
    write_mesh_log(log_entry)

    return {
        "score": mesh_score,
        "trigger_agents": triggered,
        "agent_signals": agent_signals,
        "signal_ids": signal_ids
    }

def score_exit_signals(context, position):
    perf = load_agent_performance()
    triggered = []

    iv = context.get("iv", 0)
    delta = context.get("delta", 0)
    gamma = context.get("gamma", 0)
    skew = context.get("skew", 0)
    dealer_flow = context.get("dealer_flow", 0)
    pnl = position.get("pnl", 0)

    for agent in AGENTS:
        base_score = perf.get(agent, {}).get("score", 0) / 100

        if agent == "q_0dte_brain":
            state_vector = {
                "spy_price": context.get("price"),
                "vwap_diff": context.get("vwap_diff", 0),
                "skew": context.get("skew", 1.0),
                "gex": context.get("gex", 0),
                "vix": context.get("vix", 0)
            }
            brain_result = brain_score(state_vector)
            context["q_brain_pattern"] = brain_result["pattern_tag"]
            context["q_brain_suggestion"] = brain_result["suggested_action"]
            score = round(brain_result["confidence"], 2)
        elif agent == "q_block":
            mod = skew * 0.3 - pnl * 0.05
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_trap":
            mod = iv * 0.2 + dealer_flow * 0.3
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_quant":
            mod = delta * 0.5 + pnl * 0.1
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_precision":
            mod = gamma * 0.4 - pnl * 0.05
            score = round(min(1.0, base_score + mod), 2)
        elif agent == "q_scout":
            mod = dealer_flow * 0.3 + iv * 0.1
            score = round(min(1.0, base_score + mod), 2)
        else:
            score = base_score

        if random.random() < score:
            triggered.append(agent)

    confidence = min(sum(perf.get(agent, {}).get("score", 0) for agent in triggered) / 100, 1.0) if triggered else 0.0
    signal = "exit" if confidence > 0.6 else "hold"

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "trigger_agents": triggered,
        "rationale": f"{len(triggered)} agents triggered: {', '.join(triggered)}"
    }
