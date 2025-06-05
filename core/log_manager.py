# File: core/log_manager.py  (refactored)
"""Utility to rotate and archive JSON/JSONL log files nightly.

Highlights
----------
• Uses the unified `core.logger_setup` JSON logger (no bare prints)
• Archives into `logs/archive/<filename>.<YYYY‑MM‑DD>.gz` (UTC date)
• Skips today's file if it was already archived (idempotent)
• Provides `rotate_logs()` plus a granular `rotate_file(path)` API
• Mesh‑signal writer upgraded to use the same append helper and logger
"""
from __future__ import annotations

import os, gzip, shutil, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
ARCHIVE_DIR = LOG_DIR / "archive"
MESH_LOG_PATH = Path(os.getenv("MESH_LOG_PATH", LOG_DIR / "mesh_log.jsonl"))

EXTENSIONS: set[str] = {".jsonl", ".json"}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _archive_name(src: Path) -> Path:
    return ARCHIVE_DIR / f"{src.name}.{_utc_today()}.gz"


def _compress_to_gz(src: Path, dest: Path):
    with src.open("rb") as f_in, gzip.open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

# ---------------------------------------------------------------------------
# Log rotation API
# ---------------------------------------------------------------------------

def rotate_file(path: Path):
    """Compress *path* into archive dir and truncate the original."""
    if not path.exists() or path.stat().st_size == 0:
        return  # nothing to do
    dest = _archive_name(path)
    if dest.exists():
        logger.info({"event": "log_already_archived", "file": path.name})
        return
    try:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        _compress_to_gz(path, dest)
        path.write_text("")  # truncate
        logger.info({"event": "log_rotated", "file": path.name, "archive": dest.name})
    except Exception as e:
        logger.error({"event": "log_rotate_fail", "file": path.name, "err": str(e)})


def rotate_logs():
    """Rotate all JSON/JSONL logs in LOG_DIR except the main app.log."""
    for fp in LOG_DIR.iterdir():
        if fp.suffix.lower() in EXTENSIONS and fp.name != "app.log":
            rotate_file(fp)

# ---------------------------------------------------------------------------
# Mesh‑signal logging
# ---------------------------------------------------------------------------

def write_mesh_log(entry: dict):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        **entry,
    }
    try:
        MESH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with MESH_LOG_PATH.open("a") as fh:
            fh.write(json.dumps(record) + "\n")
        logger.info({"event": "mesh_log_write", "path": str(MESH_LOG_PATH)})
    except Exception as e:
        logger.error({"event": "mesh_log_write_fail", "err": str(e)})

# ---------------------------------------------------------------------------
# CLI self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    write_mesh_log({"test": "hello"})
    rotate_logs()
    print("✨ log_manager self‑test complete.")
