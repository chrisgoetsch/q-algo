# File: polygon/polygon_utils.py
# Helper tools for working with Polygon data formats and enabling real-time mesh agent access

import math
from datetime import datetime, timedelta
import requests
import os
import json
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"

# ---------------------------------------------------------------------------
# Strike and symbol helpers
# ---------------------------------------------------------------------------
def round_to_nearest_strike(price, interval=5):
    return int(round(price / interval) * interval)

def format_option_symbol(symbol, expiry, strike, call_put):
    return f"{symbol}{expiry}{strike:05d}{call_put.upper()}"

def normalize_chain(chain, side="call"):
    return [opt for opt in chain if opt.get("details", {}).get("contract_type") == side]

# ---------------------------------------------------------------------------
# Real-time price data
# ---------------------------------------------------------------------------
def get_realtime_price(symbol="SPY") -> float:
    url = f"{BASE_URL}/v2/last/trade/{symbol}?apiKey={POLYGON_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        return data.get("last", {}).get("price", 0.0)
    except Exception as e:
        print(f"⚠️ get_realtime_price failed: {e}")
        return 0.0

# ---------------------------------------------------------------------------
# Real-time aggregate bars (1-min)
# ---------------------------------------------------------------------------
def get_intraday_bars(symbol="SPY", timespan="minute", limit=5):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/1/{timespan}/{today}/{today}?apiKey={POLYGON_KEY}&limit={limit}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"⚠️ get_intraday_bars failed: {e}")
        return []

# ---------------------------------------------------------------------------
# VWAP Calculation
# ---------------------------------------------------------------------------
def get_vwap(symbol: str = "SPY") -> float:
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/1/minute/{today}/{today}?adjusted=true&sort=asc&apiKey={POLYGON_KEY}"
        r = requests.get(url)
        r.raise_for_status()
        candles = r.json().get("results", [])
        if not candles:
            return 0.0
        total_vol = sum(c["v"] for c in candles)
        if total_vol == 0:
            return 0.0
        vwap = sum(c["v"] * (c["h"] + c["l"] + c["c"]) / 3 for c in candles) / total_vol
        return round(vwap, 2)
    except Exception:
        return 0.0
    
def get_vwap_diff(symbol: str = "SPY") -> float:
    try:
        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={POLYGON_KEY}"
        r = requests.get(url).json()
        close = r["results"][0]["c"]
        vwap = r["results"][0]["vwap"]
        return round((close - vwap) / vwap, 4)
    except Exception as e:
        print(f"get_vwap_diff error: {e}")
        return 0.0


# ---------------------------------------------------------------------------
# Intraday returns (from open)
# ---------------------------------------------------------------------------
def get_intraday_returns(symbol="SPY", limit=20) -> dict:
    bars = get_intraday_bars(symbol=symbol, limit=limit)
    try:
        if not bars:
            return {}
        first = bars[0]["o"]
        last = bars[-1]["c"]
        high = max(bar["h"] for bar in bars)
        low = min(bar["l"] for bar in bars)
        return {
            "first_hour_return": round((last - first) / first * 100, 2),
            "high_to_current_return": round((last - high) / high * 100, 2),
            "low_to_current_return": round((last - low) / low * 100, 2),
        }
    except Exception as e:
        print(f"⚠️ get_intraday_returns failed: {e}")
        return {}

# ---------------------------------------------------------------------------
# Real-time Greeks for top-of-book option symbol
# ---------------------------------------------------------------------------
def get_option_greeks(symbol: str) -> dict:
    url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={POLYGON_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json().get("results", [])
        if not data:
            return {}
        details = data[0].get("greeks", {})
        return {
            "delta": details.get("delta"),
            "gamma": details.get("gamma"),
            "vega": details.get("vega"),
            "theta": details.get("theta")
        }
    except Exception as e:
        print(f"⚠️ get_option_greeks failed: {e}")
        return {}

# ---------------------------------------------------------------------------
# Real-time order book depth (best bid/ask sizes)
# ---------------------------------------------------------------------------
def get_order_book_depth(symbol="SPY") -> dict:
    url = f"{BASE_URL}/v3/quotes/{symbol}?apiKey={POLYGON_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json().get("results", [])
        if not data:
            return {}
        quote = data[0]
        return {
            "bid_size": quote.get("bid_size"),
            "ask_size": quote.get("ask_size"),
            "bid": quote.get("bid"),
            "ask": quote.get("ask"),
        }
    except Exception as e:
        print(f"⚠️ get_order_book_depth failed: {e}")
        return {}

# ---------------------------------------------------------------------------
# VIX level for volatility agents
# ---------------------------------------------------------------------------
def get_vix_index_price() -> float:
    return get_realtime_price("VIX")

# ---------------------------------------------------------------------------
# Real-time volume for SPY
# ---------------------------------------------------------------------------
def get_recent_volume(symbol="SPY", limit=5) -> int:
    bars = get_intraday_bars(symbol=symbol, limit=limit)
    try:
        return sum(bar.get("v", 0) for bar in bars)
    except Exception as e:
        print(f"⚠️ get_recent_volume failed: {e}")
        return 0

def get_gex_score(symbol: str = "SPY") -> float:
    try:
        path = "data/gex_ml_snapshots/latest_gex.json"
        with open(path, "r") as f:
            snap = json.load(f)
        return snap.get("gex_score", 0)
    except Exception as e:
        print(f"get_gex_score error: {e}")
        return 0.0
    
    # File: polygon/polygon_utils.py
# Purpose: Unified utilities for processing Polygon.io option data



def round_to_nearest_strike(price: float, interval: int = 5) -> int:
    return int(round(price / interval) * interval)

def format_option_symbol(symbol: str, expiry: str, strike: int, call_put: str) -> str:
    strike_formatted = f"{strike:05d}"
    return f"{symbol}{expiry}{strike_formatted}{call_put.upper()}"

def normalize_chain(chain: list, side: str = "call") -> list:
    return [opt for opt in chain if opt.get("details", {}).get("contract_type") == side]

def get_intraday_returns(symbol: str = "SPY") -> float:
    try:
        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={POLYGON_KEY}"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json().get("results", [])
        if not data:
            return 0.0
        prev_close = data[0].get("c", 0)
        curr_url = f"{BASE_URL}/v2/last/trade/{symbol}?apiKey={POLYGON_KEY}"
        r2 = requests.get(curr_url)
        r2.raise_for_status()
        last = r2.json().get("results", {}).get("p", 0)
        if not last or not prev_close:
            return 0.0
        return round((last - prev_close) / prev_close, 4)
    except Exception:
        return 0.0



def get_skew(symbol: str = "SPY") -> float:
    """
    Returns skew estimate based on IV between OTM puts and OTM calls.
    This is a placeholder and should ideally be replaced with real IV surface parsing.
    """
    try:
        url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={POLYGON_KEY}"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json().get("results", [])
        if not data:
            return 1.05  # fallback

        calls = [opt for opt in data if opt["details"]["contract_type"] == "call"]
        puts = [opt for opt in data if opt["details"]["contract_type"] == "put"]
        atm_call_iv = sum(opt["implied_volatility"] for opt in calls[:3]) / max(len(calls[:3]), 1)
        atm_put_iv = sum(opt["implied_volatility"] for opt in puts[:3]) / max(len(puts[:3]), 1)

        skew = round(atm_put_iv / atm_call_iv, 4) if atm_call_iv else 1.05
        return skew

    except Exception:
        return 1.05  # conservative fallback

def get_open_interest_by_strike(symbol: str = "SPY") -> dict:
    """
    Build a dictionary of strike → {call_oi, put_oi} from option snapshot.
    """
    try:
        url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={POLYGON_KEY}"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json().get("results", [])
        if not data:
            return {}

        oi_map = defaultdict(lambda: {"call_oi": 0, "put_oi": 0})
        for opt in data:
            strike = opt["details"].get("strike_price")
            side = opt["details"].get("contract_type")
            oi = opt.get("open_interest", 0)
            if side == "call":
                oi_map[str(strike)]["call_oi"] += oi
            elif side == "put":
                oi_map[str(strike)]["put_oi"] += oi
        return dict(oi_map)
    except Exception:
        return {}
