# File: core/gpt_exit_analyzer.py

import os
import asyncio
import aiohttp
from datetime import datetime
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")
GPT_MODEL_VERSION = "gpt-exit-v1.0"
DIALOG_LOG_PATH = "logs/qthink_dialogs.jsonl"

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def get_gpt_version():
    return GPT_MODEL_VERSION

async def analyze_exit_with_gpt(position_context: dict, trade_id: str = "n/a") -> dict:
    prompt = f"""
You are QThink, an exit strategy advisor for an AI trading system.
Analyze the following trade context and decide whether to hold, partially exit, or fully exit the trade.

Respond in JSON format:
{{
  "signal": "hold" | "scale_out" | "exit",
  "confidence": float (0.0–1.0),
  "rationale": string
}}

Trade Context:
{json.dumps(position_context, indent=2)}
"""

    body = {
        "model": GPT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise, data-driven exit strategist."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=body) as resp:
                data = await resp.json()
                message = data["choices"][0]["message"]["content"]

                try:
                    suggestion = json.loads(message)
                except json.JSONDecodeError:
                    suggestion = {
                        "signal": "hold",
                        "confidence": 0.5,
                        "rationale": f"⚠️ Failed to parse GPT response: {message[:80]}..."
                    }

                await log_exit_dialog(trade_id, prompt, message, suggestion)
                return suggestion

    except Exception as e:
        print(f"⚠️ GPT exit analyzer error: {e}")
        return {
            "signal": "hold",
            "confidence": 0.5,
            "rationale": f"GPT error: {str(e)}"
        }


async def log_exit_dialog(trade_id, prompt, response, parsed):
    os.makedirs(os.path.dirname(DIALOG_LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "trade_id": trade_id,
        "model": GPT_MODEL,
        "version": GPT_MODEL_VERSION,
        "prompt": prompt,
        "raw_response": response,
        "parsed": parsed
    }
    try:
        async with asyncio.to_thread(open, DIALOG_LOG_PATH, "a") as f:
            await asyncio.to_thread(f.write, json.dumps(entry) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to log GPT exit dialog: {e}")
