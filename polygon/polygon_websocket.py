# ─────────────────────────────────────────────────────────────────────────────
# File: polygon/polygon_websocket.py   (HF upgrade)
# ─────────────────────────────────────────────────────────────────────────────
"""Lightweight Polygon WebSocket listener that keeps a live SPY price cache."""

from __future__ import annotations
import json, os, threading, time
from typing import Final

import websocket
from dotenv import load_dotenv
from core.logger_setup import get_logger

load_dotenv()
logger = get_logger(__name__)

POLYGON_API_KEY: Final[str] = os.getenv("POLYGON_API_KEY", "")

SPY_LIVE_PRICE = {
    "mid":        None,   # bid/ask midpoint
    "last_trade": None,   # last trade price
    "bid":        None,
    "ask":        None,
    "timestamp":  None,   # epoch ms from Polygon
}

# ---------------------------------------------------------------------------#
# WebSocket callbacks                                                        #
# ---------------------------------------------------------------------------#
def _on_open(ws):
    logger.info({"event": "ws_open"})
    ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
    ws.send(json.dumps({"action": "subscribe", "params": "Q.SPY,T.SPY"}))
    logger.info({"event": "ws_subscribed", "channels": ["Q.SPY", "T.SPY"]})

def _on_message(ws, message: str):
    try:
        for update in json.loads(message):
            ev  = update.get("ev")
            ts  = update.get("t", 0)

            if ev == "Q":                         # quote update
                bid = update.get("bp") or 0
                ask = update.get("ap") or 0
                if bid and ask:
                    SPY_LIVE_PRICE.update({
                        "bid": bid,
                        "ask": ask,
                        "mid": (bid + ask) / 2,
                        "timestamp": ts,
                    })
                    logger.debug({"event": "ws_mid", "mid": SPY_LIVE_PRICE["mid"]})

            elif ev == "T":                       # trade update
                price = update.get("p") or 0
                if price:
                    SPY_LIVE_PRICE.update({
                        "last_trade": price,
                        "timestamp": ts,
                    })
                    logger.debug({"event": "ws_trade", "price": price})
    except Exception as e:
        logger.warning({"event": "ws_parse_fail", "err": str(e)})

def _on_error(_, error):
    logger.error({"event": "ws_error", "err": str(error)})

def _on_close(_, code, msg):
    logger.warning({"event": "ws_close", "code": code, "msg": msg})

# ---------------------------------------------------------------------------#
# Public entrypoint                                                          #
# ---------------------------------------------------------------------------#
def start_polygon_listener(channels=None):
    """Non-blocking; spawns a daemon thread."""
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://socket.polygon.io/stocks",
        on_open=_on_open,
        on_message=_on_message,
        on_error=_on_error,
        on_close=_on_close,
    )
    th = threading.Thread(target=ws.run_forever, daemon=True)
    th.start()
    logger.info({"event": "ws_thread_started"})
    # give the socket 1–2 s to auth+sub before the caller proceeds
    time.sleep(2)

if __name__ == "__main__":
    start_polygon_listener()
    while True:
        time.sleep(1)
