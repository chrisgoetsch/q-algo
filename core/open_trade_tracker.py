import os
import json
from datetime import datetime
from core.tradier_client import get_positions

OPEN_TRADES_PATH = "logs/open_trades.jsonl"

def sync_open_trades_with_tradier():
    positions = get_positions()
    if not positions:
        print("🟡 No open positions found or invalid response.")
        return

    for pos in positions:
        if isinstance(pos, dict) and pos.get("symbol", "").startswith("SPY") and pos.get("quantity", 0) > 0:
            print(f"📥 Syncing open trade: {pos['symbol']} x{pos['quantity']}")
        else:
            print(f"⚠️ Skipped malformed or irrelevant position: {pos}")

    clean_positions = []
    for pos in positions:
        if isinstance(pos, dict) and pos.get("symbol", "").startswith("SPY") and pos.get("quantity", 0) > 0:
            print(f"📥 Syncing open trade: {pos['symbol']} x{pos['quantity']}")
            clean_positions.append({
                "symbol": pos["symbol"],
                "quantity": pos["quantity"],
                "entry_time": datetime.utcnow().isoformat(),
                "mesh_score": 50,  # Placeholder if needed
                "trade_id": f"{pos['symbol']}_{datetime.utcnow().isoformat()}"
            })

    # Write clean file
    os.makedirs(os.path.dirname(OPEN_TRADES_PATH), exist_ok=True)
    with open(OPEN_TRADES_PATH, "w") as f:
        for trade in clean_positions:
            f.write(json.dumps(trade) + "\n")

    print(f"🔄 Synced {len(clean_positions)} live trades from Tradier → open_trades.jsonl")


def atomic_write_line(filepath, line_data):
    """
    Atomically appends a single JSON line to the file.
    """
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(line_data) + "\n")
    except Exception as e:
        print(f"❌ Failed to write open trade log: {e}")


def log_open_trade(trade_id, agent, direction, strike, expiry, meta=None):
    """
    Logs a basic open trade with optional metadata.
    """
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


def track_open_trade(symbol, context):
    """
    Mesh-aware trade tracker for entry logs.
    Writes rich entry context including required fields for recovery.
    """
    try:
        trade_id = context.get("trade_id", f"{symbol}_{datetime.utcnow().isoformat()}")
        direction = context.get("direction") or ("long" if context.get("call_put") == "C" else "short")
        mesh_score = context.get("mesh_score", 100)
        pnl = context.get("pnl", 0.0)
        entry_time = context.get("timestamp", datetime.utcnow().isoformat())

        entry = {
            "trade_id": trade_id,
            "symbol": symbol,
            "entry_time": entry_time,
            "direction": direction,
            "mesh_score": mesh_score,
            "pnl": pnl,
            "quantity": context.get("quantity", 1),
            "option_symbol": context.get("option_symbol"),
            "strike": context.get("strike"),
            "expiry": context.get("expiry"),
            "signal_id": context.get("signal_id"),
            "entry_context": context
        }

        atomic_write_line(OPEN_TRADES_PATH, entry)
        print(f"🟢 Tracked open trade: {symbol} (ID: {trade_id})")

    except Exception as e:
        print(f"⚠️ Failed to track open trade: {e}")


def is_expired(option_symbol: str) -> bool:
    """
    Checks if the option symbol is expired based on today's date.
    Assumes format like SPY250527C00430000 → 25-05-27
    """
    try:
        expiry_str = option_symbol[3:9]  # Extract YYMMDD
        expiry_date = datetime.strptime(expiry_str, "%y%m%d").date()
        return expiry_date < datetime.utcnow().date()
    except Exception as e:
        print(f"⚠️ Failed to parse expiry from {option_symbol}: {e}")
        return True  # Treat parse errors as expired

def load_open_trades(path=OPEN_TRADES_PATH):
    """
    Loads and filters open trades from JSONL.
    Filters out any expired contracts based on option symbol.
    Returns a list of valid trade dicts.
    """
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
    """
    Removes a trade entry by its ID and rewrites the file.
    """
    trades = load_open_trades()
    updated = [t for t in trades if t.get("trade_id") != trade_id]
    
    try:
        with open(OPEN_TRADES_PATH, "w") as f:
            for t in updated:
                f.write(json.dumps(t) + "\n")
        print(f"🧹 Removed trade: {trade_id}")
    except Exception as e:
        print(f"⚠️ Failed to rewrite {OPEN_TRADES_PATH}: {e}")

