# regret_analyzer.py
# Tags regret on closed trades (early exit, missed move, etc.)

def tag_regret(entry_pnl_path, exit_pnl_path, peak_pnl):
    regret = {}
    if exit_pnl_path < peak_pnl and (peak_pnl - exit_pnl_path) > 0.2:
        regret["type"] = "early_exit"
        regret["score"] = round((peak_pnl - exit_pnl_path), 3)
    elif entry_pnl_path < -0.3 and exit_pnl_path > 0:
        regret["type"] = "recovered_late"
        regret["score"] = 0.5
    else:
        regret["type"] = "none"
        regret["score"] = 0.0
    return regret

