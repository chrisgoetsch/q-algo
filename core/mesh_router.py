# File: core/mesh_router.py

import random
from datetime import datetime
from core.mesh_optimizer import load_agent_performance
from core.log_manager import write_mesh_log

# Active mesh agents
AGENTS = ["q_block", "q_trap", "q_quant", "q_precision", "q_scout"]


def get_mesh_signal(context):
    symbol = context.get("symbol", "SPY")
    return score_mesh_signals(symbol, context)

def score_mesh_signals(symbol="SPY", context=None):
    """
    Dynamic mesh agent scoring with real-time context sensitivity.
    """
    if context is None:
        context = {}

    perf = load_agent_performance()
    triggered = []
    agent_signals = {}

    # Pull live values from context
    iv = context.get("iv", 0)
    delta = context.get("delta", 0)
    gamma = context.get("gamma", 0)
    skew = context.get("skew", 0)
    dealer_flow = context.get("dealer_flow", 0)

    for agent in AGENTS:
        base_score = perf[agent]["score"] / 100

        # Adjust each agent by custom context logic
        if agent == "q_block":
            mod = gamma * 0.5 + skew * 0.2
        elif agent == "q_trap":
            mod = iv * 0.3 + dealer_flow * 0.4
        elif agent == "q_quant":
            mod = delta * 0.6 + iv * 0.2
        elif agent == "q_precision":
            mod = gamma * 0.3 + skew * 0.3
        elif agent == "q_scout":
            mod = dealer_flow * 0.3 + iv * 0.2
        else:
            mod = 0

        final_chance = min(1.0, base_score + mod)
        agent_signals[agent] = round(final_chance, 2)

        if random.random() < final_chance:
            triggered.append(agent)

    score = sum(perf[agent]["score"] for agent in triggered)
    score = min(score, 100)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "triggered_agents": triggered,
        "mesh_score": score,
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
        "score": score,
        "trigger_agents": triggered,
        "agent_signals": agent_signals
    }

def score_exit_signals(context, position):
    """
    Adaptive mesh-based exit signal generator using context features.
    Evaluates agent confidence based on delta, gamma, IV, etc.
    """
    perf = load_agent_performance()
    triggered = []

    # Extract context features
    iv = context.get("iv", 0)
    delta = context.get("delta", 0)
    gamma = context.get("gamma", 0)
    skew = context.get("skew", 0)
    dealer_flow = context.get("dealer_flow", 0)
    pnl = position.get("pnl", 0)

    for agent in AGENTS:
        base_score = perf[agent]["score"] / 100

        # Apply exit-specific modifiers
        if agent == "q_block":
            mod = skew * 0.3 - pnl * 0.05
        elif agent == "q_trap":
            mod = iv * 0.2 + dealer_flow * 0.3
        elif agent == "q_quant":
            mod = delta * 0.5 + pnl * 0.1
        elif agent == "q_precision":
            mod = gamma * 0.4 - pnl * 0.05
        elif agent == "q_scout":
            mod = dealer_flow * 0.3 + iv * 0.1
        else:
            mod = 0

        final_chance = min(1.0, max(0.0, base_score + mod))
        if random.random() < final_chance:
            triggered.append(agent)

    confidence = (
        sum(perf[agent]["score"] for agent in triggered) / 100 if triggered else 0.0
    )
    confidence = min(confidence, 1.0)
    signal = "exit" if confidence > 0.6 else "hold"

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "trigger_agents": triggered,
        "rationale": f"{len(triggered)} agents triggered: {', '.join(triggered)}"
    }

