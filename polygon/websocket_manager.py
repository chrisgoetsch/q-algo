# File: polygon/websocket_manager.py

import os
import json
import asyncio
import websockets
import time
from core.tradier_client import get_quote
from core.logger_setup import logger

API_KEY = os.getenv("POLYGON_API_KEY")
POLYGON_WS_URL = "wss://socket.polygon.io/options"


# Shared memory store for live prices
LIVE_PRICES = {}
TIMESTAMPS = {}

# Time in seconds to consider price stale
STALE_THRESHOLD = 10

async def start_polygon_listener(symbols=["SPY"]):
    """
    Starts a persistent Polygon WebSocket connection to stream tick prices
    for the given list of symbols. Updates LIVE_PRICES in memory.
    """
    uri = f"{POLYGON_WS_URL}"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("🧠 Connecting to Polygon WebSocket...")
                await websocket.send(json.dumps({"action": "auth", "params": API_KEY}))

                # Subscribe to each symbol’s tick stream
                channels = ",".join([f"T.{sym}" for sym in symbols])
                await websocket.send(json.dumps({"action": "subscribe", "params": channels}))
                logger.info(f"📡 Subscribed to ticks: {symbols}")

                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    for event in data:
                        if event.get("ev") == "T":  # Tick data
                            symbol = event.get("sym")
                            price = event.get("p")
                            ts = time.time()

                            LIVE_PRICES[symbol] = price
                            TIMESTAMPS[symbol] = ts

        except Exception as e:
            logger.warning(f"⚠️ WebSocket error: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

def get_price(symbol: str) -> float:
    """
    Returns the latest price for a symbol.
    If WebSocket data is stale or missing, falls back to Tradier REST quote.
    """
    now = time.time()
    price = LIVE_PRICES.get(symbol)
    ts = TIMESTAMPS.get(symbol, 0)

    if price is not None and (now - ts) < STALE_THRESHOLD:
        return price

    # Fallback: REST quote from Tradier
    logger.warning(f"⚠️ Price stale or missing for {symbol}. Using Tradier fallback.")
    try:
        quote = get_quote(symbol)
        return quote["quotes"]["quote"]["last"]
    except Exception as e:
        logger.error(f"🛑 Fallback quote failed for {symbol}: {e}")
        return 0.0
