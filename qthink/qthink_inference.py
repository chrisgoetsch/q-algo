# File: qthink/qthink_inference.py

import openai
import os
from dotenv import load_dotenv
from utils.gpt_resilient_call import safe_chat_completion_request

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def generate_trade_reasoning(symbol, price, mesh_score, trigger_agents):
    """
    Generate a short focused reasoning for trade entry using QThink GPT.
    """
    prompt = (
        f"You are QThink, an elite quantitative trading assistant.\n"
        f"Symbol: {symbol}\n"
        f"Price: {price}\n"
        f"Mesh Score: {mesh_score}\n"
        f"Triggered Agents: {', '.join(trigger_agents)}\n\n"
        f"Give a 1-2 sentence justification for this trade setup."
    )

    messages = [
        {"role": "system", "content": "You are a professional trading decision assistant."},
        {"role": "user", "content": prompt}
    ]

    return safe_chat_completion_request(messages, model="gpt-4o", temperature=0.2, max_tokens=120)
