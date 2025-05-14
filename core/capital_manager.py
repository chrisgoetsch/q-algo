# File: core/capital_manager.py

import os
import json
from datetime import datetime

CAPITAL_TRACKER_PATH = os.getenv("CAPITAL_TRACKER_PATH", "logs/capital_tracker.json")

def get_current_allocation(default: float = 0.2) -> float:
    """
    Reads the most recent QThink capital multiplier from capital_tracker.json.
    Clamps allocation to safe range [0.0, 1.0].
    """
    if not os.path.exists(CAPITAL_TRACKER_PATH):
        return default
    try:
        with open(CAPITAL_TRACKER_PATH, "r") as f:
            lines = f.readlines()
            if not lines:
                return default
            latest = json.loads(lines[-1])
            val = float(latest.get("recommended_allocation", default))
            return max(0.0, min(round(val, 3), 1.0))
    except Exception as e:
        print(f"⚠️ Failed to read capital allocation: {e}")
        return default

def log_allocation_update(recommended: float,
                          rationale: str = "ml_adjusted",
                          qthink_label: str = None,
                          regime: str = "normal",
                          risk_profile: str = "neutral",
                          meta: dict = None):
    """
    Logs a capital scaling event with full GPT/ML reasoning metadata.
    Supports regime tagging, risk modes, and future RL training.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "recommended_allocation": round(recommended, 3),
        "rationale": rationale,
        "regime": regime,
        "qthink_label": qthink_label or "unlabeled",
        "risk_profile": risk_profile,
        "meta": meta or {}
    }
    try:
        os.makedirs(os.path.dirname(CAPITAL_TRACKER_PATH), exist_ok=True)
        with open(CAPITAL_TRACKER_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"💰 Capital allocation updated: {recommended:.2f} ({regime}, {rationale})")
    except Exception as e:
        print(f"❌ Failed to log capital update: {e}")

def adjust_allocation_from_signal(win_rate: float, volatility_score: float, drawdown: float, mesh_density: float) -> float:
    """
    Simple ML-style logic for adjusting capital scaling.
    You can replace this with an XGBoost or neural net policy in future.
    """
    base = 0.2

    if win_rate > 0.65 and drawdown < 0.1:
        base += 0.1
    if volatility_score < 0.2:
        base += 0.05
    if mesh_density > 0.7:
        base += 0.05
    if drawdown > 0.2:
        base -= 0.1
    if volatility_score > 0.6:
        base -= 0.1

    # Clamp result to [0.05, 1.0]
    return max(0.05, min(round(base, 3), 1.0))

def get_tradier_buying_power() -> float:
    """
    Checks Tradier API for real-time available option buying power.
    """
    TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")
    TRADIER_ACCESS_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
    TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")

    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/balances"
    headers = {
        "Authorization": f"Bearer {TRADIER_ACCESS_TOKEN}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return float(data.get("balances", {}).get("margin", {}).get("option_buying_power", 0))
    except Exception as e:
        print(f"⚠️ Failed to retrieve Tradier buying power: {e}")
        return 0.0
