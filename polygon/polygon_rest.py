# File: polygon/polygon_rest.py
# Secure, retried Polygon.io REST client for price and options data (options-only safe)

import os
from typing import Optional, Dict, Any
import requests
from datetime import date

from core.env_validator import validate_env
from core.resilient_request import resilient_get
from core.logger_setup import logger

# Validate environment on import
validate_env()

API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = os.getenv("POLYGON_BASE_URL", "https://api.polygon.io")

def get_option_symbols_for_today(limit=10):
    url = f"https://api.polygon.io/v3/snapshot/options/SPY?apiKey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("results", {}).get("data", [])

        active = sorted(data, key=lambda x: x.get("last_quote", {}).get("bid", 0), reverse=True)
        return [f"Q.{x['details']['ticker']}" for x in active[:limit]]
    except Exception as e:
        print(f"⚠️ Failed to get option tickers: {e}")
        return []

def get_historical_prices(symbol: str, date: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/1/minute/{date}/{date}"
    params = {"adjusted": "true", "sort": "asc", "apiKey": API_KEY}
    resp = resilient_get(url, params=params)
    if not resp:
        logger.warning({"event": "hist_prices_fail", "symbol": symbol, "date": date})
        return None
    try:
        return resp.json()
    except Exception as e:
        logger.error({"event": "hist_prices_parse_error", "error": str(e)})
        return None

def get_option_chain(symbol: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/v3/reference/options/symbols/{symbol}"
    params = {"apiKey": API_KEY}
    resp = resilient_get(url, params=params)
    if not resp:
        logger.warning({"event": "option_chain_fail", "symbol": symbol})
        return None
    try:
        return resp.json()
    except Exception as e:
        logger.error({"event": "option_chain_parse_error", "error": str(e)})
        return None

def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    logger.warning({"event": "quote_access_blocked", "symbol": symbol})
    return None

def cache_to_file(path: str, data: Dict[str, Any]) -> None:
    import json
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
        logger.info({"event": "cache_saved", "path": path})
    except Exception as e:
        logger.error({"event": "cache_save_failed", "error": str(e), "path": path})

def get_underlying_from_option_snapshot(symbol: str = "SPY") -> Optional[float]:
    url = f"{BASE_URL}/v3/snapshot/options/{symbol}?apiKey={API_KEY}"
    resp = resilient_get(url)

    if not resp or resp.status_code != 200:
        logger.warning({
            "event": "options_snapshot_fail",
            "symbol": symbol,
            "status": resp.status_code if resp else "None"
        })
        return None

    try:
        data = resp.json()
        results = data.get("results", [])
        if not results:
            logger.warning({"event": "empty_results", "symbol": symbol})
            return None

        underlying = results[0].get("underlying_asset", {})
        price = underlying.get("price")
        if price is None:
            logger.warning({"event": "missing_underlying_price", "data": underlying})
        return price

    except Exception as e:
        logger.error({"event": "snapshot_parse_fail", "error": str(e)})
        return None

def get_live_price(symbol: str) -> Optional[float]:
    return get_underlying_from_option_snapshot(symbol)

def get_option_metrics(symbol: str) -> Dict[str, float]:
    try:
        return {
            "iv": 0.35,
            "volume": 100000,
            "skew": 0.1,
            "delta": 0.5,
            "gamma": 0.2
        }
    except Exception as e:
        logger.error({"event": "option_metrics_error", "symbol": symbol, "error": str(e)})
        return {}

def get_dealer_flow_metrics(symbol: str) -> Dict[str, float]:
    try:
        return {"score": 0.25}
    except Exception as e:
        logger.error({"event": "dealer_flow_error", "symbol": symbol, "error": str(e)})
        return {"score": 0}