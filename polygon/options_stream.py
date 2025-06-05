# File: polygon/options_stream.py

import os
import asyncio
import websockets
import json
from datetime import datetime
from dotenv import load_dotenv
from polygon.polygon_rest import get_option_symbols_for_today

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
WS_URL = "wss://socket.polygon.io/options"
LOG_PATH = "logs/options_stream.jsonl"

REFRESH_INTERVAL = 300  # 5 minutes

def format_log(entry):
    return json.dumps({"timestamp": datetime.utcnow().isoformat(), "data": entry}) + "\n"

async def on_option_quote(data):
    print("📈 Option Tick:", data)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(format_log(data))
    except Exception as e:
        print(f"⚠️ Failed to log option quote: {e}")

async def stream_option_quotes():
    subscribed = set()
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"action": "auth", "params": POLYGON_KEY}))
        print("🔐 Authenticated with Polygon WebSocket")

        async def refresh_subscriptions():
            nonlocal subscribed
            while True:
                tickers = get_option_symbols_for_today(limit=5)
                new_set = set(tickers)
                if new_set != subscribed:
                    if subscribed:
                        await ws.send(json.dumps({"action": "unsubscribe", "params": ",".join(subscribed)}))
                        print(f"🛑 Unsubscribed: {subscribed}")
                    await ws.send(json.dumps({"action": "subscribe", "params": ",".join(new_set)}))
                    print(f"📡 Subscribed: {new_set}")
                    subscribed = new_set
                await asyncio.sleep(REFRESH_INTERVAL)

        async def listen():
            while True:
                try:
                    msg = await ws.recv()
                    for quote in json.loads(msg):
                        if quote.get("ev") == "Q":
                            await on_option_quote(quote)
                except Exception as e:
                    print(f"⚠️ WebSocket error: {e}. Reconnecting...")
                    break

        await asyncio.gather(refresh_subscriptions(), listen())

if __name__ == "__main__":
    asyncio.run(stream_option_quotes())
