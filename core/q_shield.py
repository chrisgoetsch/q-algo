# q_shield.py
# Detects macro volatility via VIX and suppresses trading when needed

import json
import random

def get_vix_state():
    with open("data/vix_watchlist.json", "r") as f:
        return json.load(f)

def get_risk_signal():
    vix = get_vix_state()
    level = vix.get("latest_vix", 18)

    if level > 25:
        print(f"⚠️ Q Shield: High VIX {level}")
        return "EXIT"
    elif level > 21:
        return "RISK"
    return "HOLD"

