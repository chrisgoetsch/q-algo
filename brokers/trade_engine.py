# File: core/trade_engine.py

import time
import json
import os
from datetime import datetime
from brokers.tradier_execution import place_option_order
from brokers.tradier_client import get_option_chain
from core.mesh_router import score_mesh_signals
from qthink.qthink_inference import generate_trade_reasoning
from core.market_environment import snapshot_market_environment
from core.live_price_tracker import get_current_spy_price
from utils.atomic_write import atomic_append_jsonl

SYNC_LOG_PATH = "logs/sync_log.jsonl"

def find_atm_option(symbol="SPY", expiration=None, call_put="C"):
    chain = get_option_chain(symbol, expiration)
    options = chain.get("options", {}).get("option", [])

    if not options:
        return None

    current_price = get_current_spy_price()
    if current_price is None:
        print("[Trade Engine] Warning: No live price available — fallback ATM selection.")
        return None

    closest_option = None
    closest_diff = float('inf')

    for opt in options:
        if opt['option_type'].upper() != call_put:
            continue
        diff = abs(float(opt['strike']) - current_price)
        if diff < closest_diff:
            closest_diff = diff
            closest_option = opt

    return closest_option

def open_position(symbol="SPY", quantity=1, call_put="C", expiration=None, vix_value=18.0):
    atm_option = find_atm_option(symbol, expiration, call_put)
    if not atm_option:
        print("[Trade Engine] No ATM option found.")
        return

    option_symbol = atm_option['symbol']
    print(f"[Trade Engine] Preparing to open position: {option_symbol}...")

    mesh_score_data = score_mesh_signals(symbol)
    mesh_score = mesh_score_data.get("score", 0)
    mesh_trigger_agents = mesh_score_data.get("trigger_agents", [])

    price = get_current_spy_price()
    env_snapshot = snapshot_market_environment(vix_value)

    qthink_reasoning = generate_trade_reasoning(
        symbol=symbol,
        price=price,
        mesh_score=mesh_score,
        trigger_agents=mesh_trigger_agents
    )

    result = place_option_order(option_symbol=option_symbol, quantity=quantity, action="buy_to_open")
    print(f"[Trade Engine] Order result: {result}")

    journal_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "option_symbol": option_symbol,
        "price": price,
        "quantity": quantity,
        "trade_action": "buy_to_open",
        "mesh_score": mesh_score,
        "trigger_agents": mesh_trigger_agents,
        "environment": env_snapshot,
        "qthink_reasoning": qthink_reasoning,
        "broker_response": result
    }
    atomic_append_jsonl(SYNC_LOG_PATH, journal_entry)
