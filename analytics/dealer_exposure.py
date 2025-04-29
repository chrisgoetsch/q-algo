# dealer_exposure.py
# Models Gamma Exposure (GEX) and Dealer Positioning

import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"

def fetch_option_greeks(symbol="SPY", expiry=None):
    url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={POLYGON_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json().get("results", [])
        return data
    except Exception as e:
        print(f"[dealer_exposure] Error fetching Greeks: {e}")
        return []

def calculate_gex(option_data):
    """
    Sums gamma exposure by strike, direction, and open interest
    """
    gex_by_strike = {}
    for opt in option_data:
        try:
            strike = opt["details"]["strike_price"]
            gamma = opt["greeks"]["gamma"]
            oi = opt["open_interest"]
            gex = gamma * oi
            gex_by_strike[strike] = gex_by_strike.get(strike, 0) + gex
        except Exception:
            continue
    return gex_by_strike

def detect_gex_flip(gex_map):
    """
    Identifies strike where gamma flips from positive to negative
    """
    sorted_strikes = sorted(gex_map.items())
    for i in range(1, len(sorted_strikes)):
        prev = sorted_strikes[i - 1][1]
        curr = sorted_strikes[i][1]
        if prev * curr < 0:
            return sorted_strikes[i][0]
    return None

