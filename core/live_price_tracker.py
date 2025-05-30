# core/live_price_tracker.py

from polygon.polygon_websocket import SPY_LIVE_PRICE

def get_current_spy_price():
    """
    Returns the most accurate live SPY price available:
    - Prefers mid (bid/ask midpoint)
    - Falls back to last trade
    - Defaults to 0.0 if unavailable
    """
    price = SPY_LIVE_PRICE.get("mid")
    if price:
        return price

    fallback = SPY_LIVE_PRICE.get("last_trade")
    if fallback:
        return fallback

    return 0.0
