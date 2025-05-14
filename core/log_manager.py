# File: core/log_manager.py
# Archives JSONL/log files daily and resets them safely.

import os
import gzip
import shutil
import json
from datetime import datetime

try:
    from core.logger_setup import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("fallback")

LOG_DIR = os.getenv("LOG_DIR", "logs")
ARCHIVE_DIR = os.path.join(LOG_DIR, "archive")
MESH_LOG_PATH = os.getenv("MESH_LOG_PATH", "logs/mesh_log.jsonl")

# Extensions to rotate
JSONL_EXTENSIONS = {".jsonl", ".json"}

def rotate_logs():
    """
    For each file in LOG_DIR with a matching extension,
    compress yesterday's content into archive and truncate the file.
    """
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    for fname in os.listdir(LOG_DIR):
        ext = os.path.splitext(fname)[1]
        if ext in JSONL_EXTENSIONS:
            path = os.path.join(LOG_DIR, fname)
            if fname == "app.log":
                continue
            try:
                mod_date = datetime.now().strftime("%Y-%m-%d")
                archive_name = f"{fname}.{mod_date}.gz"
                dest = os.path.join(ARCHIVE_DIR, archive_name)
                with open(path, "rb") as src, gzip.open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                open(path, "w").close()
                logger.info({"event": "log_rotated", "file": fname, "archive": archive_name})
            except Exception as e:
                logger.error({"event": "log_rotate_failed", "file": fname, "error": str(e)})

def write_mesh_log(entry: dict):
    """
    Write a structured mesh log event to logs/mesh_log.jsonl
    """
    os.makedirs(os.path.dirname(MESH_LOG_PATH), exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        **entry
    }
    try:
        with open(MESH_LOG_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")
        print(f"🧠 Mesh log entry written: {record}")
    except Exception as e:
        print(f"🛑 Failed to write mesh log: {e}")
        logger.error({"event": "mesh_log_write_failed", "error": str(e), "record": record})
