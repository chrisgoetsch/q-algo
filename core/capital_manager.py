# File: core/capital_manager.py

import os
import json
import requests
from datetime import datetime
from polygon.polygon_rest import get_option_metrics
from analytics.model_audit import analyze_by_model, load_trades

CAPITAL_TRACKER_PATH = os.getenv("CAPITAL_TRACKER_PATH", "logs/capital_tracker.json")
EQUITY_BASELINE_PATH = os.getenv("EQUITY_BASELINE_PATH", "logs/equity_baseline.json")

MODEL_VERSION = "entry-model-v1.0"


def get_latest_win_rate(version=MODEL_VERSION) -> float:
    try:
        trades = load_trades()
        summary = analyze_by_model(trades)
        return summary.get(version, {}).get("win_rate", 0.5)
    except Exception as e:
        print(f"⚠️ Failed to fetch model win rate: {e}")
        return 0.5


def parse_account_balances(data):
    balances = data.get("balances", {})
    equity_keys = ["equity", "account_value", "total_equity", "cash_available"]
    equity = 0.0
    for key in equity_keys:
        try:
            val = balances.get(key)
            if isinstance(val, dict):
                for subval in val.values():
                    if isinstance(subval, (int, float)):
                        equity = max(equity, subval)
            else:
                equity = float(val)
            if equity > 0:
                break
        except:
            continue

    buying_power = float(balances.get("margin", {}).get("option_buying_power", 0.0))
    return buying_power, equity


def get_current_allocation(default: float = 0.2) -> float:
    model_win_rate = get_latest_win_rate()
    if model_win_rate < 0.4:
        print("⚠️ Model underperforming. Reducing allocation.")
        return 0.1
    if model_win_rate > 0.7:
        print("🔥 Model strong. Boosting allocation.")
        return 0.3

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
                          confidence_score: float = 0.0,
                          regret_risk: float = 0.0,
                          meta: dict = None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "recommended_allocation": round(recommended, 3),
        "rationale": rationale,
        "regime": regime,
        "qthink_label": qthink_label or "unlabeled",
        "risk_profile": risk_profile,
        "confidence_score": confidence_score,
        "regret_risk": regret_risk,
        "meta": meta or {}
    }
    try:
        os.makedirs(os.path.dirname(CAPITAL_TRACKER_PATH), exist_ok=True)
        with open(CAPITAL_TRACKER_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"💰 Capital allocation updated: {recommended:.2f} ({regime}, {rationale})")
    except Exception as e:
        print(f"❌ Failed to log capital update: {e}")


def adjust_allocation_from_signal(win_rate: float, volatility_score: float, drawdown: float,
                                   mesh_density: float, confidence_score: float = 0.5, regret_risk: float = 0.5) -> float:
    base = 0.2
    if win_rate > 0.65 and drawdown < 0.1:
        base += 0.1
    if confidence_score > 0.75:
        base += 0.05
    if regret_risk < 0.2:
        base += 0.05
    if drawdown > 0.2:
        base -= 0.1
    if volatility_score > 0.6:
        base -= 0.1
    if regret_risk > 0.5:
        base -= 0.05
    return max(0.05, min(round(base, 3), 1.0))


def compute_position_size(base_allocation: float, mesh_agent_score: float,
                           gpt_confidence: float, max_position_fraction: float = 0.3) -> float:
    tier_boost = 0
    if mesh_agent_score > 0.8:
        tier_boost += 0.05
    if gpt_confidence > 0.85:
        tier_boost += 0.05
    if mesh_agent_score < 0.5:
        tier_boost -= 0.05
    adjusted = base_allocation + tier_boost
    return max(0.05, min(round(adjusted, 3), max_position_fraction))


def evaluate_drawdown_throttle(equity_now: float, equity_start: float) -> float:
    if equity_start == 0:
        return 1.0
    drawdown = (equity_start - equity_now) / equity_start
    if drawdown > 0.3:
        print("🚨 Entering SURVIVAL MODE: drawdown > 30%")
        return 0.2
    if drawdown > 0.15:
        print("⚠️ Drawdown exceeds 15% - reducing capital")
        return 0.5
    return 1.0


def load_equity_baseline() -> float:
    if os.path.exists(EQUITY_BASELINE_PATH):
        try:
            with open(EQUITY_BASELINE_PATH, "r") as f:
                return float(json.load(f).get("equity_baseline", 0))
        except Exception as e:
            print(f"⚠️ Failed to load equity baseline: {e}")
    return 0.0


def save_equity_baseline(value: float):
    try:
        os.makedirs(os.path.dirname(EQUITY_BASELINE_PATH), exist_ok=True)
        with open(EQUITY_BASELINE_PATH, "w") as f:
            json.dump({"equity_baseline": value}, f)
    except Exception as e:
        print(f"❌ Failed to save equity baseline: {e}")


def get_tradier_buying_power(verbose=False) -> tuple[float, float]:
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
        if verbose:
            print("📊 Tradier Balance Response:", json.dumps(data, indent=2))

        buying_power, equity = parse_account_balances(data)
        print(f"✅ Tradier buying power: ${buying_power:,.2f} | Equity: ${equity:,.2f}")
        return buying_power, equity
    except Exception as e:
        print(f"⚠️ Failed to retrieve Tradier balance info: {e}")
        return 0.0


def scale_allocation_by_volatility(symbol: str, target_iv: float = 0.3) -> float:
    option_data = get_option_metrics(symbol)
    current_iv = option_data.get("iv", 0.3)
    vol_scale = target_iv / current_iv if current_iv > 0 else 1.0
    allocation = 0.2 * vol_scale
    return max(0.05, min(round(allocation, 3), 1.0))
