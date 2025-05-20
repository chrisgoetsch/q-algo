# File: analytics/q_backtest_batch.py

import os
import json
import random
from datetime import datetime
from time import sleep
from core.live_price_tracker import get_current_spy_price
from analytics.qthink_cluster_analysis import analyze_trade_with_gpt

BACKTEST_LOG_FOLDER = "logs/backtests/"
os.makedirs(BACKTEST_LOG_FOLDER, exist_ok=True)

def simulate_entry(symbol="SPY", call_put="C"):
    base_price = get_current_spy_price()
    if base_price is None:
        return None

    # Introduce slight price randomness to simulate different entry points
    jitter = random.uniform(-0.5, 0.5)
    adjusted_price = base_price + jitter

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "price": round(adjusted_price, 2),
        "side": f"buy_{call_put.lower()}",
        "status": "open"
    }

def simulate_exit(entry_data, target_profit=0.05, stop_loss=-0.05, vix_value=18.0):
    market_price = get_current_spy_price()
    if market_price is None or not entry_data:
        return None

    # Add exit jitter to mimic market change
    jitter = random.uniform(-0.5, 0.5)
    adjusted_exit = market_price + jitter
    entry_price = entry_data["price"]
    pnl = ((adjusted_exit - entry_price) / entry_price) * 100

    if vix_value > 25:
        stop_loss = -3

    if pnl > target_profit:
        reason = f"Take Profit: {target_profit}%"
    elif pnl < stop_loss:
        reason = f"Stop Loss: {stop_loss}%"
    else:
        return None

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": entry_data["symbol"],
        "entry_price": entry_price,
        "exit_price": round(adjusted_exit, 2),
        "pnl_percentage": round(pnl, 2),
        "exit_reason": reason,
        "status": "closed",
        "outcome": "profit" if pnl > 0 else "loss"
    }

def record_result(entry, exit):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = os.path.join(BACKTEST_LOG_FOLDER, f"{today}_batch_backtest.jsonl")
    result = {"entry": entry, "exit": exit}

    try:
        gpt_feedback = analyze_trade_with_gpt(entry, exit)
        result["qthink_feedback"] = gpt_feedback
    except Exception as e:
        result["qthink_feedback"] = {"error": str(e)}

    with open(log_file, "a") as f:
        f.write(json.dumps(result) + "\n")
    print(f"✔️  Logged trade: {result}")

def batch_run(trades=25, sleep_seconds=1):
    print(f"🚀 Running batch backtest: {trades} trades")
    for i in range(trades):
        print(f"🔁 Trade {i+1}")
        entry = simulate_entry()
        if entry:
            sleep(sleep_seconds)
            exit = simulate_exit(entry)
            if exit:
                record_result(entry, exit)
            else:
                print("⏩ Exit condition not met.")
        else:
            print("❌ Skipping - no entry data.")

if __name__ == "__main__":
    batch_run(trades=25, sleep_seconds=1)
