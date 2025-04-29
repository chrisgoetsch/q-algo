# File: core/entry_learner.py

import random
import json
import os
import time
from datetime import datetime
from brokers.tradier_client import get_quote
from core.mesh_router import score_mesh_signals
from qthink.qthink_inference import generate_trade_reasoning
from core.market_environment import snapshot_market_environment
from core.live_price_tracker import get_current_spy_price
from utils.atomic_write import atomic_append_jsonl

SYNC_LOG_PATH = "logs/sync_log.jsonl"

def evaluate_entry(symbol="SPY", vix_value=18.0):
    price = get_current_spy_price()
    if price is None:
        print(f"[Entry Learner] No live price available for {symbol}")
        return False

    print(f"[Entry Learner] Current price of {symbol}: {price}")

    mesh_score_data = score_mesh_signals(symbol)
    mesh_score = mesh_score_data.get("score", 0)
    mesh_trigger_agents = mesh_score_data.get("trigger_agents", [])
    print(f"[Entry Learner] Mesh Score: {mesh_score} from agents {mesh_trigger_agents}")

    env_snapshot = snapshot_market_environment(vix_value)

    decision = mesh_score >= 65 and env_snapshot.get("vix_level") != "extreme"
    trade_action = "entry_attempted" if decision else "entry_skipped"

    reasoning = generate_trade_reasoning(
        symbol=symbol,
        price=price,
        mesh_score=mesh_score,
        trigger_agents=mesh_trigger_agents
    )

    journal_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "price": price,
        "mesh_score": mesh_score,
        "trigger_agents": mesh_trigger_agents,
        "environment": env_snapshot,
        "reasoning": reasoning,
        "decision": "enter_trade" if decision else "skip_trade",
        "confidence_threshold": 65
    }
    atomic_append_jsonl(SYNC_LOG_PATH, journal_entry)

    print(f"[Entry Learner] Decision: {'ENTER' if decision else 'SKIP'} | Reason: {reasoning}")
    return decision
