# File: core/live_price_tracker.py

import time
from polygon.polygon_websocket import SPY_LIVE_PRICE
from brokers.tradier_client import get_quote

def get_current_spy_price():
    """
    Get the best available SPY price:
    - Try live WebSocket price first
    - Fallback to Tradier REST quote if live unavailable
    """
    live_price = SPY_LIVE_PRICE.get("price")
    live_timestamp = SPY_LIVE_PRICE.get("timestamp")

    if live_price and live_timestamp:
        return live_price

    # Fallback: Tradier REST call
    quote = get_quote("SPY")
    if quote and "quotes" in quote:
        return quote["quotes"]["quote"]["last"]

    return None

if __name__ == "__main__":
    while True:
        price = get_current_spy_price()
        print(f"[Live Price Tracker] SPY Current Price: {price}")
        time.sleep(1)
