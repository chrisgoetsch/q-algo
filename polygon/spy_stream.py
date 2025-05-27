# File: polygon/spy_stream.py

import asyncio
import json
import os
import websockets
from datetime import datetime

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
WS_URL = "wss://socket.polygon.io/stocks"
SPY_SYMBOL = "T.SPY"

LOG_PATH = "logs/spy_stream.jsonl"

async def on_spy_tick(data):
    """Optional callback to react to price updates."""
    print(f"🟢 SPY Tick: {data}")
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"timestamp": datetime.utcnow().isoformat(), "data": data}) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to log tick: {e}")


async def stream_spy(callback=on_spy_tick):
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
        await ws.send(json.dumps({"action": "subscribe", "params": SPY_SYMBOL}))

        print(f"🔌 Subscribed to {SPY_SYMBOL} via Polygon WebSocket.")

        while True:
            try:
                message = await ws.recv()
                ticks = json.loads(message)
                for tick in ticks:
                    await callback(tick)
            except Exception as e:
                print(f"⚠️ WebSocket error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)
                return await stream_spy(callback)  # Reconnect on failure


if __name__ == "__main__":
    asyncio.run(stream_spy())
