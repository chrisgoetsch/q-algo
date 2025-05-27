# File: mesh/q_shield.py
# Purpose: Detect macro volatility shocks using VIX, VVIX, and divergence from SPY

import json
from datetime import datetime

VIX_DATA_PATH = "data/vix_watchlist.json"

def score_shield(context=None):
    """
    Emit a mesh agent-style confidence score based on macro volatility behavior.
    Includes VIX levels, deltas, divergence from SPY, and VVIX spike detection.
    """

    try:
        with open(VIX_DATA_PATH, "r") as f:
            vix_data = json.load(f)
    except Exception as e:
        return {
            "score": 40,
            "reason": "fallback",
            "error": str(e),
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

    reasons = []
    score = 85  # Start high, reduce on warning signals

    # 1. Panic-level VIX
    if vix_now >= 28:
        reasons.append(f"panic vix {vix_now}")
        score -= 60
    elif vix_now >= 24:
        reasons.append(f"elevated vix {vix_now}")
        score -= 30

    # 2. Sharp 1h or 1d VIX spike
    if delta_vix_1h >= 10:
        reasons.append(f"vix spike 1h +{delta_vix_1h:.1f}%")
        score -= 20
    if delta_vix_1d >= 15:
        reasons.append(f"vix spike 1d +{delta_vix_1d:.1f}%")
        score -= 15

    # 3. VVIX alert
    if delta_vvix_1h >= 12:
        reasons.append(f"vvix spike +{delta_vvix_1h:.1f}%")
        score -= 20
    elif vvix_now > 110:
        reasons.append(f"vvix high {vvix_now}")
        score -= 15

    # 4. SPY/VIX divergence
    if spy_change > 0 and delta_vix_1h > 5:
        reasons.append("divergence: SPY↑ VIX↑")
        score -= 25
    if spy_change < 0 and delta_vix_1h < -3:
        reasons.append("divergence: SPY↓ VIX↓")
        score -= 10

    score = max(0, min(score, 100))

    return {
        "score": score,
        "vix": vix_now,
        "vvix": vvix_now,
        "vix_1h_change_pct": delta_vix_1h,
        "vvix_1h_change_pct": delta_vvix_1h,
        "spy_change_pct": spy_change,
        "reasons": reasons,
        "timestamp": datetime.utcnow().isoformat()
    }
