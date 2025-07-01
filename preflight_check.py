# File: preflight_check.py — Verified startup sequence for Q-ALGO V2

import os
import sys
import json
import time
from datetime import datetime
from core.logger_setup import get_logger
from core.env_validator import validate_env
from core.resilient_request import resilient_get

logger = get_logger(__name__)

TRADIER_BASE = os.getenv("TRADIER_API_BASE", "https://sandbox.tradier.com/v1")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

POLYGON_URL = f"https://api.polygon.io/v3/snapshot/options/SPY?apiKey={POLYGON_API_KEY}"
TRADIER_BALANCES_URL = f"{TRADIER_BASE}/accounts/{TRADIER_ACCOUNT_ID}/balances"
TRADIER_ORDERS_URL = f"{TRADIER_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
TRADIER_POSITIONS_URL = f"{TRADIER_BASE}/accounts/{TRADIER_ACCOUNT_ID}/positions"


def check_polygon():
    try:
        import requests
        r = requests.get(POLYGON_URL)
        if r.status_code == 401:
            raise Exception("401 Unauthorized — check POLYGON_API_KEY.")
        r.raise_for_status()
        if not r.content:
            raise Exception("Empty response from Polygon — check credentials.")
        data = r.json()
        if "results" not in data:
            raise Exception("Missing 'results' key — possible API/key mismatch.")
        return True
    except Exception as e:
        logger.error({"event": "polygon_preflight_fail", "err": str(e)})
        print("❌ Preflight check failed:", e)
        return False


def check_tradier():
    try:
        balances = resilient_get(TRADIER_BALANCES_URL).json()
        orders = resilient_get(TRADIER_ORDERS_URL).json()
        positions = resilient_get(TRADIER_POSITIONS_URL).json()

        print("\n💼 Tradier Account Snapshot:")
        print(json.dumps({
            "balances": balances,
            "orders": orders,
            "positions": positions,
        }, indent=2))
        return True
    except Exception as e:
        logger.error({"event": "tradier_preflight_fail", "err": str(e)})
        return False


def check_logs():
    try:
        os.makedirs("logs/", exist_ok=True)
        test_path = "logs/preflight_test.log"
        with open(test_path, "w") as f:
            f.write(f"Preflight log test @ {datetime.utcnow().isoformat()}\n")
        os.remove(test_path)
        return True
    except Exception as e:
        logger.error({"event": "log_dir_write_fail", "err": str(e)})
        return False


def run_preflight_check():
    print("🚀 Running Preflight Check...")
    validate_env()
    polygon_ok = check_polygon()
    tradier_ok = check_tradier()
    logs_ok = check_logs()

    if polygon_ok and tradier_ok and logs_ok:
        print("✅ Preflight passed. Launching Q-ALGO...")
        return True
    else:
        print("❌ Preflight check failed. Fix issues and retry.")
        return False


if __name__ == "__main__":
    run_preflight_check()
