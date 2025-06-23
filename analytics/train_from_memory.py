# File: analytics/train_from_memory.py

from mesh.q_0dte_memory import summarize_patterns_with_outcomes
from qthink.qthink_pattern_matcher import gpt_reflect_on_patterns
import json
from datetime import datetime
import os

REINFORCEMENT_PROFILE_PATH = "assistants/reinforcement_profile.jsonl"

def append_to_reinforcement_log(entry):
    os.makedirs(os.path.dirname(REINFORCEMENT_PROFILE_PATH), exist_ok=True)
    with open(REINFORCEMENT_PROFILE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def run_memory_training():
    summary = summarize_patterns_with_outcomes()
    if not summary:
        print("🧠 No pattern data found in memory.")
        return

    feedback = gpt_reflect_on_patterns(summary)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "q_0dte_memory",
        "feedback": feedback
    }

    append_to_reinforcement_log(entry)
    print("✅ GPT training update complete.")
    print(json.dumps(feedback, indent=2))

if __name__ == "__main__":
    run_memory_training()
