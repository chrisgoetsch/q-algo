# kill_switch.py
# Q-ALGO v2 - Reads and writes kill switch status via backend/state file

import json
import os
from pathlib import Path

KILL_SWITCH_PATH = "logs/status.json"

def read_kill_status():
    if not os.path.exists(KILL_SWITCH_PATH):
        return False
    try:
        with open(KILL_SWITCH_PATH, "r") as f:
            data = json.load(f)
            return data.get("kill_switch", False)
    except:
        return False

def write_kill_status(state: bool):
    status_file = Path(KILL_SWITCH_PATH)
    if not status_file.exists():
        status_file.write_text(json.dumps({}))

    with open(KILL_SWITCH_PATH, "r") as f:
        data = json.load(f)

    data["kill_switch"] = state

    with open(KILL_SWITCH_PATH, "w") as f:
        json.dump(data, f, indent=2)

def check_kill():
    """Used by trade_engine and position_manager to halt trading."""
    return read_kill_status()

def toggle_kill():
    """For CLI use or manual triggers."""
    state = not read_kill_status()
    write_kill_status(state)
    print(f"🚨 Kill switch {'ENABLED' if state else 'DISABLED'}")

