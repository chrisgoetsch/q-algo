# File: core/entry_learner.py — v2.1 optimized for multi-agent mesh scoring

from __future__ import annotations
import os, json, asyncio
from datetime import datetime
from functools import lru_cache
from typing import Dict, Tuple, Any

import pandas as pd, numpy as np, joblib

from analytics.regime_forecaster import forecast_market_regime
from core.mesh_router import get_mesh_signal
from polygon.polygon_rest import get_option_metrics, get_dealer_flow_metrics
from polygon.polygon_websocket import SPY_LIVE_PRICE
from core.logger_setup import get_logger
from analytics.qthink_log_labeler import log_score_breakdown_async

logger = get_logger(__name__)

MODEL_PATH = "core/models/entry_model.pkl"
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
MODEL_VERSION = "entry-model-v2.1"
ENTRY_THRESHOLD = float(os.getenv("ENTRY_THRESHOLD", "0.55"))

REGIME_THRESHOLDS = {
    "panic": 0.80,
    "bearish": 0.75,
    "choppy": 0.65,
    "stable": 0.60,
    "bullish": 0.55,
    "trending": 0.55,
}

@lru_cache(maxsize=1)
def _load_model():
    if os.path.exists(MODEL_PATH):
        logger.info({"event": "ml_model_loaded", "path": MODEL_PATH})
        return joblib.load(MODEL_PATH)
    logger.warning({"event": "ml_model_missing"})
    return None

model = _load_model()

def _price() -> float:
    return SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade") or 0.0

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

async def evaluate_entry(symbol: str = "SPY", default_threshold: float | None = None, want_meta: bool = False, force_trade: bool = False) -> bool | dict:
    threshold_base = default_threshold if default_threshold is not None else ENTRY_THRESHOLD

    try:
        ctx = {
            "symbol": symbol,
            "price": _price(),
            "volume": 0,
            "iv": 0,
            "delta": 0,
            "gamma": 0,
            "skew": 0,
            "dealer_flow": 0,
        }

        opt = await asyncio.to_thread(get_option_metrics, symbol)
        if isinstance(opt, list):
            opt = next((o for o in opt if isinstance(o, dict) and "delta" in o), {})

        if not isinstance(opt, dict) or not opt.get("delta"):
            raise ValueError(f"Malformed or missing option data for {symbol}: {repr(opt)}")

        dealer = await asyncio.to_thread(get_dealer_flow_metrics, symbol) or {}

        ctx.update({
            "volume": opt.get("volume", 0),
            "iv": opt.get("iv", 0),
            "delta": opt.get("delta", 0),
            "gamma": opt.get("gamma", 0),
            "skew": opt.get("skew", 0),
            "dealer_flow": dealer.get("score", 0),
        })

        score, rationale, regime, mesh = await asyncio.to_thread(score_entry, ctx)

        threshold = REGIME_THRESHOLDS.get(regime, threshold_base)
        decision = force_trade or score >= threshold

        logger.info({
            "event": "entry_accepted" if decision else "entry_rejected",
            "score": round(score, 3),
            "threshold": threshold,
            "regime": regime
        })

        result = {
            "score": score,
            "rationale": rationale,
            "regime": regime,
            "passes": decision,
            "agent_signals": mesh.get("agent_signals", {}),
            "mesh_score": mesh.get("score", 0),
            "gpt_confidence": round(score, 3),
            "gpt_reasoning": rationale,
            "greeks": ctx,
        }

        return result if want_meta else decision

    except Exception as e:
        logger.error({"event": "evaluate_entry_fail", "symbol": symbol, "err": str(e)})
        print(f"[evaluate_entry] error → {e}")
        return False if not want_meta else {"error": str(e), "passes": False}

def score_entry(ctx: dict) -> Tuple[float, str, str, dict]:
    mesh = get_mesh_signal(ctx)
    if mesh.get("score", 0) >= 99:
        return 0.90, "mesh_override", forecast_market_regime(ctx), mesh

    ctx.update({
        "mesh_confidence": mesh.get("score", 0),
        "agent_signals": mesh.get("agent_signals", {}),
        "mesh_score": mesh.get("score", 0),
        "alpha_decay": ctx.get("alpha_decay", 0.1),
    })

    if model is None:
        return 0.50, "model missing", "unknown", ctx

    try:
        df = _feature_frame(ctx)
        prob = model.predict_proba(df)[0][1]
        rationale = f"ml={prob:.2f} mesh={ctx['mesh_confidence']} → {prob:.2f}"
        regime = next((k for k, v in REGIME_THRESHOLDS.items() if prob >= v), "unknown")

        ctx.update({
            "model_score": prob,
            "regime": regime,
            "rationale": rationale,
            "model_version": MODEL_VERSION
        })

        asyncio.run(log_score_breakdown_async({
            "final": round(prob, 4),
            "mesh": ctx["mesh_confidence"],
            "regime": regime,
            "agent_signals": mesh.get("agent_signals", {}),
            "reason": rationale
        }))

        return round(prob, 4), rationale, regime, ctx

    except Exception as e:
        logger.warning({"event": "ml_score_failed", "err": str(e)})
        return 0.50, "ml fail", "unknown", ctx
