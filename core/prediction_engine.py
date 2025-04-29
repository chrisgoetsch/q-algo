# prediction_engine.py
# Combines XGBoost + GPT to forecast SPY 0DTE direction + action

import os
import json
import joblib
import openai
import numpy as np
from dotenv import load_dotenv
from forecast_logger import log_forecast
from qthink_scenario_planner import simulate_market_scenario

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL_PATH = "memory/predictive/model/prediction_model.pkl"
SCALER_PATH = "memory/predictive/model/feature_scaler.pkl"

def predict_with_model(state_vector: dict) -> dict:
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        feature_vector = np.array([list(state_vector.values())])
        features_scaled = scaler.transform(feature_vector)
        probs = model.predict_proba(features_scaled)[0]
        direction = "bullish" if probs[1] > probs[0] else "bearish"
        return {
            "direction": direction,
            "confidence": float(max(probs)),
            "method": "xgboost"
        }
    except Exception as e:
        return {"error": f"Model failure: {e}", "method": "xgboost"}

def forecast_with_gpt(state_vector: dict) -> dict:
    try:
        result = simulate_market_scenario(state_vector)
        return {
            "direction": "n/a",
            "confidence": 0.65,
            "gpt_rationale": result.get("scenario"),
            "method": "gpt"
        }
    except Exception as e:
        return {"error": str(e), "method": "gpt"}

def hybrid_forecast(state_vector: dict) -> dict:
    ml_result = predict_with_model(state_vector)
    gpt_result = forecast_with_gpt(state_vector)

    # Combine or fallback
    if "error" in ml_result:
        final = gpt_result
    else:
        final = ml_result
        final["gpt_rationale"] = gpt_result.get("gpt_rationale")

    log_forecast(state_vector, final)
    return final

if __name__ == "__main__":
    test_state = {
        "spy_price": 436.12,
        "vix": 16.2,
        "gex": -800000000,
        "dex": 900000000,
        "vwap_diff": -0.15,
        "skew": 1.10,
        "macro_flag": 0,
        "time_of_day_bin": 2
    }
    forecast = hybrid_forecast(test_state)
    print(json.dumps(forecast, indent=2))

