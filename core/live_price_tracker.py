# core/live_price_tracker.py

import asyncio
import websockets
import json
import os

API_KEY = os.getenv("POLYGON_API_KEY")
latest_price = {"SPY": 0.0}  # Shared memory

async def price_listener():
    uri = f"wss://socket.polygon.io/stocks"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"action": "auth", "params": API_KEY}))
        await websocket.send(json.dumps({"action": "subscribe", "params": "T.SPY"}))
        print("🔌 Connected to Polygon WebSocket for SPY")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                for event in data:
                    if event.get("ev") == "T" and event.get("sym") == "SPY":
                        latest_price["SPY"] = event["p"]
            except Exception as e:
                print(f"[WebSocket Error] {e}")
                await asyncio.sleep(5)

def get_current_spy_price():
    return latest_price.get("SPY", 0.0)
