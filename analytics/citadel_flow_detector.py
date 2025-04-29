# File: analytics/citadel_flow_detector.py

import json
import os
from datetime import datetime
from core.live_price_tracker import get_current_spy_price
from utils.atomic_write import atomic_append_jsonl

CITADEL_FLOW_FOLDER = "logs/flow_signals/"
os.makedirs(CITADEL_FLOW_FOLDER, exist_ok=True)

def detect_flow_compression(spy_price=None):
    """
    Detect potential flow compression zones based on SPY price clustering.
    Placeholder logic for now: uses decimal rounding to find compression near whole numbers.
    """

    if spy_price is None:
        spy_price = get_current_spy_price()

    if spy_price is None:
        print("[Citadel Flow Detector] No SPY price available.")
        return None

    decimal_part = spy_price % 1

    compression_detected = decimal_part < 0.05 or decimal_part > 0.95

    detection_result = {
        "timestamp": datetime.utcnow().isoformat(),
        "spy_price": spy_price,
        "compression_detected": compression_detected
    }

    return detection_result

def record_flow_signal(signal_data):
    """
    Record detected flow compression signal atomically to flow logs.
    """
    if not signal_data:
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    path = os.path.join(CITADEL_FLOW_FOLDER, f"{today}_flow_signals.jsonl")
    atomic_append_jsonl(path, signal_data)

    print(f"[Citadel Flow Detector] Recorded flow signal: {signal_data}")

if __name__ == "__main__":
    signal = detect_flow_compression()
    if signal:
        record_flow_signal(signal)
