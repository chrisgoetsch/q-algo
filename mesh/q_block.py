# File: mesh/q_block.py
# SPY 0DTE Order Block Signal Agent (Q-Block v2 with Polygon Order Block Feed)

import datetime
from typing import Optional
from polygon.polygon_utils import round_to_nearest_strike, get_open_interest_by_strike
from polygon.polygon_rest import get_last_price
from core.logger_setup import logger

OI_THRESHOLD = 10000

def detect_order_block_signal() -> Optional[dict]:
    try:
        price = get_last_price("SPY")
        if not price:
            return None

        strike = round_to_nearest_strike(price)
        oi_map = get_open_interest_by_strike("SPY")

        if str(strike) not in oi_map:
            return None

        zone = oi_map[str(strike)]
        call_oi = zone.get("call_oi", 0)
        put_oi = zone.get("put_oi", 0)

        if max(call_oi, put_oi) < OI_THRESHOLD:
            return None

        total_oi = call_oi + put_oi
        oi_ratio = (call_oi - put_oi) / max(total_oi, 1)
        bias = "call" if oi_ratio > 0 else "put"
        score = round(abs(oi_ratio), 4)

        return {
            "agent": "q_block",
            "score": score,
            "direction": bias,
            "confidence": round(score * 100),
            "features": {
                "strike": strike,
                "price": price,
                "call_oi": call_oi,
                "put_oi": put_oi,
                "oi_ratio": round(oi_ratio, 4)
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error({"agent": "q_block", "event": "order_block_fail", "error": str(e)})
        return None


# Entry point for mesh_router
get_block_signal = detect_order_block_signal
