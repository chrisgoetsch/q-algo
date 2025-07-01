# File: polygon/polygon_websocket.py

import asyncio
import json
import os
import time
import websockets
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
WS_URL = "wss://socket.polygon.io/options"

SPY_LIVE_PRICE = {}
OPTION_TICK_DATA = {}

_ws_conn = None
_subscribed_symbols = set()
auth_ready = asyncio.Event()

async def _listener():
    global _ws_conn
    async with websockets.connect(WS_URL) as websocket:
        _ws_conn = websocket
        await websocket.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
        
        while True:
            msg = await websocket.recv()
            parsed = json.loads(msg)
            if isinstance(parsed, list) and parsed and parsed[0].get("status") == "auth_success":
                print("[websocket] authenticated")
                auth_ready.set()  # ← SET AUTH FLAG HERE
                break

        print("[websocket] ready for symbol subscriptions")

        while True:
            try:
                msg = await websocket.recv()
                parsed = json.loads(msg)
                _update_option_ticks(parsed)
            except Exception as e:
                print(f"[websocket] error: {e}")
                await asyncio.sleep(2)
                auth_ready.clear()  # ← RESET ON RECONNECT
                break

def start_polygon_listener():
    Thread(target=lambda: asyncio.run(_listener()), daemon=True).start()


def _update_option_ticks(messages):
    for msg in messages:
        if msg.get("ev") == "T" and "sym" in msg:
            sym = msg["sym"]
            OPTION_TICK_DATA[sym] = {
                "price": msg.get("p"),
                "timestamp": time.time(),
            }
def subscribe_to_option_symbol(symbol: str):
    """Subscribe to O:<contract> format after auth_ready is set."""
    global _ws_conn
    if not symbol or symbol in _subscribed_symbols:
        print(f"⚠️ Skipping symbol (already subscribed or empty): {repr(symbol)}")
        return

    async def _subscribe():
        await auth_ready.wait()
        try:
            if not symbol.startswith("O:"):
                print(f"⚠️ Missing prefix → patching {repr(symbol)}")
                symbol = f"O:{symbol}"

            print(f"🧩 Subscribing to: {repr(symbol)}")
            msg = json.dumps({"action": "subscribe", "params": symbol})
            await _ws_conn.send(msg)
            _subscribed_symbols.add(symbol)
            print(f"[websocket] subscribed to {symbol}")
        except Exception as e:
            print(f"[websocket] failed to subscribe {symbol}: {e}")

    asyncio.run_coroutine_threadsafe(_subscribe(), asyncio.get_event_loop())


async def _subscribe():
    await auth_ready.wait()
    try:
        original = symbol
        if not symbol.startswith("O:"):
            print(f"⚠️ Missing prefix → patching {original}")
            symbol = f"O:{symbol}"

        print(f"🧩 Subscribing to: {repr(symbol)}")  # ← shows exact characters

        msg = json.dumps({"action": "subscribe", "params": symbol})
        await _ws_conn.send(msg)
        _subscribed_symbols.add(symbol)
        print(f"[websocket] subscribed to {symbol}")
    except Exception as e:
        print(f"[websocket] failed to subscribe {symbol}: {e}")


    asyncio.run_coroutine_threadsafe(_subscribe(), asyncio.get_event_loop())
