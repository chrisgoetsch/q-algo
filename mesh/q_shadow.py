# File: mesh/q_shadow.py (Optimized for SPY dark flow detection)

import datetime
from polygon.polygon_utils import get_intraday_returns, get_vwap
from polygon.polygon_rest import get_last_price
from core.logger_setup import logger


def detect_dark_flow_anomaly(price: float, vwap: float, returns: list[float]) -> dict:
    """
    Detects potential dark pool / hidden bid activity via VWAP gap and abnormal return compression.
    """
    vwap_spread = (price - vwap) / vwap if vwap else 0.0
    avg_return = sum(returns[-5:]) / 5 if len(returns) >= 5 else 0.0
    compression = max(returns) - min(returns) if returns else 0.0

    confidence = 0.0
    direction = "none"
    rationale = []

    if vwap_spread > 0.004:
        direction = "call"
        confidence += 0.4
        rationale.append(f"price > VWAP ({vwap_spread:.2%})")
    elif vwap_spread < -0.004:
        direction = "put"
        confidence += 0.4
        rationale.append(f"price < VWAP ({vwap_spread:.2%})")

    if compression < 0.001 and abs(avg_return) > 0.0003:
        confidence += 0.4
        rationale.append("flow compression + non-zero drift")

    score = round(confidence, 3)
    return {
        "agent": "q_shadow",
        "score": score,
        "confidence": round(score * 100),
        "direction": direction,
        "features": {
            "vwap_spread": round(vwap_spread, 5),
            "avg_return": round(avg_return, 5),
            "compression": round(compression, 5),
        },
        "rationale": "; ".join(rationale),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


def get_shadow_signal() -> dict | None:
    try:
        price = get_last_price("SPY")
        vwap = get_vwap("SPY")
        returns = get_intraday_returns("SPY")

        if not price or not vwap or not returns:
            logger.warning("q_shadow missing data inputs")
            return None

        signal = detect_dark_flow_anomaly(price, vwap, returns)
        if signal["score"] < 0.5:
            return None
        return signal

    except Exception as e:
        logger.error({"agent": "q_shadow", "event": "signal_fail", "err": str(e)})
        return None
