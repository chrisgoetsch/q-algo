# File: polygon/stocks_websocket.py

import asyncio
import json
import os
import time
import websockets
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
WS_URL = "wss://socket.polygon.io/stocks"

SPY_LIVE_PRICE = {}

async def _spy_price_listener():
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
        print("✅ SPY price listener authenticated")

        await ws.send(json.dumps({"action": "subscribe", "params": "T.SPY"}))
        print("📡 Subscribed to T.SPY")

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                for item in data:
                    if item.get("ev") == "T" and item.get("sym") == "SPY":
                        SPY_LIVE_PRICE.update({
                            "price": item.get("p"),
                            "timestamp": time.time(),
                            "last_trade": item.get("p"),
                        })
            except Exception as e:
                print(f"❌ SPY price feed error: {e}")
                time.sleep(1)

def start_spy_price_listener():
    Thread(target=lambda: asyncio.run(_spy_price_listener()), daemon=True).start()
