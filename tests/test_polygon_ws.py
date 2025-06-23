# File: tests/test_polygon_ws.py

import asyncio
import json
import os
import websockets
from dotenv import load_dotenv

load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Replace this with whatever your Q-ALGO is producing
RAW_SYMBOL = "SPY250620C00595000"  # simulate output from option_selector

async def test_polygon_ws():
    # Patch missing prefix
    symbol = RAW_SYMBOL
    if not symbol.startswith("O:"):
        print(f"⚠️  Prefix missing. Patching with O: → {symbol}")
        symbol = f"O:{symbol}"

    print(f"✅ Using subscription symbol: {symbol}")

    try:
        async with websockets.connect("wss://socket.polygon.io/options") as ws:
            await ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
            auth_resp = await ws.recv()
            print("🔐 Auth response:", auth_resp)

            await ws.send(json.dumps({"action": "subscribe", "params": symbol}))
            print(f"📡 Sent subscription for {symbol}")

            try:
                while True:
                    msg = await ws.recv()
                    print("📨 Received:", msg)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"❌ WebSocket closed unexpectedly: {e.code} → {e.reason}")
    except Exception as e:
        print(f"🚫 WebSocket connection failed: {e}")

asyncio.run(test_polygon_ws())
