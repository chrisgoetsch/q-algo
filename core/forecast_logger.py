# File: core/forecast_logger.py

import os
import json
from datetime import datetime

LOG_PATH = os.getenv("FORECAST_LOG_PATH", "logs/forecast_log.jsonl")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log_forecast(model_name: str, forecast: dict, confidence: float, context: dict = None):
    """
    Append a single forecast event with metadata.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model_name,
        "forecast": forecast,
        "confidence": confidence,
        "context": context or {}
    }
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"✅ Forecast logged: {model_name} @ {confidence:.2f}")
    except Exception as e:
        print(f"🛑 Failed to log forecast: {e}")
