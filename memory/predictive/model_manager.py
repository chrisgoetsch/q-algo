# model_manager.py
# Handles loading, checking, and updating predictive models for 
Q-Forecaster

import os
import joblib
from pathlib import Path

MODEL_DIR = Path("memory/predictive/model")
MODEL_PATH = MODEL_DIR / "prediction_model.pkl"
SCALER_PATH = MODEL_DIR / "feature_scaler.pkl"

_loaded_model = None
_loaded_scaler = None

def load_model():
    global _loaded_model
    if _loaded_model is None or not MODEL_PATH.exists():
        _loaded_model = joblib.load(MODEL_PATH)
    return _loaded_model

def load_scaler():
    global _loaded_scaler
    if _loaded_scaler is None or not SCALER_PATH.exists():
        _loaded_scaler = joblib.load(SCALER_PATH)
    return _loaded_scaler

def model_exists():
    return MODEL_PATH.exists() and SCALER_PATH.exists()

def reload():
    """Manually reset the model + scaler cache."""
    global _loaded_model, _loaded_scaler
    _loaded_model = None
    _loaded_scaler = None
    return load_model(), load_scaler()

if __name__ == "__main__":
    if model_exists():
        model, scaler = reload()
        print("✅ Model and scaler loaded successfully.")
    else:
        print("❌ No model found. Run `train_predictive_model.py` first.")

