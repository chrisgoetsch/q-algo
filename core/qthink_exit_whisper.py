# File: core/qthink_exit_whisper.py

import openai
import os
from dotenv import load_dotenv
from utils.gpt_resilient_call import safe_chat_completion_request

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def generate_exit_reasoning(symbol, pnl_percentage, exit_trigger_reason):
    """
    Generate GPT-powered brief explanation for why an exit occurred.
    """
    prompt = (
        f"You are QThink, an elite options exit strategist.\n"
        f"Symbol: {symbol}\n"
        f"PnL Percentage: {pnl_percentage:.2f}%\n"
        f"Exit Trigger: {exit_trigger_reason}\n\n"
        f"Summarize why this exit makes sense in 1-2 clear sentences."
    )

    messages = [
        {"role": "system", "content": "You are a professional trading exit strategist."},
        {"role": "user", "content": prompt}
    ]

    return safe_chat_completion_request(messages, model="gpt-4o", temperature=0.2, max_tokens=120)
