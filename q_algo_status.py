from agents.q_ops_agent import token_expired
from mesh.q_signal_mesh import QSignalMesh
from core.q_preflight_check import QPreflightCheck
import json
import datetime

# Settings
CURRENT_EQUITY = 3_540_000
PEAK_EQUITY = 3_920_000
CAPITAL_CAP = 0.20
POSITIONS = []

# Load Mesh
mesh = QSignalMesh()

# Run Checks
status_report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "token_valid": not token_expired(),
    "mesh_initialized": isinstance(mesh, QSignalMesh),
    "capital_cap": f"{CAPITAL_CAP * 100:.0f}%",
    "equity": CURRENT_EQUITY,
    "peak_equity": PEAK_EQUITY,
    "drawdown_pct": round(1 - CURRENT_EQUITY / PEAK_EQUITY, 4),
    "preflight_passed": False,
    "is_ready_to_trade": False
}

# Run preflight
check = QPreflightCheck(mesh)
passed = check.full_check(CURRENT_EQUITY, PEAK_EQUITY, POSITIONS)
status_report["preflight_passed"] = passed
status_report["is_ready_to_trade"] = passed and status_report["token_valid"]

# Log to bus
status_report["source"] = "q_algo_status.py"
status_report["type"] = "diagnostic_check"

with open("q_bus.jsonl", "a") as f:
    f.write(json.dumps(status_report) + "\n")

# Output to terminal
print("\n📡 Q ALGO STATUS REPORT")
for key, val in status_report.items():
    print(f"{key}: {val}")
