# File: handlers/trailing_stop.py

def apply_trailing_stop(pnl: float, current_stop: float = -0.2):
    """
    Returns True if trailing stop is hit. Basic version for now.
    """
    if pnl <= current_stop:
        return True, f"Trailing stop hit at {pnl:.2f}"
    return False, "No stop hit"
