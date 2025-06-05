# File: core/entry_learner.py  (refactored with legacy shim)
"""Scores potential entries with ML + mesh signals + regime forecast.

Includes back‑compat `build_entry_features()` for trade_engine.
"""
from __future__ import annotations

import os, json, asyncio
from datetime import datetime
from functools import lru_cache
from typing import Dict

import pandas as pd, numpy as np, joblib

from analytics.regime_forecaster import forecast_market_regime
from core.mesh_router import get_mesh_signal
from polygon.polygon_rest import get_option_metrics, get_dealer_flow_metrics
from polygon.polygon_websocket import SPY_LIVE_PRICE
from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------
MODEL_PATH = "core/models/entry_model.pkl"
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
SCORE_LOG_PATH = os.getenv("SCORE_LOG_PATH", "logs/qthink_score_breakdown.jsonl")
MODEL_VERSION = "entry-model-v1.0"

# ---------------------------------------------------------------------------
# Load ML model lazily
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_model():
    if os.path.exists(MODEL_PATH):
        logger.info({"event": "ml_model_loaded", "path": MODEL_PATH})
        return joblib.load(MODEL_PATH)
    logger.warning({"event": "ml_model_missing"})
    return None

model = _load_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _price() -> float:
    return SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade") or 0.0


def _load_profile() -> Dict[str, int]:
    try:
        return json.load(open(REINFORCEMENT_PROFILE_PATH)) if os.path.exists(REINFORCEMENT_PROFILE_PATH) else {}
    except Exception as e:
        logger.error({"event": "reinforcement_load_fail", "err": str(e)})
        return {}


def _log_score(obj: dict):
    try:
        os.makedirs(os.path.dirname(SCORE_LOG_PATH), exist_ok=True)
        with open(SCORE_LOG_PATH, "a") as fh:
            fh.write(json.dumps(obj) + "\n")
    except Exception as e:
        logger.error({"event": "score_log_fail", "err": str(e)})


def _feature_frame(ctx: dict) -> pd.DataFrame:
    base = {
        "price": ctx.get("price", 0),
        "iv": ctx.get("iv", 0),
        "volume": ctx.get("volume", 0),
        "skew": ctx.get("skew", 0),
        "delta": ctx.get("delta", 0),
        "gamma": ctx.get("gamma", 0),
        "dealer_flow": ctx.get("dealer_flow", 0),
        "mesh_confidence": ctx.get("mesh_confidence", 0),
        "mesh_score": ctx.get("mesh_score", 0),
        "alpha_decay": ctx.get("alpha_decay", 0.1),
    }
    for agent, sc in ctx.get("agent_signals", {}).items():
        base[f"agent_{agent}"] = sc
    df = pd.DataFrame([base])

    if model and hasattr(model, "feature_names_in_"):
        df = df.reindex(columns=model.feature_names_in_, fill_value=0)
    return df

# Back‑compat alias for trade_engine ----------------------------------------

def build_entry_features(context: dict):
    """Legacy wrapper used by trade_engine. Returns DataFrame."""
    return _feature_frame(context)

# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def score_entry(ctx: dict) -> tuple[float, str]:
    mesh = get_mesh_signal(ctx)
    ctx.update({
        "mesh_confidence": mesh.get("score", 0),
        "agent_signals": mesh.get("agent_signals", {}),
        "mesh_score": mesh.get("score", 0),
        "alpha_decay": ctx.get("alpha_decay", 0.1),
    })

    df = _feature_frame(ctx)
    if df.empty:
        return 0.0, "empty_feature_frame"

    profile = _load_profile()
    penalties = sum(profile.get(k, 0) for k in ("bad", "conflict", "regret"))
    boosts = sum(profile.get(k, 0) for k in ("strong", "profit"))
    regime = forecast_market_regime(ctx)
    regime_mod = {"panic": -0.3, "bearish": -0.2, "choppy": -0.1, "stable": 0.0, "bullish": 0.1, "trending": 0.2}.get(regime, 0.0)

    raw = model.predict_proba(df)[0][1] if model else 0.0
    adjusted = raw + 0.05 * boosts - 0.05 * penalties + regime_mod
    final = 0.6 * adjusted + 0.4 * (ctx["mesh_confidence"] / 100)

    rationale = f"ml={raw:.2f} adj={adjusted:.2f} mesh={ctx['mesh_confidence']:.1f} regime={regime} → {final:.2f}"

    _log_score({
        "timestamp": datetime.utcnow().isoformat(),
        "final": round(final, 4),
        "raw": round(raw, 4),
        "mesh": ctx["mesh_confidence"],
        "regime": regime,
        "model_version": MODEL_VERSION,
    })

    return round(final, 4), rationale

# ---------------------------------------------------------------------------
# Coroutine API
# ---------------------------------------------------------------------------

async def evaluate_entry(symbol: str = "SPY", threshold: float = 0.6) -> bool:
    try:
        opt = await asyncio.to_thread(get_option_metrics, symbol)
        dealer = await asyncio.to_thread(get_dealer_flow_metrics, symbol) or {}

        ctx = {
            "symbol": symbol,
            "price": _price(),
            "iv": opt.get("iv", 0),
            "volume": opt.get("volume", 0),
            "skew": opt.get("skew", 0),
            "delta": opt.get("delta", 0),
            "gamma": opt.get("gamma", 0),
            "dealer_flow": dealer.get("score", 0),
        }

        score, rationale = await asyncio.to_thread(score_entry, ctx)
        print(f"[Entry] {symbol} score {score:.2f} (th {threshold}) | {rationale}")
        return score >= threshold

    except Exception as e:
        logger.error({"event": "evaluate_entry_fail", "err": str(e)})
        return False

# ---------------------------------------------------------------------------
# CLI self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, asyncio as aio

    async def _test():
        ok = await evaluate_entry("SPY", 0.5)
        print("entry decision →", ok)

    aio.run(_test())
