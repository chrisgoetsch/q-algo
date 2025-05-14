# core/alpha_decay_tracker.py
import math
from datetime import datetime

def calculate_time_decay(entry_time: str) -> float:
    """
    Calculate normalized time decay (0 to 1) from trade entry until now.
    Assumes 0DTE trade expiring at 4:00 PM ET.
    """
    try:
        fmt = "%Y-%m-%dT%H:%M:%S"
        entry_dt = datetime.strptime(entry_time[:19], fmt)
        now = datetime.utcnow()
        market_close = entry_dt.replace(hour=20, minute=0, second=0)  # 4 PM ET = 20:00 UTC

        total_seconds = (market_close - entry_dt).total_seconds()
        elapsed_seconds = (now - entry_dt).total_seconds()
        decay = min(1.0, max(0.0, elapsed_seconds / total_seconds))
        return round(decay, 4)
    except Exception as e:
        print(f"[Alpha Decay] Error parsing entry time: {e}")
        return 0.0

def calculate_mesh_decay(mesh_confidence: float, age_minutes: float) -> float:
    """
    Decay based on time and weakening signal strength.
    """
    if mesh_confidence >= 80:
        return min(0.3, age_minutes / 240)  # slower decay
    elif mesh_confidence >= 50:
        return min(0.5, age_minutes / 180)
    else:
        return min(0.8, age_minutes / 120)
