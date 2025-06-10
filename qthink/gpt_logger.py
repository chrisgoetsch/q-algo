

import json
import os
from datetime import datetime

LOG_PATH = "logs/qthink_dialogs.jsonl"

def log_dialog(prompt: str, response: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)  # 🔧 Ensures 'logs/' exists
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "response": response,
        "model": "gpt-4o"
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
