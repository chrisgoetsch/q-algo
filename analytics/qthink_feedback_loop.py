# File: analytics/qthink_feedback_loop.py

import os
import json
import requests
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")
INSIGHTS_LOG_PATH = "logs/qthink_insights.jsonl"
REINFORCEMENT_PROFILE_PATH = "training_data/reinforcement_profile.json"

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer " + OPENAI_API_KEY,
    "Content-Type": "application/json"
}

def load_reinforcement_profile():
    if not os.path.exists(REINFORCEMENT_PROFILE_PATH):
        return {}
    try:
        with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def save_reinforcement_profile(profile):
    try:
        tmp = REINFORCEMENT_PROFILE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(profile, f, indent=2)
        os.replace(tmp, REINFORCEMENT_PROFILE_PATH)
    except Exception as e:
        print(f"❌ Failed to save reinforcement profile: {e}")

def log_insight(record):
    try:
        with open(INSIGHTS_LOG_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to write GPT insight: {e}")

def label_trade_with_gpt(trade):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a quant strategy reviewer. "
                "Label the following trade with explanations of success or failure. "
                "Use simple labels like 'profit_target', 'mesh_conflict', 'bad_entry', 'drawdown_exit', "
                "'alpha_decay', or 'missed_signal'."
            )
        },
        {
            "role": "user",
            "content": json.dumps(trade)
        }
    ]
    payload = {
        "model": GPT_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 150
    }

    try:
        response = requests.post(OPENAI_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        gpt_output = response.json()
        label = gpt_output["choices"][0]["message"]["content"].strip()
        return label
    except Exception as e:
        print(f"❌ GPT labeling failed: {e}")
        return "unlabeled"

def process_trade_for_learning(trade):
    label = label_trade_with_gpt(trade)
    timestamp = datetime.utcnow().isoformat()

    log_entry = {
        "timestamp": timestamp,
        "trade": trade,
        "label": label
    }

    log_insight(log_entry)

    profile = load_reinforcement_profile()
    label_terms = [l.strip() for l in label.split("|")]

    for term in label_terms:
        profile[term] = profile.get(term, 0) + 1

    save_reinforcement_profile(profile)
    print(f"🧠 GPT labeled trade: {label}")
