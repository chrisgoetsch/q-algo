# ─────────────────────────────────────────────────────────────────────────────
# File: core/prediction_engine.py        (v2-HF clean)
# ─────────────────────────────────────────────────────────────────────────────
"""
Directional forecast engine combining:
  • XGBoost probability
  • GPT scenario rationale (optional)

Returns a consistent dict:
    {direction, confidence, method, gpt_rationale?}
"""

from __future__ import annotations

import functools
import json
import os
from typing import Dict, Any

import joblib
import numpy as np
from dotenv import load_dotenv

from core.logger_setup import get_logger
from core.forecast_logger import log_forecast
from core.openai_safe import chat  # version-safe GPT helper

logger = get_logger(__name__)
load_dotenv()

MODEL_PATH  = "memory/predictive/model/prediction_model.pkl"
SCALER_PATH = "memory/predictive/model/feature_scaler.pkl"

# Ordered feature list used during training
FEATURE_KEYS = [
    "spy_price",
    "vix",
    "gex",
    "dex",
    "vwap_diff",
    "skew",
    "macro_flag",
    "time_of_day_bin",
]

# ---------------------------------------------------------------------------#
# Lazy-loaders                                                               #
# ---------------------------------------------------------------------------#
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

# ---------------------------------------------------------------------------#
# XGBoost probability                                                         #
# ---------------------------------------------------------------------------#
def predict_with_model(state: Dict[str, float]) -> Dict[str, Any]:
    mdl = _load_model()
    scl = _load_scaler()
    if not mdl or not scl:
        return {"error": "model_or_scaler_unavailable", "method": "xgboost"}

    try:
        X   = np.array([[state.get(k, 0.0) for k in FEATURE_KEYS]])
        X_s = scl.transform(X)
        p   = mdl.predict_proba(X_s)[0]
        direction  = "bullish" if p[1] > p[0] else "bearish"
        return {
            "direction":  direction,
            "confidence": float(max(p)),
            "method":     "xgboost",
        }
    except Exception as e:
        logger.error({"event": "model_predict_fail", "err": str(e)})
        return {"error": str(e), "method": "xgboost"}

# ---------------------------------------------------------------------------#
# GPT fallback / enrichment                                                   #
# ---------------------------------------------------------------------------#
def forecast_with_gpt(state: Dict[str, float]) -> Dict[str, Any]:
    try:
        txt = chat(json.dumps(state))
        logger.info({"event": "gpt_forecast_ok"})
        return {
            "direction":      "n/a",
            "confidence":     0.65,
            "method":         "gpt",
            "gpt_rationale":  txt,
        }
    except Exception as e:
        logger.error({"event": "gpt_forecast_fail", "err": str(e)})
        return {"error": str(e), "method": "gpt"}

# ---------------------------------------------------------------------------#
# Hybrid merge                                                                #
# ---------------------------------------------------------------------------#
def hybrid_forecast(state: Dict[str, float]) -> Dict[str, Any]:
    ml  = predict_with_model(state)
    gpt = forecast_with_gpt(state)

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
        final["gpt_rationale"] = gpt.get("gpt_rationale", "")

    try:
        log_forecast("HybridModel-v2", final, final.get("confidence", 0.5), state)
    except Exception as e:
        logger.error({"event": "forecast_log_fail", "err": str(e)})

    return final

# ---------------------------------------------------------------------------#
# CLI self-test                                                               #
# ---------------------------------------------------------------------------#
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
