# q_0dte_brain.py
# Learns and scores SPY 0DTE market state patterns using memory and GPT 
reflection

import json
from datetime import datetime
from q_0dte_memory import store_snapshot, fetch_recent_snapshots
from qthink_pattern_matcher import gpt_reflect_on_patterns

# Optional: advanced scoring engine coming later
def score_current_state(state_vector: dict) -> dict:
    """
    Analyze current state vector and return:
    - Pattern tag
    - Confidence score
    - Trade suggestion (e.g., 'buy call', 'scalp put', 'stand down')
    """
    spy_price = state_vector.get("spy_price", 0)
    vwap_diff = state_vector.get("vwap_diff", 0)
    skew = state_vector.get("skew", 1.0)
    gex = state_vector.get("gex", 0)

    pattern = "unclassified"
    suggestion = "stand down"
    confidence = 0.5

    # Rule-based classification for now
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
    """Wrapper to score state + log snapshot."""
    scored = score_current_state(state_vector)
    store_snapshot(state_vector, pattern_tag=scored["pattern_tag"])
    return scored

def compare_to_memory():
    """Runs GPT reflection on past 0DTE setups stored in memory."""
    recent = fetch_recent_snapshots(limit=20)
    summary = {
        "tags": [snap["pattern_tag"] for snap in recent if 
snap["pattern_tag"]],
        "result_outcomes": [snap["result"] for snap in recent if 
snap["result"]]
    }
    return gpt_reflect_on_patterns(summary)

if __name__ == "__main__":
    test_vector = {
        "spy_price": 437.15,
        "vix": 15.9,
        "gex": -900_000_000,
        "dex": 930_000_000,
        "vwap_diff": -0.17,
        "skew": 1.13
    }
    result = score_and_log(test_vector)
    print("🧠 Q-0DTE Pattern Scored:", json.dumps(result, indent=2))

