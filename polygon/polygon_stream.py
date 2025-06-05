# File: polygon/options_stream.py

import os
import asyncio
import websockets
import json
from datetime import datetime
from dotenv import load_dotenv
from polygon.polygon_rest import get_option_symbols_for_today
from core.entry_learner import score_entry
from core.position_manager import evaluate_exit

load_dotenv()

POLYGON_KEY = os.getenv("POLYGON_API_KEY")
WS_URL = "wss://socket.polygon.io/options"
LOG_PATH = "logs/options_stream.jsonl"

async def on_option_quote(data):
    print("📈 Option Tick:", data)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to log option quote: {e}")

    # Pipe into entry/exit logic if needed
    context = {
        "symbol": data.get("sym"),
        "bid": data.get("bp"),
        "ask": data.get("ap"),
        "bid_size": data.get("bs"),
        "ask_size": data.get("as"),
        "timestamp": data.get("t")
    }

    try:
        score, rationale = score_entry(context)
        print(f"🧠 Entry Score: {score:.2f} | {rationale}")
    except Exception as e:
        print(f"⚠️ Entry logic error: {e}")

    try:
        exit_decision, reason = evaluate_exit(context, context)
        print(f"🚪 Exit Decision: {exit_decision} | {reason}")
    except Exception as e:
        print(f"⚠️ Exit logic error: {e}")


async def stream_option_quotes():
    try:
        option_tickers = get_option_symbols_for_today(limit=5)
        if not option_tickers:
            print("⚠️ No active SPY options returned. Exiting.")
            return

        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({"action": "auth", "params": POLYGON_KEY}))
            await ws.send(json.dumps({"action": "subscribe", "params": ",".join(option_tickers)}))
            print(f"📡 Subscribed to {option_tickers} via Polygon Options WebSocket.")

            while True:
                msg = await ws.recv()
                quotes = json.loads(msg)
                for quote in quotes:
                    if quote.get("ev") == "Q":
                        await on_option_quote(quote)
    except Exception as e:
        print(f"🔌 Reconnecting in 5s due to error: {e}")
        await asyncio.sleep(5)
        await stream_option_quotes()


if __name__ == "__main__":
    asyncio.run(stream_option_quotes())
