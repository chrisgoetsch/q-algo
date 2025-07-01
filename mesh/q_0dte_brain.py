# File: mesh/q_0dte_brain.py
# Purpose: Pattern-based brain using SPY microstructure and GPT reflection

import json
from datetime import datetime
from mesh.q_0dte_memory import store_snapshot, fetch_recent_snapshots
from qthink.qthink_pattern_matcher import gpt_reflect_on_patterns
from polygon.polygon_utils import (
    get_vwap_diff,
    get_gex_score,
    get_skew,
    get_intraday_returns
)

def score_current_state(state_vector: dict) -> dict:
    spy_price = state_vector.get("spy_price", 0)
    vwap_diff = state_vector.get("vwap_diff", 0)
    skew = state_vector.get("skew", 1.0)
    gex = state_vector.get("gex", 0)

    pattern = "unclassified"
    suggestion = "stand down"
    confidence = 0.5

    if gex < -800_000_000 and vwap_diff < -0.1 and skew > 1.1:
        pattern = "gamma_fade"
        suggestion = "scalp put"
        confidence = 0.78
    elif gex > -700_000_000 and vwap_diff > 0.1 and skew < 1.08:
        pattern = "vwap_reclaim"
        suggestion = "buy call"
        confidence = 0.82
    elif abs(vwap_diff) < 0.05:
        pattern = "compression_chop"
        suggestion = "avoid"
        confidence = 0.4

    return {
        "pattern_tag": pattern,
        "confidence": confidence,
        "suggested_action": suggestion,
        "timestamp": datetime.utcnow().isoformat()
    }

def score_and_log(state_vector: dict):
    scored = score_current_state(state_vector)
    store_snapshot(state_vector, pattern_tag=scored["pattern_tag"])
    return scored

def compare_to_memory():
    recent = fetch_recent_snapshots(limit=20)
    summary = {
        "tags": [snap.get("pattern_tag", "") for snap in recent if snap.get("pattern_tag")],
        "result_outcomes": [snap.get("result", "") for snap in recent if snap.get("result")]
    }
    try:
        reflection = gpt_reflect_on_patterns(summary)
        if isinstance(reflection, dict):
            return reflection
        else:
            return {"error": "unexpected GPT output", "raw": reflection}
    except Exception as e:
        return {"error": str(e), "status": "GPT reflection failed"}

# Live signal builder for mesh_router
def get_0dte_brain_signal() -> dict:
    try:
        vwap_diff = get_vwap_diff("SPY")
        gex = get_gex_score("SPY")
        skew = get_skew("SPY")
        spy_return = get_intraday_returns("SPY")

        state = {
            "spy_price": spy_return.get("price", 0),
            "vwap_diff": vwap_diff,
            "gex": gex,
            "skew": skew,
            "return": spy_return.get("return", 0)
        }

        result = score_and_log(state)
        return {
            "agent": "q_0dte_brain",
            "score": result["confidence"],
            "direction": "call" if result["suggested_action"] == "buy call" else "put",
            "pattern": result["pattern_tag"],
            "confidence": round(result["confidence"] * 100),
            "features": state,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        from core.logger_setup import logger
        logger.warning({"event": "q_0dte_brain_fail", "error": str(e)})
        return None

# Mesh entrypoint
brain_score = score_and_log
