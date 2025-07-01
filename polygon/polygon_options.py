# File: polygon/polygon_options.py
# Live SPY option chain fetch + GEX model builder

import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from polygon.polygon_rest import get_today_expiry
from core.logger_setup import logger

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"


def get_option_chain(symbol="SPY", expiry=None):
    if not expiry:
        expiry = get_today_expiry()

    url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={POLYGON_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        chain = data.get("results", [])
        return [opt for opt in chain if opt.get("details", {}).get("expiration_date", "").replace("-", "") == expiry]
    except Exception as e:
        logger.error({"event": "polygon_chain_fetch_error", "error": str(e)})
        return []


def filter_atm_options(option_chain, strike):
    return [
        opt for opt in option_chain
        if abs(opt.get("details", {}).get("strike_price", 0) - strike) <= 5
    ]


def get_option_chain_gex(symbol="SPY", spot=None):
    """
    Returns GEX snapshot from live chain for SPY.
    Output:
    {
        "gex_map": {580: -300000, 585: -240000, ...},
        "dealer_bias": "short_gamma",
        "gamma_flip_zone": 588.0
    }
    """
    try:
        expiry = get_today_expiry()
        chain = get_option_chain(symbol, expiry)
        if not chain:
            return None

        gex_map = {}
        call_gex = 0
        put_gex = 0

        for opt in chain:
            strike = int(opt.get("details", {}).get("strike_price", 0))
            delta = opt.get("greeks", {}).get("delta")
            gamma = opt.get("greeks", {}).get("gamma")
            oi = opt.get("open_interest", 0)
            opt_type = opt.get("details", {}).get("contract_type")

            if delta is None or gamma is None or oi == 0:
                continue

            # Simplified gamma notional
            notional_gamma = gamma * oi * 100

            gex_map[strike] = gex_map.get(strike, 0) + notional_gamma

            if opt_type == "call":
                call_gex += notional_gamma
            else:
                put_gex += notional_gamma

        dealer_bias = "short_gamma" if call_gex < 0 and put_gex < 0 else "long_gamma"

        # Flip zone = strike where GEX flips sign
        flip_zone = None
        sorted_strikes = sorted(gex_map.keys())
        for i in range(1, len(sorted_strikes)):
            a, b = sorted_strikes[i - 1], sorted_strikes[i]
            if gex_map[a] * gex_map[b] < 0:
                flip_zone = (a + b) / 2
                break

        return {
            "gex_map": gex_map,
            "dealer_bias": dealer_bias,
            "gamma_flip_zone": flip_zone
        }

    except Exception as e:
        logger.error({"event": "gex_build_fail", "error": str(e)})
        return None
