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
            "params": "Q.SPY"
        }))

        print("[Polygon WS Async] Connected and subscribed to SPY quotes.")

        async for message in websocket:
            try:
                data = json.loads(message)

                for update in data:
                    if update.get("ev") == "Q":
                        ask = update.get("ap", 0)
                        bid = update.get("bp", 0)
                        mid = (ask + bid) / 2 if ask and bid else 0
                        timestamp = update.get("t", 0)

                        SPY_LIVE_PRICE["price"] = mid
                        SPY_LIVE_PRICE["timestamp"] = timestamp

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
