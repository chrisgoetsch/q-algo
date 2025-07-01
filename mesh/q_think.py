# File: mesh/q_think.py — Meta-agent to synthesize all mesh signals

import json
from datetime import datetime
from qthink.qthink_pattern_matcher import gpt_reflect_on_patterns
from core.logger_setup import logger

JOURNAL_PATH = "logs/qthink_journal_summary.json"


def synthesize_mesh_signals(agent_outputs: list[dict]) -> dict:
    """
    Synthesizes all mesh agent signals into a unified decision.
    Uses GPT reflection when available, or falls back to rule-based averaging.
    """
    if not agent_outputs:
        return {
            "agent": "q_think",
            "score": 0.0,
            "direction": "none",
            "rationale": "No signals received",
            "mesh_votes": {},
            "timestamp": datetime.utcnow().isoformat()
        }

    mesh_votes = {
        agent["agent"]: {
            "score": agent.get("score"),
            "direction": agent.get("direction"),
            "confidence": agent.get("confidence", 0),
            "features": agent.get("features", {})
        }
        for agent in agent_outputs if agent.get("score") is not None
    }

    scores = [a["score"] for a in agent_outputs if "score" in a]
    directions = [a["direction"] for a in agent_outputs if "direction" in a]

    try:
        reflection = gpt_reflect_on_patterns({"agent_data": agent_outputs})
        if not isinstance(reflection, dict):
            raise ValueError("GPT returned non-dict")

        direction = reflection.get("final_direction", "stand down")
        score = float(reflection.get("confidence_score", 0.5))
        rationale = reflection.get("rationale", "GPT reflection returned no rationale")

    except Exception as e:
        direction = max(set(directions), key=directions.count)
        score = round(sum(scores) / len(scores), 3)
        rationale = f"Fallback rule-based mesh average. GPT failed: {str(e)}"

    result = {
        "agent": "q_think",
        "score": round(score, 4),
        "direction": direction,
        "rationale": rationale,
        "mesh_votes": mesh_votes,
        "timestamp": datetime.utcnow().isoformat()
    }

    _log_qthink_summary(result)
    logger.info({
        "event": "qthink_meta_signal",
        "score": result["score"],
        "direction": result["direction"],
        "reason": result["rationale"]
    })

    return result


def _log_qthink_summary(summary: dict):
    try:
        with open(JOURNAL_PATH, "a") as f:
            f.write(json.dumps(summary) + "\n")
    except Exception as e:
        logger.warning({"event": "qthink_log_fail", "err": str(e)})


if __name__ == "__main__":
    # Dry run test
    mock_agents = [
        {"agent": "q_block", "score": 0.83, "direction": "call"},
        {"agent": "q_gamma", "score": 0.78, "direction": "call"},
        {"agent": "q_shield", "score": 0.42, "direction": "put"},
        {"agent": "q_precision", "score": 0.91, "direction": "call"},
        {"agent": "q_0dte_brain", "score": 0.81, "direction": "call"},
    ]
    print(json.dumps(synthesize_mesh_signals(mock_agents), indent=2))
