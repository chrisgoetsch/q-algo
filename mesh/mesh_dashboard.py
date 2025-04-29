# File: mesh/mesh_dashboard.py

import os
import json
import matplotlib.pyplot as plt

AGENT_PERFORMANCE_PATH = "logs/mesh_agent_performance.json"
PLOT_OUTPUT_FOLDER = "logs/plots/"

def load_agent_performance():
    if not os.path.exists(AGENT_PERFORMANCE_PATH):
        print("[Mesh Dashboard] No agent performance file found.")
        return None
    with open(AGENT_PERFORMANCE_PATH, "r") as f:
        return json.load(f)

def plot_agent_scores(perf_data):
    agents = list(perf_data.keys())
    scores = [perf_data[agent]["score"] for agent in agents]

    plt.figure(figsize=(10, 6))
    plt.bar(agents, scores, color='skyblue')
    plt.title('Mesh Agent Score Drift')
    plt.ylabel('Score (0–100)')
    plt.xlabel('Agent')
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--')
    plt.tight_layout()

    # Save plot
    os.makedirs(PLOT_OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(PLOT_OUTPUT_FOLDER, "mesh_agent_scores.png")
    plt.savefig
