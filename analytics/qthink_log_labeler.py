# File: analytics/qthink_log_labeler.py

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict
from core.env_validator import validate_env
from core.resilient_request import resilient_post

# Adjust path for standalone debugging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qthink")

# Validate env
validate_env()

# Paths
QTHINK_LOG_PATH = os.getenv("QTHINK_LOG_PATH", "logs/qthink_labels.jsonl")
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")
INSIGHTS_LOG_PATH = os.getenv("INSIGHTS_LOG_PATH", "logs/qthink_insights.jsonl")
OPENAI_COMPLETION_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")

# Ensure paths exist
os.makedirs(os.path.dirname(QTHINK_LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(REINFORCEMENT_PROFILE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(INSIGHTS_LOG_PATH), exist_ok=True)

def label_exit_reason(pnl: float, decay: float, mesh_signal: str) -> str:
    reasons = []
    if mesh_signal == "exit":
        reasons.append("Mesh agents triggered exit")
    if pnl < -0.3:
        reasons.append(f"PnL dropped below -30%: {pnl:.2f}")
    if decay > 0.5:
        reasons.append(f"Alpha decay exceeded: {decay:.2f}")
    if not reasons:
        reasons.append("Exit triggered by fallback logic")
    return " | ".join(reasons)

def write_jsonl(path: str, record: Dict):
    try:
        with open(path, "a", buffering=1) as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.error({"event": "jsonl_write_failed", "path": path, "error": str(e), "record": record})

def load_reinforcement_profile() -> Dict:
    if not os.path.exists(REINFORCEMENT_PROFILE_PATH):
        return {}
    try:
        with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error({"event": "reinforcement_load_failed", "error": str(e)})
        return {}

def save_reinforcement_profile(profile: Dict):
    tmp = REINFORCEMENT_PROFILE_PATH + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(profile, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, REINFORCEMENT_PROFILE_PATH)
    except Exception as e:
        logger.error({"event": "reinforcement_save_failed", "error": str(e)})

def label_trade(trade: Dict) -> Dict:
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GPT_MODEL,
            "messages": [
                {"role": "system", "content": (
                    "You are QThink. Label this SPY 0DTE trade outcome with root cause insights. "
                    "Use formats like 'q_block:bad entry' or 'q_trap:late mesh'. "
                    "Output 1–3 labels separated by |."
                )},
                {"role": "user", "content": json.dumps(trade)}
            ],
            "max_tokens": 150
        }
        resp = resilient_post(OPENAI_COMPLETION_URL, headers=headers, json=payload)
        if not resp:
            raise RuntimeError("No response from OpenAI API")
        result = resp.json()
        choices = result.get("choices", [])
        if not choices or "message" not in choices[0]:
            raise ValueError("Malformed GPT response")
        label = choices[0]["message"]["content"].strip()
        return {"trade": trade, "label": label, "labeled_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error({"event": "trade_label_failed", "error": str(e), "trade": trade})
        return {"trade": trade, "label": None, "labeled_at": datetime.utcnow().isoformat()}

def process_and_journal(trade: Dict):
    labeled = label_trade(trade)
    write_jsonl(QTHINK_LOG_PATH, labeled)
    write_jsonl(INSIGHTS_LOG_PATH, labeled)

    profile = load_reinforcement_profile()

    labels = [l.strip() for l in (labeled["label"] or "").split("|") if l.strip()]
    if not labels:
        labels = ["unlabeled"]

    for label in labels:
        profile[label] = profile.get(label, 0) + 1

    save_reinforcement_profile(profile)
    logger.info({"event": "trade_processed", "labels": labels, "timestamp": labeled["labeled_at"]})

if __name__ == "__main__":
    sample_trade = {
        "symbol": "SPY",
        "entry_price": 420.5,
        "exit_price": 422.0,
        "quantity": 1,
        "pnl": 1.5,
        "reason": "profit_target"
    }
    process_and_journal(sample_trade)
