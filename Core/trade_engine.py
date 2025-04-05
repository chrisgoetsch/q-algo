from mesh.q_signal_mesh import QSignalMesh
from core.q_preflight_check import QPreflightCheck
from agents.whisper_agent import WhisperAgent
from agents.flow_agent import FlowAgent
import json
import datetime

class TradeEngine:
    def __init__(self):
        self.mesh = QSignalMesh()
        self.preflight = QPreflightCheck(self.mesh)
        self.whisper = WhisperAgent()
        self.flow = FlowAgent()
        self.capital_cap = 0.20  # 20% live capital limit

    def run(self, current_equity, peak_equity, positions):
        print("🚀 Starting Q Algo trade loop...")

        if not self.preflight.full_check(current_equity, peak_equity, positions):
            print("❌ Trade blocked by preflight check.")
            return

        mesh_data = self.mesh.get_score()
        confidence = mesh_data["mesh_confidence"]
        tier = self.determine_tier(confidence)

        if tier == 0:
            print("⚠️ No trade: Mesh confidence too low.")
            return

        # 🧠 Agent coordination
        whisper_signal = self.whisper.detect()
        flow_signal = self.flow.pressure()

        if whisper_signal == 0:
            print("🔇 Whisper says wait.")
            return

        if flow_signal == "sell_pressure" and whisper_signal == 1:
            print("🚫 Flow pressure contradicts long entry. Aborting.")
            return

        position_size = self.calculate_position_size(current_equity, tier)

        # 📝 Log the decision
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "confidence": confidence,
            "tier": tier,
            "position_size": position_size,
            "whisper": whisper_signal,
            "flow": flow_signal,
            "agent_signals": mesh_data["agent_signals"],
            "action": "PLACE_ORDER"
        }

        with open("q_bus.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"✅ Executing Tier {tier} trade with size: {position_size}")

    def determine_tier(self, confidence):
        if confidence >= 0.90:
            return 1
        elif confidence >= 0.70:
            return 2
        elif confidence >= 0.50:
            return 3
        return 0

    def calculate_position_size(self, equity, tier):
        base = equity * self.capital_cap
        if tier == 1:
            return round(base)
        elif tier == 2:
            return round(base * 0.6)
        elif tier == 3:
            return round(base * 0.35)
        return 0
