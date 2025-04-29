# q_block.py
# Q-ALGO v2 - Detects order block zones using open interest heatmap

import json
import datetime
from polygon.polygon_utils import round_to_nearest_strike
from polygon.polygon_rest import get_last_price

def load_heatmap():
    try:
        with open("data/open_interest_heatmap.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load heatmap: {e}")
        return {}

def get_block_signal():
    try:
        price = get_last_price()
        if not price:
            return None

        strike = round_to_nearest_strike(price)
        heatmap = load_heatmap()

        strike_str = str(strike)
        if strike_str not in heatmap:
            print(f"⚠️ No heatmap data for strike {strike}")
            return None

        data = heatmap[strike_str]
        call_oi = data.get("call", 0)
        put_oi = data.get("put", 0)
        max_oi = max(call_oi, put_oi)

        if max_oi < 10000:
            print(f"🟡 Not enough OI at strike {strike}")
            return None

        direction = "call" if put_oi > call_oi else "put"

        return {
            "agent": "q_block",
            "confidence": 0.85,
            "direction": direction,
            "score": 0.83,
            "zone": strike,
            "features": {
                "strike": strike,
                "call_oi": call_oi,
                "put_oi": put_oi
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ q_block error: {e}")
        return None

