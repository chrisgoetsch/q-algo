# health/health_api.py
# FastAPI-based health endpoints for status, capital, and mesh.

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from core.logger_setup import logger

app = FastAPI(title="Q-ALGO Health API")

def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error({"event": "health_load_failed", "path": path, "error": str(e)})
        return None

def load_jsonl(path):
    data = []
    if not os.path.exists(path):
        return data
    try:
        with open(path, "r") as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.error({"event": "health_jsonl_parse_error", "path": path, "error": str(e)})
    except Exception as e:
        logger.error({"event": "health_load_jsonl_failed", "path": path, "error": str(e)})
    return data

@app.get("/api/status")
def api_status():
    """Overall system status and last runtime timestamp."""
    runtime = load_json(os.getenv("RUNTIME_STATE_FILE_PATH", "logs/runtime_state.json")) or {}
    return JSONResponse({"status": "ok", "runtime_state": runtime})

@app.get("/api/capital")
def api_capital():
    """Return latest capital tracker state."""
    capital = load_json(os.getenv("CAPITAL_TRACKER_PATH", "logs/capital_tracker.json")) or {}
    return JSONResponse({"status": "ok", "capital_state": capital})

@app.get("/api/mesh")
def api_mesh():
    """Return recent mesh agent logs (up to 10)."""
    mesh_logs = load_jsonl(os.getenv("MESH_LOG_PATH", "logs/mesh_logger.jsonl"))
    recent = mesh_logs[-10:]
    return JSONResponse({"status": "ok", "recent_mesh": recent})

@app.get("/api/open_trades")
def api_open_trades():
    """Return current open trades."""
    trades = load_jsonl(os.getenv("OPEN_TRADES_FILE_PATH", "logs/open_trades.jsonl"))
    return JSONResponse({"status": "ok", "open_trades": trades})

@app.get("/api/health_check")
def api_health_check():
    """Simple ping endpoint."""
    return JSONResponse({"status": "healthy"})
