# File: preflight_check.py

import sys
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

REQUIRED_ENV_VARS = [
    "TRADIER_ACCOUNT_ID",
    "TRADIER_ACCESS_TOKEN",
    "OPENAI_API_KEY",
    "POLYGON_API_KEY",
    "TRADIER_API_BASE"
]

REQUIRED_FILES = [
    "logs/runtime_state.json",
    "logs/status.json",
    "logs/open_trades.jsonl",
    "data/mesh_config.json"
]

MINIMUM_REQUIRED_CASH = float(os.getenv("MINIMUM_REQUIRED_CASH", 1.00))  # $1 default

def check_env_file():
    root_path = Path(__file__).resolve().parent
    dotenv_path = root_path / ".env"
    if not dotenv_path.exists():
        print(f"❌ Missing .env file at {dotenv_path}")
        return False
    load_dotenv(dotenv_path)
    all_present = True
    print("🔍 Validating environment variables:")
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            print(f"    ❌ Missing: {var}")
            all_present = False
        else:
            print(f"    ✅ {var}")
    return all_present

def check_files():
    all_present = True
    print("\n📁 Checking required system files:")
    for rel_path in REQUIRED_FILES:
        file_path = Path(__file__).resolve().parent / rel_path
        if not file_path.exists():
            print(f"    ❌ Missing file: {rel_path}")
            all_present = False
        elif file_path.suffix == ".json":
            try:
                with open(file_path) as f:
                    json.load(f)
                print(f"    ✅ {rel_path}")
            except Exception as e:
                print(f"    ❌ Malformed JSON: {rel_path} → {e}")
                all_present = False
        else:
            print(f"    ✅ {rel_path}")
    return all_present

def check_tradier_funding():
    print("\n💰 Checking Tradier account balance...")
    token = os.getenv("TRADIER_ACCESS_TOKEN")
    account_id = os.getenv("TRADIER_ACCOUNT_ID")
    base = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1")

    url = f"{base}/accounts/{account_id}/balances"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        balances = data.get("balances", {})
        cash = balances.get("total_cash", 0)
        buying_power = balances.get("margin", {}).get("option_buying_power", 0)

        print(f"    💵 Cash: ${cash:.2f} | Option Buying Power: ${buying_power:.2f}")

        if float(cash) < MINIMUM_REQUIRED_CASH and float(buying_power) < MINIMUM_REQUIRED_CASH:
            print(f"    ❌ Insufficient funds: minimum required is ${MINIMUM_REQUIRED_CASH:.2f}")
            return False
        return True
    except Exception as e:
        print(f"    ❌ Failed to retrieve or parse Tradier balances: {e}")
        return False

def main():
    print(f"\n🚀 Q-ALGO v2 Preflight Check — {datetime.utcnow().isoformat()} UTC\n")
    env_ok = check_env_file()
    files_ok = check_files()
    funding_ok = check_tradier_funding()

    if env_ok and files_ok and funding_ok:
        print("\n✅ All systems GO. You're ready to launch Q-ALGO.\n")
        sys.exit(0)
    else:
        print("\n⚠️ Preflight check failed. Fix issues above before running.\n")
        sys.exit(1) 
   