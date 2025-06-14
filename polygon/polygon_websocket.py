# ── polygon/polygon_websocket.py ───────────────────────────────────────────
from __future__ import annotations

import asyncio, json, os, time
from typing import Final

import websockets
from dotenv import load_dotenv
from core.logger_setup import get_logger

load_dotenv()
logger = get_logger(__name__)

POLYGON_API_KEY: Final[str] = os.getenv("POLYGON_API_KEY", "")
POLYGON_WS_URL : Final[str] = "wss://socket.polygon.io/stocks"

# the only two keys other modules ever read ↓
SPY_LIVE_PRICE: dict[str, float | None] = {
    "mid":        None,   # bid/ask midpoint
    "last_trade": None,   # last trade price
    "timestamp":  None,   # epoch ns
}

# ---------------------------------------------------------------------------#
# WebSocket driver                                                           #
# ---------------------------------------------------------------------------#
async def _listen_forever() -> None:
    uri = POLYGON_WS_URL
    while True:
        try:
            async with websockets.connect(uri) as ws:
                logger.info({"event": "ws_connected"})
                await ws.send(json.dumps({"action": "auth", "params": POLYGON_API_KEY}))
                await ws.send(json.dumps({"action": "subscribe",
                                          "params": "Q.SPY,T.SPY"}))

                while True:
                    for event in json.loads(await ws.recv()):
                        ev = event.get("ev")
                        ts = event.get("t")

                        if ev == "Q":             # quote
                            bid, ask = event.get("bp"), event.get("ap")
                            if bid and ask:
                                SPY_LIVE_PRICE.update({
                                    "mid":       (bid + ask) / 2,
                                    "timestamp": ts,
                                })

                        elif ev == "T":           # trade
                            price = event.get("p")
                            if price:
                                SPY_LIVE_PRICE.update({
                                    "last_trade": price,
                                    "timestamp" : ts,
                                })
        except Exception as e:                    # network hiccup → retry
            logger.warning({"event": "ws_error", "err": str(e)})
            await asyncio.sleep(5)

# ---------------------------------------------------------------------------#
# Bootstrap helper – **call this once** at start-up                          #
# ---------------------------------------------------------------------------#
def start_polygon_listener() -> None:
    """
    Fire-and-forget bootstrap.  Example::

        from polygon.polygon_websocket import start_polygon_listener
        start_polygon_listener()
    """
    loop = asyncio.get_running_loop()
    loop.create_task(_listen_forever())
    logger.info({"event": "ws_task_spawned"})

# CLI quick-test ------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(_listen_forever())
