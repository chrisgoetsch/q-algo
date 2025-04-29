# File: analytics/q_backtest.py

import os
import json
from datetime import datetime
from core.live_price_tracker import get_current_spy_price

BACKTEST_LOG_FOLDER = "logs/backtests/"
os.makedirs(BACKTEST_LOG_FOLDER, exist_ok=True)

def simulate_live_entry(symbol="SPY", call_put="C", expiration=None):
    """
    Simulate entering a position using real-time SPY pricing.
    """
    current_price = get_current_spy_price()
    if current_price is None:
        print("[Backtest] No live price available — cannot simulate entry.")
        return None

    entry_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "price": current_price,
        "side": f"buy_{call_put.lower()}",
        "status": "open"
    }
    print(f"[Backtest] Simulated entry: {entry_data}")
    return entry_data

def simulate_live_exit(entry_data, target_profit=20, stop_loss=-10, vix_value=18.0):
    """
    Simulate exiting a position using real-time SPY pricing and simple rules.
    """
    current_price = get_current_spy_price()
    if current_price is None or not entry_data:
        print("[Backtest] No live price available or missing entry data — cannot simulate exit.")
        return None

    entry_price = entry_data["price"]
    pnl_percentage = ((current_price - entry_price) / entry_price) * 100 if entry_price else 0

    exit_now = False
    exit_reason = ""

    # Optional: tighten based on VIX
    if vix_value > 25:
        stop_loss = -5

    if pnl_percentage > target_profit:
        exit_now = True
        exit_reason = f"Take Profit: +{target_profit}%"
    elif pnl_percentage < stop_loss:
        exit_now = True
        exit_reason = f"Stop Loss: {stop_loss}%"

    if not exit_now:
        print(f"[Backtest] No exit triggered yet: PnL {pnl_percentage:.2f}%")
        return None

    exit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": entry_data["symbol"],
        "entry_price": entry_price,
        "exit_price": current_price,
        "pnl_percentage": pnl_percentage,
        "exit_reason": exit_reason,
        "status": "closed",
        "outcome": "profit" if pnl_percentage > 0 else "loss"
    }
    print(f"[Backtest] Simulated exit: {exit_data}")
    return exit_data

def record_backtest_result(entry_data, exit_data):
    """
    Save the entry and exit simulation to backtest logs.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    path = os.path.join(BACKTEST_LOG_FOLDER, f"{today}_live_backtest.jsonl")

    with open(path, "a") as f:
        f.write(json.dumps({
            "entry": entry_data,
            "exit": exit_data
        }) + "\n")

    print(f"[Backtest] Recorded simulation to {path}")

if __name__ == "__main__":
    entry = simulate_live_entry(symbol="SPY")
    if entry:
        # Wait a few seconds to simulate holding period
        import time
        time.sleep(5)

        exit_data = simulate_live_exit(entry)
        if exit_data:
            record_backtest_result(entry, exit_data)
