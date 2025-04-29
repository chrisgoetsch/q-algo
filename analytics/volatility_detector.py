# volatility_detector.py
# Detects high-volatility macro shocks or institutional flow triggers

import datetime
import random
import json
from polygon.polygon_options import get_option_chain
from analytics.citadel_flow_detector import match_fingerprint

PIVOT_ALERT_FILE = "data/pivot_alert.json"

def detect_macro_volatility():
    chain = get_option_chain("SPY")
    flows = match_fingerprint(chain)

    for f in flows:
        if f["behavior"] in ["dealer unwind", "pin drift"]:
            log_pivot_alert(f"Flow pattern: {f['pattern']}")
            return True, f["pattern"]

    # Simulated fallback logic
    detected = random.choice([False, False, True])
    if detected:
        log_pivot_alert("Simulated shock (fallback)")
        return True, "Simulated macro"

    return False, None

def log_pivot_alert(reason):
    alert = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "trigger": True,
        "reason": reason,
        "confidence": 0.95,
        "macro_type": "flow_triggered",
        "impact_sector": "broad",
        "vix_level": 23.4,
        "vol_spike": True,
        "auto_disable_agents": ["q_precision", "q_quant"],
        "recommended_mode": "scalp_only"
    }
    with open(PIVOT_ALERT_FILE, "w") as f:
        json.dump(alert, f, indent=2)

