# File: core/capital_manager.py  (patched — added parse_account_balances)
"""Capital allocation & risk throttle utilities aligned with new Tradier flow."""
from __future__ import annotations

import os, json
from datetime import datetime
from typing import Tuple

from polygon.polygon_rest import get_option_metrics
from analytics.model_audit import analyze_by_model, load_trades
from core.resilient_request import resilient_get
from core.logger_setup import logger
from core.tradier_execution import _headers  # internal helper ok for now

# ---------------------------------------------------------------------------
# Paths / env
# ---------------------------------------------------------------------------
CAPITAL_TRACKER_PATH = os.getenv("CAPITAL_TRACKER_PATH", "logs/capital_tracker.json")
EQUITY_BASELINE_PATH = os.getenv("EQUITY_BASELINE_PATH", "logs/equity_baseline.json")
MODEL_VERSION = "entry-model-v1.0"
FORCED_ALLOCATION_OVERRIDE = float(os.getenv("FORCED_ALLOCATION_OVERRIDE", 0))

TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "")

# ---------------------------------------------------------------------------
# Helper: parse Tradier balances
# ---------------------------------------------------------------------------

def parse_account_balances(data: dict) -> Tuple[float, float]:
    """Return (buying_power, equity) from Tradier balances JSON."""
    balances = data.get("balances", {})

    # equity — try multiple common keys
    equity = 0.0
    for key in ("total_equity", "account_value", "equity", "cash_available"):
        val = balances.get(key)
        try:
            equity = max(equity, float(val)) if val is not None else equity
        except (TypeError, ValueError):
            continue

    # option buying power (margin acct) else cash_available
    buying_power = 0.0
    obp = balances.get("margin", {}).get("option_buying_power")
    try:
        buying_power = float(obp) if obp is not None else float(balances.get("cash_available", 0.0))
    except (TypeError, ValueError):
        buying_power = 0.0

    return buying_power, equity

# ---------------------------------------------------------------------------
# Tradier buying-power fetch (resilient)
# ---------------------------------------------------------------------------

def _tradier_balances(verbose: bool = False) -> Tuple[float, float]:
    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/balances"
    resp = resilient_get(url, headers=_headers())
    if not resp:
        return 0.0, 0.0
    if verbose:
        print("📊 Tradier Balance Response:", resp.text)
    try:
        data = resp.json()
    except Exception as e:
        logger.error({"event": "balance_parse_fail", "err": str(e), "raw": resp.text})
        return 0.0, 0.0
    return parse_account_balances(data)


def get_tradier_buying_power(verbose: bool = False) -> Tuple[float, float]:
    bp, eq = _tradier_balances(verbose)
    print(f"✅ Tradier buying power ${bp:,.2f} | Equity ${eq:,.2f}")
    return bp, eq

# ---------------------------------------------------------------------------
# Model-aware allocation helpers
# ---------------------------------------------------------------------------

def get_latest_win_rate(version: str = MODEL_VERSION) -> float:
    try:
        summary = analyze_by_model(load_trades())
        return float(summary.get(version, {}).get("win_rate", 0.5))
    except Exception as e:
        logger.error({"event": "win_rate_fetch_fail", "error": str(e)})
        return 0.5

# ---------------------------------------------------------------------------
# Allocation logic
# ---------------------------------------------------------------------------

def get_current_allocation(default: float = 0.2) -> float:
    if FORCED_ALLOCATION_OVERRIDE > 0:
        print(f"🔒 Using FORCED override {FORCED_ALLOCATION_OVERRIDE:.2f}")
        return FORCED_ALLOCATION_OVERRIDE

    wr = get_latest_win_rate()
    if wr < 0.4:
        return 0.1
    if wr > 0.7:
        return 0.3

    if not os.path.exists(CAPITAL_TRACKER_PATH):
        return default
    try:
        return float(json.load(open(CAPITAL_TRACKER_PATH)).get("recommended_allocation", default))
    except Exception as e:
        logger.error({"event": "cap_track_read_fail", "err": str(e)})
        return default


def log_allocation_update(
    recommended: float,
    rationale: str = "ml_adjusted",
    qthink_label: str | None = None,
    regime: str = "normal",
    risk_profile: str = "neutral",
    confidence_score: float = 0.0,
    regret_risk: float = 0.0,
    meta: dict | None = None,
):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "recommended_allocation": round(recommended, 3),
        "rationale": rationale,
        "regime": regime,
        "qthink_label": qthink_label or "unlabeled",
        "risk_profile": risk_profile,
        "confidence_score": confidence_score,
        "regret_risk": regret_risk,
        "meta": meta or {},
    }
    os.makedirs(os.path.dirname(CAPITAL_TRACKER_PATH), exist_ok=True)
    with open(CAPITAL_TRACKER_PATH, "w") as fh:
        json.dump(entry, fh, indent=2)
    print(f"💰 Capital allocation updated → {recommended:.2f} ({regime}, {rationale})")

# ---------------------------------------------------------------------------
# Utility calculators (unchanged)
# ---------------------------------------------------------------------------

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


def compute_position_size(base_allocation: float, mesh_agent_score: float, gpt_confidence: float,
                           max_position_fraction: float = 0.3) -> float:
    tier_boost = 0.0
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
        print("🚨 SURVIVAL MODE drawdown > 30%")
        return 0.2
    if drawdown > 0.15:
        print("⚠️ Drawdown > 15% — throttling")
        return 0.5
    return 1.0


def load_equity_baseline() -> float:
    try:
        return float(json.load(open(EQUITY_BASELINE_PATH)).get("equity_baseline", 0))
    except Exception:
        return 0.0


def save_equity_baseline(value: float):
    os.makedirs(os.path.dirname(EQUITY_BASELINE_PATH), exist_ok=True)
    json.dump({"equity_baseline": value}, open(EQUITY_BASELINE_PATH, "w"))

# ---------------------------------------------------------------------------
# Volatility scaling helper
# ---------------------------------------------------------------------------

def scale_allocation_by_volatility(symbol: str, target_iv: float = 0.3) -> float:
    option_data = get_option_metrics(symbol) or {}
    current_iv = option_data.get("iv", 0.3)
    vol_scale = target_iv / current_iv if current_iv > 0 else 1.0
    return max(0.05, min(round(0.2 * vol_scale, 3), 1.0))