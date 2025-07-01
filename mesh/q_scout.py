# File: mesh/q_scout.py
# Q-ALGO v2 – Legacy pattern-based SPY 0DTE agent upgraded with GPT logic

import json
from datetime import datetime
from polygon.polygon_utils import get_intraday_returns, get_vwap
from qthink.qthink_pattern_matcher import gpt_reflect_on_patterns
from core.logger_setup import logger


def get_scout_signal(symbol="SPY"):
    """
    Produces a pattern-based GPT signal for SPY 0DTE scalping.
    Uses intraday return, VWAP diff, and GPT scoring.
    """
    try:
        intraday_return = get_intraday_returns(symbol)
        vwap = get_vwap(symbol)
        features = {
            "intraday_return": intraday_return,
            "vwap": vwap,
            "symbol": symbol
        }

        reflection_input = {
            "agent": "q_scout",
            "data": features
        }
        gpt_result = gpt_reflect_on_patterns(reflection_input)

        direction = gpt_result.get("final_direction", "stand down")
        score = float(gpt_result.get("confidence_score", 0.5))
        rationale = gpt_result.get("rationale", "No rationale")

        if direction.lower() in ["call", "put"]:
            return {
                "agent": "q_scout",
                "score": round(score, 4),
                "direction": direction.lower(),
                "confidence": round(score * 100, 2),
                "features": {
                    **features,
                    "gpt_rationale": rationale
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        return None

    except Exception as e:
        logger.error({"agent": "q_scout", "event": "signal_fail", "err": str(e)})
        return None


if __name__ == "__main__":
    print(json.dumps(get_scout_signal(), indent=2))
