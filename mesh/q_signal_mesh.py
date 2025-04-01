from market.live_price_feed import get_live_price

class QSignalMesh:
    def __init__(self):
        self.agent_signals = {}
        self.mesh_score = 0.0
        self.mesh_confidence = 0.0
        self.agents = [
            "q_flow_agent",
            "q_quant_agent",
            "q_pattern_agent",
            "q_macro_agent"
        ]
        self.load_signals()

    def load_signals(self):
        # 🟢 Pull real-time market data
        price_data = get_live_price("SPY")
        price = price_data["price"]
        volume = price_data["volume"]

        # 🧠 Agent-based signal logic (placeholder logic — upgrade with whisper/flow soon)
        self.agent_signals = {
            "q_flow_agent": 1 if volume > 1500000 else 0,
            "q_quant_agent": 1 if price > 440 else 0,
            "q_pattern_agent": 0,
            "q_macro_agent": 1
        }

    def calculate_mesh(self):
        signal_sum = sum(self.agent_signals.values())
        total_agents = len(self.agent_signals)
        self.mesh_score = signal_sum
        self.mesh_confidence = round(signal_sum / total_agents, 2)

    def get_score(self):
        self.load_signals()
        self.calculate_mesh()
        return {
            "mesh_score": self.mesh_score,
            "mesh_confidence": self.mesh_confidence,
            "agent_signals": self.agent_signals
        }
