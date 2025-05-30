# devtools/close_all_open_trades.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from datetime import datetime
from core.tradier_execution import submit_order
from core.open_trade_tracker import load_open_trades

OPEN_TRADES_PATH = "logs/open_trades.jsonl"
ARCHIVE_PATH = f"logs/open_trades_closed_{datetime.utcnow().date()}.jsonl"

def close_all_open_trades():
    open_trades = load_open_trades()
    if not open_trades:
        print("✅ No open trades to close.")
        return

    print(f"🛑 Attempting to close {len(open_trades)} open trade(s)...")
    closed = []

    for trade in open_trades:
        symbol = trade.get("option_symbol")
        qty = trade.get("quantity", 1)
        direction = trade.get("direction", "long")

        if not symbol:
            print(f"⚠️ Skipping malformed trade: {trade}")
            continue

        try:
            action = "sell_to_close" if direction == "long" else "buy_to_close"
            response = submit_order(symbol, qty, action)

            if response:
                print(f"✅ Closed {symbol} x{qty} via {action}")
                trade["closed_at"] = datetime.utcnow().isoformat()
                closed.append(trade)
            else:
                print(f"❌ Failed to close {symbol}")

        except Exception as e:
            print(f"❌ Error closing {symbol}: {e}")

    # Archive successfully closed trades
    os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)
    with open(ARCHIVE_PATH, "w") as f:
        for t in closed:
            f.write(json.dumps(t) + "\n")

    # Clear live trade tracker
    open(OPEN_TRADES_PATH, "w").close()
    print(f"🧹 All open trades closed and archived → {ARCHIVE_PATH}")

if __name__ == "__main__":
    close_all_open_trades()
