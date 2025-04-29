# File: polygon/polygon_websocket.py

import websocket
import threading
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
SPY_LIVE_PRICE = {"price": None, "timestamp": None}

def on_open(ws):
    print("[Polygon WS] Connection opened.")
    auth_data = {
        "action": "auth",
        "params": POLYGON_API_KEY
    }
    ws.send(json.dumps(auth_data))

    # Subscribe to SPY quote updates (NBBO best bid/offer updates)
    sub_data = {
        "action": "subscribe",
        "params": "Q.SPY"
    }
    ws.send(json.dumps(sub_data))

def on_message(ws, message):
    global SPY_LIVE_PRICE
    try:
        data = json.loads(message)

        for update in data:
            if update.get("ev") == "Q":  # Quote event
                ask_price = update.get("ap", 0)
                bid_price = update.get("bp", 0)
                mid_price = (ask_price + bid_price) / 2 if ask_price and bid_price else 0
                timestamp = update.get("t", 0)

                SPY_LIVE_PRICE["price"] = mid_price
                SPY_LIVE_PRICE["timestamp"] = timestamp

                print(f"[Polygon WS] SPY Live Mid Price: {mid_price:.2f}")

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

    # Allow the feed to initialize
    time.sleep(2)

if __name__ == "__main__":
    start_polygon_websocket()
    while True:
        time.sleep(1)
