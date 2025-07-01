# File: mesh/q_quant.py
# Q-ALGO v2 - Statistical edge detection using IV skew + gamma compression

import datetime
from typing import Optional
from polygon.polygon_iv_surface import build_iv_surface
from polygon.polygon_utils import round_to_nearest_strike
from polygon.polygon_rest import get_last_price
from core.logger_setup import logger

def get_quant_signal(symbol: str = "SPY") -> Optional[dict]:
    """
    Identifies statistical edge based on implied volatility skew and compression.
    """
    try:
        surface = build_iv_surface(symbol)
        if not surface:
            return None

        today = max(surface.keys())
        strikes = list(surface[today].keys())
        if not strikes:
            return None

        price = get_last_price()
        if not price or price < 100:
            return None

        atm_strike = round_to_nearest_strike(price)

        iv_atm = surface[today].get(atm_strike)
        iv_up  = surface[today].get(atm_strike + 10)
        iv_down = surface[today].get(atm_strike - 10)

        if any(v is None for v in [iv_atm, iv_up, iv_down]):
            return None

        skew = round(iv_down - iv_up, 4)
        crush_score = round(1.0 - iv_atm, 3) if iv_atm < 0.3 else 0.2

        score = round(abs(skew) * crush_score, 3)
        direction = "put" if skew < 0 else "call"

        return {
            "agent": "q_quant",
            "score": score,
            "confidence": round(score * 100),
            "direction": direction,
            "features": {
                "skew": skew,
                "iv_atm": iv_atm,
                "iv_up": iv_up,
                "iv_down": iv_down,
                "crush_score": crush_score,
                "price": price,
                "atm_strike": atm_strike
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error({"agent": "q_quant", "event": "signal_fail", "error": str(e)})
        return None
