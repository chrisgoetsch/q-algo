# File: mesh/q_shield.py
# Q-ALGO v2 – Macro shock detector for SPY 0DTE defense layer

import json
from datetime import datetime
from polygon.polygon_utils import get_intraday_returns
from core.logger_setup import logger

VIX_DATA_PATH = "data/vix_watchlist.json"


def get_shield_signal():
    """
    Detects macro volatility shocks using VIX, VVIX, and SPY divergence.
    Emits directional defense signal with confidence and rationale.
    """
    try:
        with open(VIX_DATA_PATH, "r") as f:
            vix_data = json.load(f)
    except Exception as e:
        logger.warning({"agent": "q_shield", "event": "vix_data_load_fail", "error": str(e)})
        return {
            "agent": "q_shield",
            "confidence": 0.5,
            "direction": "neutral",
            "score": 40,
            "features": {},
            "timestamp": datetime.utcnow().isoformat()
        }

    vix_now = vix_data.get("latest_vix", 18)
    vix_1h = vix_data.get("prev_1h_vix", vix_now)
    vix_1d = vix_data.get("prev_1d_vix", vix_now)
    vvix_now = vix_data.get("latest_vvix", 90)
    vvix_1h = vix_data.get("prev_1h_vvix", vvix_now)
    spy_now = vix_data.get("spy_price", 0)
    spy_prev = vix_data.get("prev_spy", spy_now)

    delta_vix_1h = ((vix_now - vix_1h) / max(1, vix_1h)) * 100
    delta_vix_1d = ((vix_now - vix_1d) / max(1, vix_1d)) * 100
    delta_vvix_1h = ((vvix_now - vvix_1h) / max(1, vvix_1h)) * 100
    spy_change = ((spy_now - spy_prev) / max(1, spy_prev)) * 100
    intraday_rets = get_intraday_returns("SPY")

    reasons = []
    score = 85

    if vix_now >= 28:
        reasons.append(f"panic vix {vix_now}")
        score -= 60
    elif vix_now >= 24:
        reasons.append(f"elevated vix {vix_now}")
        score -= 30

    if delta_vix_1h >= 10:
        reasons.append(f"vix spike 1h +{delta_vix_1h:.1f}%")
        score -= 20
    if delta_vix_1d >= 15:
        reasons.append(f"vix spike 1d +{delta_vix_1d:.1f}%")
        score -= 15

    if delta_vvix_1h >= 12:
        reasons.append(f"vvix spike +{delta_vvix_1h:.1f}%")
        score -= 20
    elif vvix_now > 110:
        reasons.append(f"vvix high {vvix_now}")
        score -= 15

    if spy_change > 0 and delta_vix_1h > 5:
        reasons.append("divergence: SPY↑ VIX↑")
        score -= 25
    if spy_change < 0 and delta_vix_1h < -3:
        reasons.append("divergence: SPY↓ VIX↓")
        score -= 10

    score = max(0, min(score, 100))

    direction = "put" if score < 50 else "neutral"

    return {
        "agent": "q_shield",
        "score": round(score / 100, 4),
        "confidence": round(score, 2),
        "direction": direction,
        "features": {
            "vix_now": vix_now,
            "vvix_now": vvix_now,
            "delta_vix_1h": delta_vix_1h,
            "delta_vix_1d": delta_vix_1d,
            "delta_vvix_1h": delta_vvix_1h,
            "spy_change": spy_change,
            "intraday_spy_return": intraday_rets,
            "reasons": reasons
        },
        "timestamp": datetime.utcnow().isoformat()
    }
