# File: core/logger_setup.py  (refactored)
"""Central JSON logging utility for Q‑ALGO v2

Key upgrades
------------
• Log level configurable via `LOG_LEVEL` env var (default INFO)
• Prevents duplicate handlers when modules reload this file
• Console and rotating‑file handlers share the same JSON format
• Helper `get_logger(__name__)` returns a child logger for modules
• All loggers write in UTC with ISO‑8601 timestamps
"""
from __future__ import annotations

import os, json, logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
from typing import Dict, Any

# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Merge extra kwargs passed via logger.info({…}) style
        if isinstance(record.args, dict):
            payload.update(record.args)
            record.args = ()  # prevent logging lib from interpolating
        return json.dumps(payload)

# ---------------------------------------------------------------------------
# Root logger setup (called once on import)
# ---------------------------------------------------------------------------

_LOG_DIR = os.getenv("LOG_DIR", "logs")
_LOG_FILE = os.getenv("LOG_FILE", "app.log")
_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

os.makedirs(_LOG_DIR, exist_ok=True)

_root = logging.getLogger()  # root logger
if not _root.handlers:  # avoid duplicate handlers on reload
    _root.setLevel(_LEVEL)

    fmt = JsonFormatter()

    # File handler – rotates at midnight, keeps 7 days
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(_LOG_DIR, _LOG_FILE),
        when="midnight",
        backupCount=7,
        utc=True,
    )
    file_handler.setFormatter(fmt)
    _root.addHandler(file_handler)

    # Console handler (STDOUT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    _root.addHandler(console_handler)

# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger with propagated settings."""
    return logging.getLogger(name)

# Default export for simple modules: `from core.logger_setup import logger`
logger = get_logger("qalgo")
