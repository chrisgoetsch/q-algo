# analytics/qthink_log_labeler.py
# Labels completed trades using GPT, journals labels and updates reinforcement profiles safely.

import os
import json
from datetime import datetime
from typing import Dict

from core.logger_setup import logger
from core.env_validator import validate_env
from core.resilient_request import resilient_post

# Validate critical environment on import
validate_env()

# Paths from env (with sensible defaults)
QTHINK_LOG_PATH = os.getenv("QTHINK_LOG_PATH", "logs/qthink_labels.jsonl")
REINFORCEMENT_PROFILE_PATH = os.getenv("REINFORCEMENT_PROFILE_PATH", "assistants/reinforcement_profile.json")

# Ensure log directories exist
os.makedirs(os.path.dirname(QTHINK_LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(REINFORCEMENT_PROFILE_PATH), exist_ok=True)

# GPT endpoint for labeling (example)
OPENAI_COMPLETION_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def write_jsonl(path: str, record: Dict):
    """Append a JSON line, guarding against disk errors."""
    try:
        with open(path, "a", buffering=1) as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.error({
            "event": "jsonl_write_failed",
            "path": path,
            "error": str(e),
            "record": record
        })

def load_reinforcement_profile() -> Dict:
    """Load or initialize the reinforcement profile."""
    if not os.path.exists(REINFORCEMENT_PROFILE_PATH):
        return {}
    try:
        with open(REINFORCEMENT_PROFILE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error({
            "event": "reinforcement_load_failed",
            "error": str(e)
        })
        return {}

def save_reinforcement_profile(profile: Dict):
    """Atomically save reinforcement profile."""
    tmp = REINFORCEMENT_PROFILE_PATH + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(profile, f, indent=2)
        os.replace(tmp, REINFORCEMENT_PROFILE_PATH)
    except Exception as e:
        logger.error({
            "event": "reinforcement_save_failed",
            "error": str(e)
        })

def label_trade(trade: Dict) -> Dict:
    """
    Sends trade data to GPT to generate a label.
    Returns the label data dict, or original trade on failure.
    """
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": os.getenv("GPT_MODEL", "gpt-4-turbo"),
            "messages": [
                {"role": "system", "content": "Label this trade outcome with reasons."},
                {"role": "user", "content": json.dumps(trade)}
            ],
            "max_tokens": 150
        }
        resp = resilient_post(OPENAI_COMPLETION_URL, headers=headers, json=payload)
        if not resp:
            raise RuntimeError("No response from OpenAI API")
        result = resp.json()
        label = result["choices"][0]["message"]["content"]
        return {"trade": trade, "label": label, "labeled_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error({
            "event": "trade_label_failed",
            "error": str(e),
            "trade": trade
        })
        return {"trade": trade, "label": None, "labeled_at": datetime.utcnow().isoformat()}

def process_and_journal(trade: Dict):
    """
    Full pipeline: label the trade, journal the label, and update reinforcement profile.
    """
    labeled = label_trade(trade)
    write_jsonl(QTHINK_LOG_PATH, labeled)

    # Update reinforcement memory
    profile = load_reinforcement_profile()
    key = labeled["label"] or "unlabeled"
    profile[key] = profile.get(key, 0) + 1
    save_reinforcement_profile(profile)

    logger.info({
        "event": "trade_processed",
        "label": key,
        "timestamp": labeled["labeled_at"]
    })

if __name__ == "__main__":
    # Example usage
    sample_trade = {
        "symbol": "SPY",
        "entry_price": 420.5,
        "exit_price": 422.0,
        "quantity": 1,
        "pnl": 1.5,
        "reason": "profit_target"
    }
    process_and_journal(sample_trade)
