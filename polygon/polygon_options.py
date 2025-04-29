# polygon_options.py
# Live SPY option chain pull and filter

import requests
import os
from dotenv import load_dotenv

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"

def get_option_chain(symbol="SPY", expiry=None):
    """
    Pulls the current option chain from Polygon.io
    """
    if not expiry:
        from polygon_rest import get_today_expiry
        expiry = get_today_expiry()

    url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={POLYGON_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        chain = data.get("results", [])
        return [opt for opt in chain if opt.get("details", 
{}).get("expiration_date", "").replace("-", "") == expiry]
    except Exception as e:
        print(f"[polygon_options] Failed to fetch chain: {e}")
        return []

def filter_atm_options(option_chain, strike):
    """
    Filters options near the ATM strike
    """
    return [
        opt for opt in option_chain
        if abs(opt.get("details", {}).get("strike_price", 0) - strike) <= 5
    ]

