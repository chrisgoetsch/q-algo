from fastapi import FastAPI
from agents.q_ops_agent import token_expired, refresh_token
from agents.q_risk_agent import QRisk
from mesh.q_signal_mesh import QSignalMesh
from core.trade_engine import run_q_algo_live
from core.q_preflight_check import QPreflightCheck
import datetime
import json

# === Q Algo System Config ===
CAPITAL_CAP = 0.20  # 20%
CURRENT_EQUITY = 3_540_000
PEAK_EQUITY = 3_920_000
CURRENT_POSITIONS = []

# === Initialize System ===
app = FastAPI()
mesh = QSignalMesh()

# === Routes for System Monitoring ===
@app.get("/")
def root():
    return {"status": "Q Algo autonomous mode", "timestamp": 
datetime.datetime.now().isoformat()}

@app.get("/status")
def status():
    return {
        "mesh_active": True,
        "trading_enabled": True,
        "capital_cap": f"{CAPITAL_CAP * 100:.0f}%",
        "token_status": "expired" if token_expired() else "valid"
    }

@app.get("/run-preflight")
def run_preflight():
    check = QPreflightCheck(mesh)
    passed = check.full_check(CURRENT_EQUITY, PEAK_EQUITY, 
CURRENT_POSITIONS)
    return {
        "preflight_passed": passed,
        "details": check.readiness
    }

# === Logging Function ===
def log_to_bus(message: str, level: str = "INFO"):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "source": "main.py",
        "level": level,
        "message": message
    }
    with open("q_bus.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

# === Launch Q Algo Autonomously on Boot ===
def launch_autonomous_q_algo():
    log_to_bus("Q Algo launching in autonomous mode.")

    if token_expired():
        log_to_bus("Token expired at launch. Refreshing...")
        refresh_token()
        log_to_bus("Token refreshed successfully.")

    check = QPreflightCheck(mesh)
    if check.full_check(CURRENT_EQUITY, PEAK_EQUITY, CURRENT_POSITIONS):
        log_to_bus("✅ Preflight check passed. Launching live execution.")
        run_q_algo_live()
    else:
        log_to_bus("❌ Preflight check failed. Trading not started.", 
level="ERROR")

# === Launch Logic ===
if __name__ == "__main__":
    launch_autonomous_q_algo()

