# test_signal_scoring.py
# Verifies adaptive scoring using mesh_config.json

from core.signal_scoring import score_signal

def test_score_signal_scaling():
    signal = {
        "agent": "q_quant",
        "confidence": 0.75,
        "score": 0.8
    }
    final_score = score_signal(signal)
    assert final_score > 0.0 and final_score <= 1.5

