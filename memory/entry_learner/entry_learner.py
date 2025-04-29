# entry_learner.py
# Entry score calculator using trained model

import joblib
import numpy as np
import os

MODEL_PATH = "models/entry_model.pkl"
SCALER_PATH = "models/entry_scaler.pkl"

def load_model():
    try:
        return joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"[entry_learner] Failed to load model: {e}")
        return None

def load_scaler():
    try:
        return joblib.load(SCALER_PATH)
    except Exception as e:
        print(f"[entry_learner] Failed to load scaler: {e}")
        return None

def build_entry_features(signal):
    """
    Extracts numeric features from signal for ML prediction.
    """
    return np.array([
        signal.get("score", 0),
        signal.get("iv_rank", 0),
        signal.get("dealer_position", 0),
        signal.get("skew", 0),
        signal.get("gex", 0)
    ]).reshape(1, -1)

def score_entry(features):
    model = load_model()
    scaler = load_scaler()
    if not model or not scaler:
        print("[entry_learner] Fallback score used (0.5)")
        return 0.5
    try:
        scaled = scaler.transform(features)
        return float(model.predict_proba(scaled)[0][1])
    except Exception as e:
        print(f"[entry_learner] Scoring error: {e}")
        return 0.5

