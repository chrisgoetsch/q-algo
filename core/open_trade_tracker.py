import os
import json
from datetime import datetime
from typing import Dict

from core.tradier_client import get_positions

OPEN_TRADES_PATH = "logs/open_trades.jsonl"


def sync_open_trades_with_tradier():
    """
    Pull live open positions from Tradier and sync to local open_trades.jsonl,
    tagging each trade with timestamp and minimal context.
    """
    raw = get_positions()
    if not isinstance(raw, dict):
        print("🛑 'positions' field not a dict: null or invalid response.")
        return

    positions = raw.get("positions", [])
    if not positions:
        print("🟡 No open positions found or empty response.")
        return

    clean_positions = []
    for pos in positions:
        if isinstance(pos, dict) and pos.get("symbol", "").startswith("SPY") and pos.get("quantity", 0) > 0:
            print(f"📥 Syncing open trade: {pos['symbol']} x{pos['quantity']}")
            clean_positions.append({
                "symbol": pos["symbol"],
                "quantity": pos["quantity"],
                "entry_time": datetime.utcnow().isoformat(),
                "mesh_score": 50,
                "trade_id": f"{pos['symbol']}_{datetime.utcnow().isoformat()}"
            })
        else:
            print(f"⚠️ Skipped malformed or irrelevant position: {pos}")

    os.makedirs(os.path.dirname(OPEN_TRADES_PATH), exist_ok=True)
    with open(OPEN_TRADES_PATH, "w") as f:
        for trade in clean_positions:
            f.write(json.dumps(trade) + "\n")

    print(f"🔄 Synced {len(clean_positions)} live trades from Tradier → open_trades.jsonl")


def atomic_write_line(filepath, line_data):
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(line_data) + "\n")
    except Exception as e:
        print(f"❌ Failed to write open trade log: {e}")


def log_open_trade(trade_id, agent, direction, strike, expiry, meta=None):
    entry = {
        "trade_id": trade_id,
        "agent": agent,
        "direction": direction,
        "strike": strike,
        "expiry": expiry,
        "timestamp": datetime.utcnow().isoformat(),
        "meta": meta or {}
    }
    atomic_write_line(OPEN_TRADES_PATH, entry)


def track_open_trade(trade: Dict):
    if trade.get("status") != "ok":
        print(f"⚠️ Not tracking trade due to failed order: {trade}")
        return

    record = {
        "trade_id": f"{trade['option_symbol']}_{datetime.utcnow().isoformat()}",
        "option_symbol": trade["option_symbol"],
        "timestamp": datetime.utcnow().isoformat(),
        "meta": {
            "order_id": trade.get("order_id"),
            "contracts": 1
        }
    }

    try:
        with open(OPEN_TRADES_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")
        print(f"📈 Trade logged: {record['trade_id']}")
    except Exception as e:
        print(f"🛑 Failed to log trade: {e}")


def is_expired(option_symbol: str) -> bool:
    try:
        expiry_str = option_symbol[3:9]
        expiry_date = datetime.strptime(expiry_str, "%y%m%d").date()
        return expiry_date < datetime.utcnow().date()
    except Exception as e:
        print(f"⚠️ Failed to parse expiry from {option_symbol}: {e}")
        return True


def load_open_trades(path=OPEN_TRADES_PATH):
    if not os.path.exists(path):
        print(f"⚠️ {path} not found. Returning empty trade list.")
        return []

    valid_trades = []
    with open(path, "r") as f:
        for line in f:
            try:
                trade = json.loads(line)
                symbol = trade.get("symbol", trade.get("trade_id", ""))
                if is_expired(symbol):
                    print(f"🪦 Skipping expired option: {symbol}")
                    continue
                valid_trades.append(trade)
            except Exception as e:
                print(f"⚠️ Skipping malformed trade line: {e}")

    return valid_trades


def remove_trade(trade_id):
    trades = load_open_trades()
    updated = [t for t in trades if t.get("trade_id") != trade_id]
    try:
        with open(OPEN_TRADES_PATH, "w") as f:
            for t in updated:
                f.write(json.dumps(t) + "\n")
        print(f"🧹 Removed trade: {trade_id}")
    except Exception as e:
        print(f"⚠️ Failed to rewrite {OPEN_TRADES_PATH}: {e}")
