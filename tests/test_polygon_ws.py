# File: tests/test_polygon_ws.py

import asyncio
import json
import os
import websockets
from dotenv import load_dotenv
from core.tradier_execution import get_atm_option_symbol

load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

async def test_polygon_ws():
    # Get best option from live selector
    opt = get_atm_option_symbol("SPY", side="call", verbose=True)
    if not opt or not opt.get("symbol"):
        print("❌ No valid option returned.")
        return

    raw_symbol = opt["symbol"]
    if not raw_symbol.startswith("O:"):
        print(f"⚠️ Prefix missing. Patching → {raw_symbol}")
        raw_symbol = f"O:{raw_symbol}"

    print(f"✅ Subscribing to: {repr(raw_symbol)}")

    try:
        async with websockets.connect("wss://socket.polygon.io/options") as ws:
            await ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
            auth_resp = await ws.recv()
            print("🔐 Auth response:", auth_resp)

            await ws.send(json.dumps({"action": "subscribe", "params": raw_symbol}))
            print(f"📡 Sent subscription for: {repr(raw_symbol)}")

            try:
                while True:
                    msg = await ws.recv()
                    print("📨 Received:", msg)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"❌ WebSocket closed unexpectedly: {e.code} → {e.reason}")
    except Exception as e:
        print(f"🚫 WebSocket connection failed: {e}")

asyncio.run(test_polygon_ws())
