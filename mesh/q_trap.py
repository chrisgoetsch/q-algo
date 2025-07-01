# File: mesh/q_trap.py — Liquidity trap detection agent (v2.0)

from datetime import datetime
from polygon.polygon_utils import (
    get_realtime_price,
    get_vwap,
    get_intraday_returns,
    get_recent_volume
)
from core.logger_setup import logger

def get_trap_signal() -> dict | None:
    try:
        price = get_realtime_price("SPY")
        vwap = get_vwap("SPY")
        volume = get_recent_volume("SPY")
        intraday = get_intraday_returns("SPY")

        if not price or not vwap:
            return None

        vwap_diff = price - vwap
        early_gain = intraday.get("first_hour_return", 0)
        fade_from_high = intraday.get("high_to_current_return", 0)
        fade_from_low = intraday.get("low_to_current_return", 0)

        # Trap logic 1: morning breakout reversed hard
        bull_trap = early_gain > 0.3 and fade_from_high < -0.4
        bear_trap = early_gain < -0.3 and fade_from_low > 0.4

        if not (bull_trap or bear_trap):
            return None

        direction = "put" if bull_trap else "call"
        confidence = 0.9 if abs(vwap_diff) > 1 else 0.75
        score = round(confidence, 3)

        signal = {
            "agent": "q_trap",
            "score": score,
            "confidence": round(confidence * 100),
            "direction": direction,
            "features": {
                "price": price,
                "vwap": vwap,
                "vwap_diff": round(vwap_diff, 2),
                "early_gain": early_gain,
                "fade_from_high": fade_from_high,
                "fade_from_low": fade_from_low,
                "volume": volume,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        print(f"🕳️ [q_trap] → {direction.upper()} trap | score={score:.2f} | ΔVWAP={vwap_diff:.2f}")
        return signal

    except Exception as e:
        logger.error({"agent": "q_trap", "event": "trap_signal_fail", "error": str(e)})
        return None
