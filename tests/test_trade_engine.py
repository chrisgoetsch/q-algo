# test_trade_engine.py
# Confirms mesh, model, and core logic run to entry point

from core.mesh_router import get_mesh_signal
from core.entry_learner import build_entry_features, score_entry

def test_mesh_signal():
    signal = get_mesh_signal("SPY")
    assert "score" in signal
    assert signal["score"] >= 0.0

def test_entry_pipeline():
    signal = get_mesh_signal("SPY")
    features = build_entry_features(signal)
    score = score_entry(features)
    assert 0.0 <= score <= 1.0

