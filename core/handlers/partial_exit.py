# File: handlers/partial_exit.py

def apply_partial_exit(pnl: float, quantity: int):
    """
    Apply partial exits at predefined profit targets.
    """
    if pnl >= 1.0:
        return quantity, "Full exit at 100%+"
    elif pnl >= 0.5:
        return max(1, quantity // 2), "50% PnL, partial exit"
    return 0, "No partial exit triggered"
