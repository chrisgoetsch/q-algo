# File: polygon/polygon_websocket.py

import websocket
import threading
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
SPY_LIVE_PRICE = {
    "mid": None,
    "last_trade": None,
    "bid": None,
    "ask": None,
    "timestamp": None
}


def on_open(ws):
    print("[Polygon WS] Connection opened.")
    auth_data = {
        "action": "auth",
        "params": POLYGON_API_KEY
    }
    ws.send(json.dumps(auth_data))

    # ✅ Subscribe to both quote and trade events for SPY
    sub_data = {
        "action": "subscribe",
        "params": "Q.SPY,T.SPY"
    }
    ws.send(json.dumps(sub_data))
    print("[Polygon WS] Subscribed to: Q.SPY and T.SPY")

def on_message(ws, message):
    global SPY_LIVE_PRICE
    try:
        data = json.loads(message)
        for update in data:
            ev = update.get("ev")
            timestamp = update.get("t", 0)

            if ev == "Q":  # Equity quote
                ask = update.get("ap", 0)
                bid = update.get("bp", 0)
                if ask and bid:
                    mid = (ask + bid) / 2
                    SPY_LIVE_PRICE["price"] = mid
                    SPY_LIVE_PRICE["timestamp"] = timestamp
                    print(f"[Polygon WS] SPY Mid Price (Q): {mid:.2f}")

            elif ev == "T":  # Equity trade
                price = update.get("p", 0)
                if not SPY_LIVE_PRICE["price"]:  # fallback if no quote yet
                    SPY_LIVE_PRICE["price"] = price
                    SPY_LIVE_PRICE["timestamp"] = timestamp
                    print(f"[Polygon WS] SPY Last Trade Price (T): {price:.2f}")

    except Exception as e:
        print(f"[Polygon WS] Error parsing message: {e}")

def on_error(ws, error):
    print(f"[Polygon WS] Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[Polygon WS] Connection closed: {close_status_code} - {close_msg}")

def start_polygon_websocket():
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://socket.polygon.io/stocks",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    print("[Polygon WS] WebSocket thread started.")
    time.sleep(2)

if __name__ == "__main__":
    start_polygon_websocket()
    while True:
        time.sleep(1)
