# polygon_stream.py
# Streams live SPY trades via Polygon.io WebSocket

import os
import asyncio
import websockets
import json
from dotenv import load_dotenv

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
WS_URL = "wss://socket.polygon.io/stocks"

async def stream_spy_trades():
    async with websockets.connect(WS_URL) as websocket:
        # Authenticate
        await websocket.send(json.dumps({"action": "auth", "params": 
POLYGON_KEY}))
        print("🔐 WebSocket authenticated.")

        # Subscribe to SPY trades
        await websocket.send(json.dumps({"action": "subscribe", "params": 
"T.SPY"}))
        print("📡 Subscribed to SPY trade stream.")

        # Listen
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print("📈 SPY Tick:", data)

if __name__ == "__main__":
    asyncio.run(stream_spy_trades())

