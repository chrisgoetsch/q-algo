# File: qthink/qthink_engine.py

import os
from openai import OpenAIError
from dotenv import load_dotenv
from repo_context import get_context_snippets
from gpt_logger import log_dialog
from github_interface import get_latest_open_pr_number, get_pr_file_diffs
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL = os.getenv("GPT_MODEL", "gpt-4o")


def ask_qthink(user_input: str) -> str:
    try:
        context = get_context_snippets()

        # Fetch GitHub diff context
        pr_number = get_latest_open_pr_number()
        diff_snippets = ""
        if pr_number:
            diffs = get_pr_file_diffs(pr_number, max_chars_per_file=1000)
            diff_snippets = "\n\n".join([f"### {f}\n{patch}" for f, patch in diffs.items()])

        full_prompt = (
            f"You are QThink, a GPT-powered AI assistant for a live SPY 0DTE trading system.\n"
            f"Your task is to assist the developer by reviewing context and recent code changes.\n\n"
            f"Recent GitHub PR Diffs:\n{diff_snippets}\n\n"
            f"Codebase Snippets:\n{context}\n\n"
            f"User: {user_input}\nQThink:"
        )

        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.3,
        )
        reply = response.choices[0].message['content']
        log_dialog(user_input, reply)
        return reply
    except OpenAIError as e:
        return f"[QThink Error] {str(e)}"
