# File: polygon/async_polygon_websocket.py

import asyncio
import json
import websockets
import os
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
SPY_LIVE_PRICE = {"price": None, "timestamp": None}

async def connect_polygon_ws():
    uri = "wss://socket.polygon.io/stocks"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "action": "auth",
            "params": POLYGON_API_KEY
        }))
        await websocket.send(json.dumps({
            "action": "subscribe",
            "params": "Q.SPY,T.SPY"
        }))

        print("[Polygon WS Async] Connected and subscribed to Q.SPY, T.SPY.")

        async for message in websocket:
            try:
                data = json.loads(message)

                for update in data:
                    ev = update.get("ev")
                    timestamp = update.get("t", 0)

                    if ev == "Q":  # Quote event
                        ask = update.get("ap", 0)
                        bid = update.get("bp", 0)
                        mid = (ask + bid) / 2 if ask and bid else 0
                        SPY_LIVE_PRICE["price"] = mid
                        SPY_LIVE_PRICE["timestamp"] = timestamp
                        print(f"[Quote] SPY Mid Price: {mid:.2f}")

                    elif ev == "T":  # Trade event
                        price = update.get("p", 0)
                        if not SPY_LIVE_PRICE["price"]:
                            SPY_LIVE_PRICE["price"] = price
                            SPY_LIVE_PRICE["timestamp"] = timestamp
                            print(f"[Trade Fallback] SPY Last Price: {price:.2f}")

            except Exception as e:
                print(f"[Polygon WS Async] Message parsing error: {e}")

async def start_polygon_websocket():
    while True:
        try:
            await connect_polygon_ws()
        except Exception as e:
            print(f"[Polygon WS Async] Connection error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(start_polygon_websocket())
