# File: core/account_fetcher.py

import os
import json
import requests
from datetime import datetime

TRADIER_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TRADIER_BASE_URL = os.getenv("TRADIER_BASE_URL", "https://api.tradier.com/v1")

ACCOUNT_SUMMARY_PATH = "logs/account_summary.json"

def fetch_tradier_equity():
    headers = {
        "Authorization": f"Bearer {TRADIER_TOKEN}",
        "Accept": "application/json"
    }

    url = f"{TRADIER_BASE_URL}/accounts/{TRADIER_ACCOUNT_ID}/balances"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("balances", {})

        summary = {
            "equity": data.get("equity", 0.0),
            "cash": data.get("cash", 0.0),
            "margin": data.get("margin", 0.0),
            "timestamp": datetime.utcnow().isoformat()
        }

        os.makedirs("logs", exist_ok=True)
        with open(ACCOUNT_SUMMARY_PATH, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"✅ Account equity pulled: ${summary['equity']:.2f}")
        return summary

    except Exception as e:
        print(f"❌ Failed to fetch account equity: {e}")
        return {}
