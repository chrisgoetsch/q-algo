# polygon/polygon_rest.py
# Secure, retried Polygon.io REST client for price and options data

import os
from typing import Optional, Dict, Any

from core.env_validator import validate_env
from core.resilient_request import resilient_get
from core.logger_setup import logger

# Validate environment on import
validate_env()

API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = os.getenv("POLYGON_BASE_URL", "https://api.polygon.io")

def get_historical_prices(symbol: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Fetches minute-aggregation price data for `symbol` on `date`.
    Returns JSON dict on success or None on failure.
    """
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
    """
    Fetches the full option chain for `symbol`.
    Returns JSON dict on success or None on failure.
    """
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
    """
    Fetches the latest quote for `symbol`.
    Returns JSON dict on success or None on failure.
    """
    url = f"{BASE_URL}/v1/last_quote/stocks/{symbol}"
    params = {"apiKey": API_KEY}
    resp = resilient_get(url, params=params)
    if not resp:
        logger.warning({"event": "quote_fail", "symbol": symbol})
        return None
    try:
        return resp.json()
    except Exception as e:
        logger.error({"event": "quote_parse_error", "error": str(e)})
        return None

# Example of caching to disk (optional):
def cache_to_file(path: str, data: Dict[str, Any]) -> None:
    """
    Atomically writes JSON data to `path` for caching purposes.
    """
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
