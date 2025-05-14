# File: training_data/reinforcement_profile_updater.py

import os
import json
from datetime import datetime

JOURNAL_PATH = "logs/qthink_journal_summary.json"
PROFILE_PATH = "assistants/reinforcement_profile.json"

def load_journal():
    if not os.path.exists(JOURNAL_PATH):
        print("❌ Journal summary not found.")
        return []
    with open(JOURNAL_PATH, "r") as f:
        return json.load(f)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_profile(profile):
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"✅ Reinforcement profile updated at {PROFILE_PATH}")

def extract_threshold(text):
    """
    Look for lines like:
    'recommended threshold around 0.6'
    or 'exit when decay exceeds 0.62'
    """
    import re
    matches = re.findall(r"(?:around|above|exceeds|greater than)?\s*0\.\d{1,3}", text)
    values = [float(x.strip()) for x in matches if "0." in x]
    if values:
        return round(sum(values) / len(values), 3)
    return None

def update_reinforcement_profile():
    journal = load_journal()
    profile = load_profile()

    decay_thresholds = []
    for entry in journal:
        if entry["type"] == "exit_threshold_analysis":
            threshold = extract_threshold(entry["summary"])
            if threshold:
                decay_thresholds.append(threshold)

    if not decay_thresholds:
        print("⚠️ No thresholds found in GPT summaries.")
        return

    avg_threshold = round(sum(decay_thresholds) / len(decay_thresholds), 3)
    profile["suggested_exit_decay"] = avg_threshold
    profile["last_updated"] = datetime.utcnow().isoformat()

    save_profile(profile)
    print(f"🧠 GPT-derived exit decay threshold: {avg_threshold}")

if __name__ == "__main__":
    update_reinforcement_profile()
