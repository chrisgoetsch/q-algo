# File: qthink/memory_compression.py

import json
import os
from datetime import datetime
import openai
from dotenv import load_dotenv
from core.utils.gpt_resilient_call import safe_chat_completion_request

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

SYNC_LOG_PATH = "logs/sync_log.jsonl"
SUMMARY_FOLDER = "logs/"
SUMMARY_FILENAME_TEMPLATE = "qthink_journal_summary_{year}-{month}.json"

# ... load_monthly_trades() and save_summary() stay same

def compress_trades(trades):
    """
    Summarize trades into key learnings using GPT.
    """
    prompt = (
        f"You are QThink, an elite trading AI.\n"
        f"Here is a list of trades:\n\n"
        f"{json.dumps(trades, indent=2)}\n\n"
        f"Analyze:\n"
        f"- What conditions led to profits?\n"
        f"- What mistakes led to losses?\n"
        f"Return JSON with 'profitable_patterns', 'losing_patterns', 'strategic_recommendations'."
    )

    messages = [
        {"role": "system", "content": "You are a quantitative trading journal summarizer."},
        {"role": "user", "content": prompt}
    ]

    summary_text = safe_chat_completion_request(messages, model="gpt-4o", temperature=0.2, max_tokens=1000)

    try:
        return json.loads(summary_text)
    except Exception as e:
        print(f"[Memory Compression] Warning: GPT returned non-JSON: {e}")
        return {"raw_summary_text": summary_text}
