# core/logger_setup.py
# Sets up JSON-formatted, rotating logs for resilience and audit

import os
import logging
from logging.handlers import TimedRotatingFileHandler
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(log_dir="logs", log_file="app.log"):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Rotating handler: new file at midnight, keep 7 days
    handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, log_file),
        when="midnight",
        backupCount=7,
        utc=True,
    )
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    # Console output in same JSON format
    console = logging.StreamHandler()
    console.setFormatter(JsonFormatter())
    logger.addHandler(console)

    return logger

# Initialize root logger on import
logger = setup_logging()

def atomic_append_json(filepath, line_data):
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(line_data) + "\n")
    except Exception as e:
        print(f"❌ Failed to write mesh signal log: {e}")
