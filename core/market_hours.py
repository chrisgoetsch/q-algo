# File: core/market_hours.py

from datetime import datetime, time
import pytz

def is_market_open_now() -> bool:
    """Check if the current time is during regular market hours (Eastern Time)."""
    eastern = pytz.timezone("US/Eastern")
    now_et = datetime.now(pytz.utc).astimezone(eastern).time()  # ← FIXED
    market_open = time(9, 30)
    market_close = time(16, 0)
    return market_open <= now_et <= market_close

def get_market_status_string() -> str:
    """Return a human-readable market status string."""
    return "open" if is_market_open_now() else "closed"
