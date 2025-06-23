# File: core/entry_learner.py  (v1.5 - final meta patch with GPT integration)

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
SCORE_LOG_PATH = os.getenv("SCORE_LOG_PATH", "logs/qthink_score_breakdown.jsonl")
MODEL_VERSION = "entry-model-v1.5"

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

def _load_profile() -> Dict[str, int]:
    try:
        if os.path.exists(REINFORCEMENT_PROFILE_PATH):
            return json.load(open(REINFORCEMENT_PROFILE_PATH))
    except Exception as e:
        logger.error({"event": "reinforcement_load_fail", "err": str(e)})
    return {}

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

    df = _feature_frame(ctx)
    if df.empty:
        return 0.0, "empty_feature_frame", "n/a", mesh

    profile = _load_profile()
    penalties = sum(profile.get(k, 0) for k in ("bad", "conflict", "regret"))
    boosts = sum(profile.get(k, 0) for k in ("strong", "profit"))
    regime = forecast_market_regime(ctx)
    regime_mod = {
        "panic": -0.30,
        "bearish": -0.20,
        "choppy": -0.10,
        "stable": 0.00,
        "bullish": 0.10,
        "trending": 0.20,
    }.get(regime, 0.0)

    raw = model.predict_proba(df)[0][1] if model else 0.0
    adjusted = raw + 0.05 * boosts - 0.05 * penalties + regime_mod
    mesh_pct = ctx["mesh_confidence"] / 100.0
    mesh_boost = 0.25 + 0.75 * mesh_pct ** 2
    final = 0.50 * adjusted + 0.50 * mesh_boost

    rationale = (
        f"ml={raw:.2f} adj={adjusted:.2f} mesh={ctx['mesh_confidence']:.1f} regime={regime} → {final:.2f}"
    )

    log_data = {
        "final": round(final, 4),
        "raw": round(raw, 4),
        "mesh": ctx["mesh_confidence"],
        "regime": regime,
        "agent_signals": mesh.get("agent_signals", {}),
        "reason": rationale
    }
    asyncio.run(log_score_breakdown_async(log_data))

    return round(final, 4), rationale, regime, mesh

async def evaluate_entry(symbol: str = "SPY", default_threshold: float | None = None, want_meta: bool = False, force_trade: bool = False) -> bool | dict:
    threshold_base = default_threshold if default_threshold is not None else ENTRY_THRESHOLD

    try:
        opt = await asyncio.to_thread(get_option_metrics, symbol)
        if isinstance(opt, list):
            opt = opt[0] if opt else {}
        if not opt:
            return False if not want_meta else {"error": "empty_option_chain", "passes": False}

        dealer = await asyncio.to_thread(get_dealer_flow_metrics, symbol) or {}
        greeks = {
            "iv": opt.get("iv", 0),
            "delta": opt.get("delta", 0),
            "gamma": opt.get("gamma", 0),
            "skew": opt.get("skew", 0),
        }

        ctx = {
            "symbol": symbol,
            "price": _price(),
            "volume": opt.get("volume", 0),
            **greeks,
            "dealer_flow": dealer.get("score", 0),
        }

        score, rationale, regime, mesh = await asyncio.to_thread(score_entry, ctx)
        threshold = REGIME_THRESHOLDS.get(regime, threshold_base)
        decision = force_trade or score >= threshold

        if decision:
            logger.info({
                "event": "entry_accepted",
                "score": round(score, 3),
                "threshold": threshold,
                "regime": regime
            })
        else:
            logger.info({
                "event": "entry_rejected",
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
            "gpt_confidence": round(score, 3),  # used as placeholder
            "gpt_reasoning": rationale,
            "greeks": greeks,
        }

        return result if want_meta else decision

    except Exception as e:
        logger.error({"event": "evaluate_entry_fail", "err": str(e)})
        print(f"[evaluate_entry] error → {e}")
        return False if not want_meta else {"error": str(e), "passes": False}

if __name__ == "__main__":
    import asyncio as aio

    async def _test():
        meta = await evaluate_entry("SPY", want_meta=True, force_trade=True)
        print("entry meta →", meta)

    aio.run(_test())
