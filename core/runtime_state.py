# File: core/runtime_state.py

import os
import json
from datetime import datetime

RUNTIME_STATE_PATH = os.getenv("RUNTIME_STATE_PATH", "logs/runtime_state.json")

def load_runtime_state() -> dict:
    if not os.path.exists(RUNTIME_STATE_PATH):
        return {}
    try:
        with open(RUNTIME_STATE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load runtime state: {e}")
        return {}

def update_runtime_state(updates: dict):
    state = load_runtime_state()
    state.update(updates)
    state["last_updated"] = datetime.utcnow().isoformat()
    try:
        with open(RUNTIME_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        print(f"📘 Runtime state updated: {updates}")
    except Exception as e:
        print(f"❌ Failed to update runtime state: {e}")
