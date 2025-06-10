import json, os
from pathlib import Path
from datetime import datetime

MEMORY_FILE = "qthink_memory.json"

def save_to_memory(tag: str, notes: str):
    mem = Path(MEMORY_FILE)
    history = json.loads(mem.read_text()) if mem.exists() else {}
    history[tag] = {
        "timestamp": datetime.utcnow().isoformat(),
        "notes": notes
    }
    mem.write_text(json.dumps(history, indent=2))

def retrieve_memory():
    if Path(MEMORY_FILE).exists():
        return json.loads(Path(MEMORY_FILE).read_text())
    return {}
