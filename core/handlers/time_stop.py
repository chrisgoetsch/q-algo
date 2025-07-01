# File: handlers/time_stop.py

def apply_time_stop(minutes_alive: int, threshold: int = 45):
    """
    Exit if trade has been alive too long without sufficient gain.
    """
    if minutes_alive >= threshold:
        return True, f"Time-based exit triggered after {minutes_alive}m"
    return False, "Time stop not reached"
