# test_entry_learner.py
# Validates that entry model loads and returns a probability

from core.entry_learner import load_entry_model, score_entry

def test_model_loads():
    model = load_entry_model()
    assert model is not None

def test_model_prediction_format():
    sample = {
        "gex": -1.2,
        "dex": 0.4,
        "iv": 0.25,
        "skew": -0.3,
        "oi_call_ratio": 2.1,
        "entry_score": 0.7
    }
    score = score_entry(sample)
    assert 0.0 <= score <= 1.0

