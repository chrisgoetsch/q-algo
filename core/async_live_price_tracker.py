# File: core/async_live_price_tracker.py

from polygon.async_polygon_websocket import SPY_LIVE_PRICE
from core.tradier_client import get_quote

def get_current_spy_price():
    """
    Return the best current SPY price.
    Prioritize WebSocket live price; fallback to Tradier REST quote if needed.
    """
    live_price = SPY_LIVE_PRICE.get("price")
    live_timestamp = SPY_LIVE_PRICE.get("timestamp")

    if live_price and live_timestamp:
        return live_price

    # REST fallback
    quote = get_quote("SPY")
    if quote and "quotes" in quote:
        return quote["quotes"]["quote"]["last"]

    return None
