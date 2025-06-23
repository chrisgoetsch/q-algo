# File: core/telegram_alerts.py
import os
import httpx
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        return  # silently fail if not configured

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        with httpx.Client() as client:
            r = client.post(url, json=payload, timeout=5)
            r.raise_for_status()
    except Exception as e:
        print(f"⚠️ Telegram alert failed: {e}")
