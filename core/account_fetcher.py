# File: core/account_fetcher.py

import os
import json
import requests
from datetime import datetime
from core.capital_manager import get_tradier_buying_power

TRADIER_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TRADIER_BASE_URL = os.getenv("TRADIER_BASE_URL", "https://api.tradier.com/v1")

ACCOUNT_SUMMARY_PATH = "logs/account_summary.json"

def fetch_tradier_equity():
    buying_power, equity = get_tradier_buying_power(verbose=True)
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "equity": equity,
        "buying_power": buying_power
    }
    os.makedirs("logs", exist_ok=True)
    with open(ACCOUNT_SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Account equity pulled: ${equity:,.2f}")
