from agents.q_risk_agent import QRisk
from agents.q_ops_agent import token_expired

class QPreflightCheck:
    def __init__(self, mesh):
        self.mesh = mesh

    def full_check(self, current_equity, peak_equity, positions):
        # Load drawdown protection settings
        settings = {
            "drawdown_cap_pct": 0.10,
            "drawdown_response": "reduce_size"
        }

        # 1. Check Token
        if token_expired():
            print("❌ Token expired.")
            return False

        # 2. Risk Check
        risk = QRisk(current_equity, peak_equity, settings)
        if risk.evaluate() == "halt":
            print("🚨 Drawdown breach — trading halted.")
            return False

        # 3. Mesh Check
        if not self.mesh or not isinstance(self.mesh.agent_signals, dict):
            print("❌ Mesh not properly loaded.")
            return False

        print("✅ Preflight check passed.")
        return True
