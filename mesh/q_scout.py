# q_scout.py
# Legacy pattern detector for SPY intraday scalps

import random

def scout_signal(symbol="SPY"):
    """
    Produces a legacy pattern-based score.
    Replace with real pattern logic or remove if deprecated.
    """
    try:
        pattern_score = round(random.uniform(0.2, 0.8), 3)
        return {
            "agent": "q_scout",
            "score": pattern_score,
            "direction": "CALL" if pattern_score > 0.5 else "PUT",
            "reason": "Legacy mean-reversion pattern triggered",
            "features": {
                "scout_score": pattern_score
            }
        }
    except Exception as e:
        print(f"[q_scout] Pattern detection failed: {e}")
        return None

