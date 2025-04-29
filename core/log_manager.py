# core/log_manager.py
# Archives JSONL/log files daily and resets them safely.

import os
import gzip
import shutil
from datetime import datetime

from core.logger_setup import logger

LOG_DIR = os.getenv("LOG_DIR", "logs")
ARCHIVE_DIR = os.path.join(LOG_DIR, "archive")
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
            # Skip app.log (handled by TimedRotatingFileHandler)
            if fname == "app.log":
                continue
            try:
                # Archive name: filename.YYYY-MM-DD.gz
                mod_date = datetime.now().strftime("%Y-%m-%d")
                archive_name = f"{fname}.{mod_date}.gz"
                dest = os.path.join(ARCHIVE_DIR, archive_name)
                with open(path, "rb") as src, gzip.open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                # Truncate original
                open(path, "w").close()
                logger.info({"event": "log_rotated", "file": fname, "archive": archive_name})
            except Exception as e:
                logger.error({"event": "log_rotate_failed", "file": fname, "error": str(e)})
