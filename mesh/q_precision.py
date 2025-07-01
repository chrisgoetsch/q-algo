# File: mesh/q_precision.py — Microstructure-Based Entry Signal (Polygon-powered)

from datetime import datetime
from polygon.polygon_rest import get_last_price
from polygon.polygon_utils import get_intraday_returns, get_vwap
from core.logger_setup import logger

def sniper_entry_signal(symbol="SPY"):
    """
    High-precision SPY signal based on:
    - VWAP vs. price
    - Return momentum
    - Latency placeholder (can be enhanced)
    """
    try:
        price = get_last_price(symbol)
        vwap = get_vwap(symbol)
        returns = get_intraday_returns(symbol, minutes=5)

        if not price or not vwap or not returns:
            return None

        spread = price - vwap
        return_slope = returns.get("slope", 0)

        score = 0.5
        direction = "put"

        if spread > 0 and return_slope > 0:
            score = 0.85
            direction = "call"
        elif spread < 0 and return_slope < 0:
            score = 0.75
            direction = "put"
        elif abs(spread) < 0.1 and abs(return_slope) < 0.03:
            score = 0.4
            direction = "put"
        else:
            return None  # no clean signal

        return {
            "agent": "q_precision",
            "score": round(score, 3),
            "direction": direction,
            "confidence": round(score * 100),
            "features": {
                "price": price,
                "vwap": vwap,
                "spread": round(spread, 3),
                "momentum": round(return_slope, 3)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error({"agent": "q_precision", "event": "signal_fail", "err": str(e)})
        return None
