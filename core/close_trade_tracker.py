# File: core/close_trade_tracker.py
# Q-ALGO v2 - Tracks closed trades and updates reinforcement profile

import os
import json
from datetime import datetime
from core.open_trade_tracker import load_open_trades, remove_trade

CLOSE_LOG_PATH = os.getenv("CLOSE_TRADES_FILE_PATH", "logs/closed_trades.jsonl")
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")

LABEL_KEYWORDS = ["profit", "target", "strong", "alignment"]
NEGATIVE_KEYWORDS = ["bad entry", "mesh conflict", "regret"]

def log_closed_trade(trade_id, result, context):
    """
    Save the result of a closed trade, and remove it from open_trades.jsonl.
    Also updates the reinforcement profile.
    """
    closed_entry = {
        "trade_id": trade_id,
        "result": result,
        "exit_context": context,
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        os.makedirs(os.path.dirname(CLOSE_LOG_PATH), exist_ok=True)
        with open(CLOSE_LOG_PATH, "a") as f:
            f.write(json.dumps(closed_entry) + "\n")
        remove_trade(trade_id)
        print(f"🔴 Closed trade logged: {trade_id}")
        update_reinforcement_profile(context.get("rationale", ""))
    except Exception as e:
        print(f"❌ Failed to log closed trade: {e}")

def update_reinforcement_profile(label_text):
    """
    Update reinforcement profile based on final rationale (e.g. bad exit or strong signal).
    """
    label_text = label_text.lower()
    profile = {}
    if os.path.exists(REINFORCEMENT_PROFILE_PATH):
        try:
            with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
                profile = json.load(f)
        except Exception:
            profile = {}

    labels = []
    for k in LABEL_KEYWORDS:
        if k in label_text:
            labels.append(k)
    for k in NEGATIVE_KEYWORDS:
        if k in label_text:
            labels.append(k)

    for label in labels:
        profile[label] = profile.get(label, 0) + 1

    try:
        with open(REINFORCEMENT_PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=2)
        print("🧠 Reinforcement profile updated.")
    except Exception as e:
        print(f"⚠️ Failed to update reinforcement profile: {e}")
