# File: mesh/q_gamma.py — Updated for full real-time GEX/DEX logic

import os
import json
from datetime import datetime
from polygon.polygon_utils import (
    get_realtime_price, round_to_nearest_strike
)
from polygon.polygon_options import get_option_chain_gex
from core.logger_setup import logger

SNAPSHOT_PATH = "data/gex_ml_snapshots/latest_gex.json"
HISTORICAL_PATH = f"data/gex_ml_snapshots/gex_{datetime.utcnow().date()}.json"

def write_gex_snapshot():
    try:
        price = get_realtime_price("SPY")
        if not price:
            raise ValueError("Missing SPY price")

        data = get_option_chain_gex("SPY", price)
        if not data or "gex_map" not in data:
            raise ValueError("Malformed GEX data")

        gex_map = data["gex_map"]
        dealer_bias = data.get("dealer_bias", "neutral")
        flip_zone = data.get("gamma_flip_zone")

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "spy_price": price,
            "gex_map": gex_map,
            "dealer_bias": dealer_bias,
            "gamma_flip_zone": flip_zone,
            "max_gex_strike": max(gex_map, key=gex_map.get, default=None),
            "min_gex_strike": min(gex_map, key=gex_map.get, default=None),
        }

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w") as f:
            json.dump(snapshot, f, indent=2)
        with open(HISTORICAL_PATH, "w") as f:
            json.dump(snapshot, f, indent=2)

        print(f"✅ GEX snapshot saved to {SNAPSHOT_PATH}")
        return snapshot
    except Exception as e:
        logger.error({"agent": "q_gamma", "event": "snapshot_fail", "error": str(e)})
        return None

def load_latest_gex_snapshot():
    try:
        with open(SNAPSHOT_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning({"agent": "q_gamma", "event": "load_fail", "error": str(e)})
        return None

def get_gamma_signal(force_refresh=False) -> dict | None:
    try:
        snapshot = write_gex_snapshot() if force_refresh else load_latest_gex_snapshot()
        if not snapshot:
            return None

        price = get_realtime_price("SPY")
        flip_zone = snapshot.get("gamma_flip_zone")
        dealer_bias = snapshot.get("dealer_bias", "neutral")
        gex_map = snapshot.get("gex_map", {})

        if not price or not flip_zone or not gex_map:
            return None

        flip_distance = abs(price - flip_zone)
        gamma_pressure_score = max(0, 1 - (flip_distance / 12))
        dealer_score = 0.6 if dealer_bias == "short_gamma" else 0.3 if dealer_bias == "long_gamma" else 0.2
        composite = round((gamma_pressure_score + dealer_score) / 2, 4)

        direction = "put" if price < flip_zone else "call"

        if composite < 0.4:
            return None

        result = {
            "agent": "q_gamma",
            "score": composite,
            "confidence": round(composite * 100),
            "direction": direction,
            "features": {
                "spy_price": price,
                "flip_zone": flip_zone,
                "dealer_bias": dealer_bias,
                "gamma_pressure": gamma_pressure_score
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        print(f"📊 [q_gamma] → {direction.upper()} score={composite:.2f} | bias={dealer_bias} | Δflip={flip_distance:.2f}")
        return result

    except Exception as e:
        logger.error({"agent": "q_gamma", "event": "signal_fail", "error": str(e)})
        return None
