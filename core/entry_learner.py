# File: core/entry_learner.py

import os
import pandas as pd
import joblib
import json
import numpy as np
from analytics.regime_forecaster import forecast_market_regime
from core.mesh_router import get_mesh_signal
from datetime import datetime
from polygon.polygon_rest import get_option_metrics, get_dealer_flow_metrics
import asyncio
from polygon.websocket_manager import get_price

MODEL_PATH = "core/models/entry_model.pkl"
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
SCORE_LOG_PATH = os.getenv("SCORE_LOG_PATH", "logs/qthink_score_breakdown.jsonl")
MODEL_VERSION = "entry-model-v1.0"

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("✅ ML entry model loaded.")
else:
    model = None
    print("⚠️ Warning: entry_model.pkl not found. score_entry will default to zero scoring.")

def get_model_version():
    return MODEL_VERSION

def load_reinforcement_profile():
    if not os.path.exists(REINFORCEMENT_PROFILE_PATH):
        return {}
    try:
        with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load reinforcement profile: {e}")
        return {}

def build_entry_features(context):
    keys = ["price", "iv", "volume", "skew", "delta", "gamma", "dealer_flow",
            "mesh_confidence", "mesh_score", "alpha_decay"]
    features = {k: float(context.get(k, 0)) for k in keys}
    agent_signals = context.get("agent_signals", {})
    for agent, score in agent_signals.items():
        features[f"agent_{agent}"] = score
    return features

async def log_score_breakdown_async(log_data):
    os.makedirs(os.path.dirname(SCORE_LOG_PATH), exist_ok=True)
    log_data["timestamp"] = datetime.utcnow().isoformat()
    log_data["model_version"] = MODEL_VERSION
    log_data = {
        k: float(v) if isinstance(v, (np.float32, np.float64)) else v
        for k, v in log_data.items()
    }
    try:
        async with asyncio.to_thread(open, SCORE_LOG_PATH, "a") as f:
            await asyncio.to_thread(f.write, json.dumps(log_data) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to log score breakdown: {e}")

def score_entry(context):
    mesh_result = get_mesh_signal(context)
    context["mesh_confidence"] = mesh_result.get("score", 0)
    context["agent_signals"] = mesh_result.get("agent_signals", {})
    context["mesh_score"] = context.get("mesh_confidence", 0)
    context["alpha_decay"] = context.get("alpha_decay", 0.1)

    features = build_entry_features(context)
    df = pd.DataFrame([features]).astype(float)

    profile = load_reinforcement_profile()
    mesh_score = context["mesh_confidence"]
    label_penalties = sum([profile.get(k, 0) for k in ["bad entry", "mesh conflict", "regret"]])
    label_boosts = sum([profile.get(k, 0) for k in ["strong signal", "profit target"]])
    suggested_exit_decay = profile.get("suggested_exit_decay", 0.6)

    regime = forecast_market_regime(context)
    context["regime"] = regime
    regime_adjust = {
        "panic": -0.3,
        "bearish": -0.2,
        "choppy": -0.1,
        "stable": 0.0,
        "bullish": 0.1,
        "trending": 0.2
    }
    regime_mod = regime_adjust.get(regime, 0.0)

    if model:
        try:
            raw_score = model.predict_proba(df)[0][1]
            adjusted_score = raw_score + (0.05 * label_boosts) - (0.05 * label_penalties) + regime_mod

            if suggested_exit_decay < 0.5:
                adjusted_score += 0.05
            elif suggested_exit_decay > 0.65:
                adjusted_score -= 0.05

            final_score = (0.6 * adjusted_score) + (0.4 * (mesh_score / 100))

            rationale = f"ML: {raw_score:.2f}, Adjusted: {adjusted_score:.2f}, Mesh: {mesh_score:.2f}, Regime: {regime}, Final: {final_score:.2f}"

            asyncio.create_task(log_score_breakdown_async({
                "features": features,
                "mesh_score": mesh_score,
                "raw_score": round(raw_score, 4),
                "adjusted_score": round(adjusted_score, 4),
                "final_score": round(final_score, 4),
                "regime": regime,
                "rationale": rationale
            }))

            return round(final_score, 4), rationale
        except Exception as e:
            print(f"⚠️ Error scoring entry: {e}")
            return 0.0, "Model error"
    else:
        return 0.0, f"No ML model loaded | Regime: {regime}"

async def evaluate_entry(symbol="SPY", threshold=0.6):
    try:
        price = get_price("SPY")
        option_data = await asyncio.to_thread(get_option_metrics, symbol)
        dealer_data = await asyncio.to_thread(get_dealer_flow_metrics, symbol)

        context = {
            "symbol": symbol,
            "price": float(price),
            "iv": option_data.get("iv", 0),
            "volume": option_data.get("volume", 0),
            "skew": option_data.get("skew", 0),
            "delta": option_data.get("delta", 0),
            "gamma": option_data.get("gamma", 0),
            "dealer_flow": dealer_data.get("score", 0) if dealer_data else 0
        }

        score, rationale = await asyncio.to_thread(score_entry, context)
        print(f"[Entry Learner] Entry score: {score:.4f} | Threshold: {threshold:.2f} | Rationale: {rationale}")
        return score >= threshold

    except Exception as e:
        print(f"[Entry Learner] Failed to evaluate entry for {symbol}: {e}")
        return False
