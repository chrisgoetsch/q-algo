# File: analytics/regime_forecaster.py

import os
import json
from datetime import datetime
from core.resilient_request import resilient_post

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_COMPLETION_URL = "https://api.openai.com/v1/chat/completions"
FORECAST_LOG_PATH = os.getenv("FORECAST_LOG_PATH", "logs/forecast_log.jsonl")

os.makedirs(os.path.dirname(FORECAST_LOG_PATH), exist_ok=True)

def forecast_market_regime(context: dict) -> str:
    """
    Use GPT to forecast the current market regime based on context.
    Returns a one-word regime label.
    """
    if not OPENAI_API_KEY:
        return "unknown"

    prompt = f"""
    Given the following market snapshot:
    {json.dumps(context, indent=2)}

    Classify the regime in one word: bullish, bearish, volatile, stable, trending, panic, choppy.
    """

    payload = {
        "model": os.getenv("GPT_MODEL", "gpt-4-turbo"),
        "messages": [
            {"role": "system", "content": "You are a financial regime classifier."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 10
    }

    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        response = resilient_post(OPENAI_COMPLETION_URL, headers=headers, json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"].strip().lower()
    except Exception as e:
        print(f"🛑 GPT forecast failed: {e}")
        return "unknown"

def log_forecast(context: dict, regime: str):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "regime": regime,
        "context": context
    }
    with open(FORECAST_LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"✅ Forecast logged: {regime}")

if __name__ == "__main__":
    test_context = {
        "vix": 16.5,
        "momentum": "rising",
        "mesh_confidence": 0.7,
        "capital_pressure": 0.2
    }
    regime = forecast_market_regime(test_context)
    log_forecast(test_context, regime)
