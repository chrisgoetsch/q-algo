# File: core/market_environment.py

import os
import json
from datetime import datetime

VIX_WATCHLIST_PATH = "data/vix_watchlist.json"
PIVOT_ALERT_PATH = "data/pivot_alert.json"
DEALER_EXPOSURE_PATH = "data/dealer_exposure.json"

def load_json_file(path):
    if not os.path.exists(path):
        print(f"[Environment] Warning: {path} not found.")
        return {}
    with open(path, "r") as f:
        return json.load(f)

def get_vix_environment(vix_value):
    """
    Categorize VIX level into 'calm', 'elevated', 'extreme'
    """
    if vix_value < 15:
        return "calm"
    elif 15 <= vix_value < 25:
        return "elevated"
    else:
        return "extreme"

def get_today_pivot_alert():
    """
    Check today's date in pivot_alert.json
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    alerts = load_json_file(PIVOT_ALERT_PATH).get("alerts", [])
    for alert in alerts:
        if alert.get("date") == today:
            return alert.get("macro_type", "unknown")
    return "none"

def get_dealer_gamma_position():
    """
    Read dealer gamma exposure bias (positive, neutral, negative)
    """
    dealer_data = load_json_file(DEALER_EXPOSURE_PATH)
    gamma_exposure = dealer_data.get("gamma_exposure", 0)
    if gamma_exposure > 0:
        return "positive"
    elif gamma_exposure < 0:
        return "negative"
    else:
        return "neutral"

def snapshot_market_environment(vix_value):
    """
    Produce a market environment snapshot
    """
    vix_regime = get_vix_environment(vix_value)
    pivot_alert = get_today_pivot_alert()
    gamma_position = get_dealer_gamma_position()

    snapshot = {
        "vix_level": vix_regime,
        "pivot_alert": pivot_alert,
        "gamma_position": gamma_position
    }

    print(f"[Environment] Snapshot: {snapshot}")
    return snapshot
