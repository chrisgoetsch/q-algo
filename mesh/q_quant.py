# q_quant.py
# Q-ALGO v2 - Statistical edge detection using IV skew + gamma compression

import datetime
from polygon.polygon_iv_surface import build_iv_surface
from polygon.polygon_utils import round_to_nearest_strike

def get_quant_signal():
    try:
        surface = build_iv_surface("SPY")
        if not surface:
            return None

        today = max(surface.keys())
        strikes = list(surface[today].keys())
        if not strikes:
            return None

        atm_price = 443.00  # could be live later
        atm_strike = round_to_nearest_strike(atm_price)

        iv_atm = surface[today].get(atm_strike)
        iv_wing_up = surface[today].get(atm_strike + 10)
        iv_wing_down = surface[today].get(atm_strike - 10)

        if iv_atm is None or iv_wing_up is None or iv_wing_down is None:
            return None

        skew = round(iv_wing_down - iv_wing_up, 3)
        crush_score = round(1.0 - iv_atm, 3) if iv_atm < 0.3 else 0.2

        if skew < -0.2 and crush_score > 0.5:
            return {
                "agent": "q_quant",
                "confidence": 0.82,
                "direction": "put",
                "score": 0.84,
                "features": {
                    "skew": skew,
                    "iv_atm": iv_atm,
                    "crush_score": crush_score
                },
                "timestamp": datetime.datetime.utcnow().isoformat()
            }

        return None

    except Exception as e:
        print(f"⚠️ q_quant failed: {e}")
        return None

