# ✅ Updated: health_api.py with fixed sys.path for core module resolution

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from core.logger_setup import logger
import json

app = FastAPI()

@app.get("/health")
def health_check():
    try:
        # Dummy check logic — replace with actual runtime checks
        status = {
            "status": "ok",
            "mesh": "active",
            "trading": "ready"
        }
        logger.info({"event": "health_check", "status": status})
        return status

    except Exception as e:
        logger.error({"event": "health_check_fail", "error": str(e)})
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/runtime")
def get_runtime_state():
    try:
        with open("logs/runtime_state.json", "r") as f:
            state = json.load(f)
        return state
    except Exception as e:
        logger.error({"event": "runtime_state_fail", "error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to load runtime state")
