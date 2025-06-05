# File: core/prediction_engine.py (refactored for v2)
"""Generates directional forecasts for SPY 0‑DTE using an XGBoost model and an
OpenAI‑powered scenario generator, then logs a merged forecast.

Highlights
----------
• Lazy‑loads model/scaler exactly once (module‑level cache)
• Structured JSON logging through core.logger_setup
• GPT call is optional: if OPENAI_API_KEY missing, we gracefully degrade
• `hybrid_forecast()` returns consistent schema: {direction, confidence, method, ...}
"""
from __future__ import annotations

import os, json, functools
from typing import Dict, Any

import numpy as np, joblib
from dotenv import load_dotenv

from core.logger_setup import get_logger
from core.qthink_scenario_planner import simulate_market_scenario
from core.forecast_logger import log_forecast

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Environment / paths
# ---------------------------------------------------------------------------
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

MODEL_PATH = "memory/predictive/model/prediction_model.pkl"
SCALER_PATH = "memory/predictive/model/feature_scaler.pkl"

# ---------------------------------------------------------------------------
# Lazy loaders to avoid re‑reading pickle on every call
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_model():
    if not os.path.exists(MODEL_PATH):
        logger.warning({"event": "model_missing", "path": MODEL_PATH})
        return None
    return joblib.load(MODEL_PATH)


@functools.lru_cache(maxsize=1)
def _load_scaler():
    if not os.path.exists(SCALER_PATH):
        logger.warning({"event": "scaler_missing", "path": SCALER_PATH})
        return None
    return joblib.load(SCALER_PATH)

# ---------------------------------------------------------------------------
# ML model prediction
# ---------------------------------------------------------------------------

def predict_with_model(state_vec: Dict[str, float]) -> Dict[str, Any]:
    model = _load_model()
    scaler = _load_scaler()
    if not model or not scaler:
        return {"error": "model_or_scaler_unavailable", "method": "xgboost"}
    try:
        X = np.array([list(state_vec.values())])
        Xs = scaler.transform(X)
        probs = model.predict_proba(Xs)[0]
        direction = "bullish" if probs[1] > probs[0] else "bearish"
        return {
            "direction": direction,
            "confidence": float(max(probs)),
            "method": "xgboost",
        }
    except Exception as e:
        logger.error({"event": "model_predict_fail", "err": str(e)})
        return {"error": str(e), "method": "xgboost"}

# ---------------------------------------------------------------------------
# GPT scenario forecast (placeholder – using internal simulator)
# ---------------------------------------------------------------------------

def forecast_with_gpt(state_vec: Dict[str, float]) -> Dict[str, Any]:
    if not OPENAI_KEY:
        return {"error": "no_api_key", "method": "gpt"}
    try:
        scenario = simulate_market_scenario(state_vec)
        direction = scenario.get("direction", "n/a")
        return {
            "direction": direction,
            "confidence": 0.65,
            "gpt_rationale": scenario.get("scenario"),
            "method": "gpt",
        }
    except Exception as e:
        logger.error({"event": "gpt_forecast_fail", "err": str(e)})
        return {"error": str(e), "method": "gpt"}

# ---------------------------------------------------------------------------
# Hybrid forecast – picks best available
# ---------------------------------------------------------------------------

def hybrid_forecast(state_vec: Dict[str, float]) -> Dict[str, Any]:
    ml = predict_with_model(state_vec)
    gpt = forecast_with_gpt(state_vec)

    if "error" in ml and "error" in gpt:
        final = {
            "direction": "unknown",
            "confidence": 0.5,
            "method": "fallback",
            "errors": {"ml": ml.get("error"), "gpt": gpt.get("error")},
        }
    elif "error" in ml:
        final = gpt
    else:
        final = ml
        if "gpt_rationale" in gpt:
            final["gpt_rationale"] = gpt["gpt_rationale"]

    # Persist forecast
    try:
        log_forecast("HybridModel-v2", final, final.get("confidence", 0.5), state_vec)
    except Exception as e:
        logger.error({"event": "forecast_log_fail", "err": str(e)})

    return final

# ---------------------------------------------------------------------------
# CLI self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_state = {
        "spy_price": 436.12,
        "vix": 16.2,
        "gex": -8e8,
        "dex": 9e8,
        "vwap_diff": -0.15,
        "skew": 1.10,
        "macro_flag": 0,
        "time_of_day_bin": 2,
    }
    print(json.dumps(hybrid_forecast(test_state), indent=2))
