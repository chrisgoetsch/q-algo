# File: core/position_manager.py

import time
import json
import os
from datetime import datetime
from brokers.tradier_client import get_positions
from brokers.tradier_execution import place_option_order
from qthink.qthink_inference import generate_trade_reasoning
from core.market_environment import snapshot_market_environment
from core.live_price_tracker import get_current_spy_price
from mesh.mesh_router import adjust_agent_performance
from utils.atomic_write import atomic_append_jsonl, atomic_write_json

SYNC_LOG_PATH = "logs/sync_log.jsonl"
DAILY_ALPHA_FOLDER = "logs/daily_alpha_log/"

def get_open_positions():
    response = get_positions()
    if "positions" not in response or not response["positions"]:
        return []
    return response["positions"].get("position", [])

def write_daily_alpha_log(pnl_percentage, trade_result):
    """Update today's PnL summary in daily_alpha_log_DATE.json"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    os.makedirs(DAILY_ALPHA_FOLDER, exist_ok=True)
    path = os.path.join(DAILY_ALPHA_FOLDER, f"{today}.json")

    if os.path.exists(path):
        with open(path, "r") as f:
            daily_log = json.load(f)
    else:
        daily_log = {
            "date": today,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "net_pnl": 0.0
        }

    daily_log["total_trades"] += 1
    if trade_result == "profit":
        daily_log["wins"] += 1
    else:
        daily_log["losses"] += 1

    daily_log["net_pnl"] += pnl_percentage

    atomic_write_json(path, daily_log)

def update_sync_log_with_outcome(option_symbol, outcome):
    """Update the corresponding entry in sync_log.jsonl with realized outcome"""
    if not os.path.exists(SYNC_LOG_PATH):
        print(f"[Reinforcement] No sync log found.")
        return None

    updated_entries = []
    trigger_agents = None
    found = False

    with open(SYNC_LOG_PATH, "r") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("option_symbol") == option_symbol and "outcome" not in entry:
                entry["outcome"] = outcome
                trigger_agents = entry.get("trigger_agents", [])
                found = True
            updated_entries.append(entry)

    if found:
        temp_path = SYNC_LOG_PATH + ".tmp"
        with open(temp_path, "w") as f:
            for entry in updated_entries:
                f.write(json.dumps(entry) + "\n")
        os.replace(temp_path, SYNC_LOG_PATH)
        print(f"[Reinforcement] Updated sync log with outcome for {option_symbol}.")
    else:
        print(f"[Reinforcement] No matching entry found for {option_symbol}.")

    return trigger_agents

def manage_positions(vix_value=18.0):
    print("[Position Manager] Checking open positions...")
    positions = get_open_positions()
    if not positions:
        print("[Position Manager] No open positions.")
        return

    env_snapshot = snapshot_market_environment(vix_value)
    vix_regime = env_snapshot.get("vix_level", "unknown")
    pivot_alert = env_snapshot.get("pivot_alert", "none")

    for pos in positions:
        symbol = pos.get("symbol")
        quantity = pos.get("quantity", 0)
        cost_basis = pos.get("cost_basis", 0)

        last_price = get_current_spy_price()

        if last_price is None:
            print(f"[Position Manager] Warning: No live price for {symbol}")
            continue

        pnl_percentage = ((last_price - cost_basis) / cost_basis) * 100 if cost_basis else 0
        print(f"[Position Manager] {symbol} PnL: {pnl_percentage:.2f}% (Last: {last_price}, Basis: {cost_basis})")

        # Default exit rules
        take_profit = 20
        stop_loss = -10

        # Adjust exit rules based on environment
        if vix_regime == "extreme":
            stop_loss = -5
        if pivot_alert != "none":
            take_profit = 15

        exit_now = False
        exit_reason = ""

        if pnl_percentage > take_profit:
            exit_now = True
            exit_reason = f"Take Profit: +{take_profit}%"
        elif pnl_percentage < stop_loss:
            exit_now = True
            exit_reason = f"Stop Loss: {stop_loss}%"

        if exit_now:
            reasoning = generate_trade_reasoning(
                symbol=symbol,
                price=last_price,
                mesh_score=0,
                trigger_agents=["position_manager_exit"]
            )

            print(f"[Position Manager] Closing {symbol}: {exit_reason} | Reason: {reasoning}")

            result = place_option_order(option_symbol=symbol, quantity=quantity, action="sell_to_close")
            print(f"[Position Manager] Exit Result: {result}")

            journal_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "option_symbol": symbol,
                "last_price": last_price,
                "cost_basis": cost_basis,
                "pnl_percentage": pnl_percentage,
                "exit_reason": exit_reason,
                "environment": env_snapshot,
                "qthink_reasoning": reasoning,
                "trade_action": "exit_trade",
                "outcome": "profit" if pnl_percentage > 0 else "loss"
            }
            atomic_append_jsonl(SYNC_LOG_PATH, journal_entry)

            write_daily_alpha_log(pnl_percentage, "profit" if pnl_percentage > 0 else "loss")

            trigger_agents = update_sync_log_with_outcome(symbol, "profit" if pnl_percentage > 0 else "loss")
            if trigger_agents:
                adjust_agent_performance(trigger_agents, "profit" if pnl_percentage > 0 else "loss")

            time.sleep(1)  # API pacing
