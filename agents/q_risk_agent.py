import json
import datetime

class QRisk:
    def __init__(self, current_equity: float, peak_equity: float, settings: dict):
        self.current_equity = current_equity
        self.peak_equity = peak_equity
        self.settings = settings
        self.drawdown_pct = 1 - (current_equity / peak_equity)
        self.cap_reached = self.drawdown_pct >= settings.get("drawdown_cap_pct", 0.10)
        self.response = settings.get("drawdown_response", "reduce_size")
        self.status = "safe"

    def evaluate(self):
        if self.cap_reached:
            self.status = self.response
            self.log_violation()
        return self.status

    def log_violation(self):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "q_risk_agent.py",
            "level": "CRITICAL",
            "type": "drawdown_violation",
            "equity": self.current_equity,
            "peak_equity": self.peak_equity,
            "drawdown_pct": round(self.drawdown_pct, 4),
            "response": self.response
        }
        with open("q_bus.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
