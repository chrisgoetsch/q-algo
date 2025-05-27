# File: devtools/seed_reinforcement_data.py

import json
import os
import random
from datetime import datetime, timedelta

OUTPUT_PATH = "assistants/reinforcement_profile.jsonl"
AGENTS = ["q_block", "q_trap", "q_quant", "q_precision", "q_scout"]

def generate_trade(i):
    pnl = round(random.uniform(-1.0, 2.0), 2)  # Some wins, some losses
    base_price = 520 + random.uniform(-5, 5)
    entry = {
        "symbol": f"SIM_OPTION_{i}",
        "pnl": pnl,
        "mesh_confidence": round(random.uniform(60, 100), 2),
        "price": round(base_price, 2),
        "iv": round(random.uniform(0.18, 0.35), 3),
        "volume": random.randint(500000, 2000000),
        "skew": round(random.uniform(0.05, 0.3), 3),
        "delta": round(random.uniform(0.3, 0.7), 3),
        "gamma": round(random.uniform(0.05, 0.25), 3),
        "dealer_flow": round(random.uniform(-0.5, 0.5), 3),
        "mesh_score": round(random.uniform(60, 100), 2),
        "alpha_decay": round(random.uniform(0.05, 0.3), 3),
        "timestamp": (datetime.utcnow() - timedelta(minutes=i * 2)).isoformat()
    }

    for agent in AGENTS:
        entry[f"agent_{agent}"] = round(random.uniform(0.5, 1.0), 2)

    return entry

def seed_data(n=20):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "a") as f:
        for i in range(n):
            f.write(json.dumps(generate_trade(i)) + "\n")
    print(f"✅ Seeded {n} simulated trades into {OUTPUT_PATH}")

if __name__ == "__main__":
    seed_data()
