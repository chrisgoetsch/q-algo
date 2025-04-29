# prediction_summary_writer.py
# Writes summary files of model predictions for downstream audit or GPT review

import json
import datetime
from pathlib import Path

SUMMARY_PATH = Path("logs/predictions/summary.jsonl")

def write_prediction_summary(trade_id, prediction_score, model_version="v2", 
meta=None):
    """
    Writes a structured summary of an entry prediction for tracking over time.
    """
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "trade_id": trade_id,
        "prediction_score": round(prediction_score, 4),
        "model_version": model_version,
        "meta": meta or {}
    }

    try:
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[prediction_summary] Logged prediction for {trade_id}")
    except Exception as e:
        print(f"[prediction_summary] Failed to write prediction: {e}")

