import os
import json
from dotenv import load_dotenv
from core.resilient_request import resilient_get, resilient_post
from core.logger_setup import logger

load_dotenv()

TRADIER_ACCESS_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TRADIER_API_URL = "https://api.tradier.com/v1"

HEADERS = {
    "Authorization": f"Bearer {TRADIER_ACCESS_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 📊 Account + Market Data Functions

def get_account_profile():
    url = f"{TRADIER_API_URL}/user/profile"
    response = resilient_get(url, headers=HEADERS)
    if not response:
        return {}
    return response.json()


def get_account_balances(verbose=False):
    """
    Returns (buying_power, equity) as floats.
    """
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/balances"
    response = resilient_get(url, headers=HEADERS)
    if not response:
        logger.error({"event": "tradier_balance_fetch_fail"})
        return 0.0, 0.0

    try:
        data = response.json()
        if verbose:
            print(json.dumps(data, indent=2))
        return parse_account_balances(data)
    except Exception as e:
        logger.error({"event": "tradier_balance_parse_error", "error": str(e), "raw": response.text})
        return 0.0, 0.0


def get_positions():
    """
    Returns {"positions": [position_dicts]} or {"positions": []} on error.
    """
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/positions"
    response = resilient_get(url, headers=HEADERS)
    if not response:
        logger.error({"event": "tradier_position_fetch_fail"})
        return {"positions": []}

    try:
        data = response.json()
        raw = data.get("positions", {})
        pos_data = raw.get("position", [])

        if isinstance(pos_data, dict):
            return {"positions": [pos_data]}
        elif isinstance(pos_data, list):
            return {"positions": pos_data}
        else:
            logger.warning({"event": "tradier_position_format_error", "type": str(type(pos_data))})
            return {"positions": []}

    except Exception as e:
        logger.error({"event": "tradier_position_json_error", "error": str(e), "raw": response.text})
        return {"positions": []}


def get_option_chain(symbol, expiration=None):
    url = f"{TRADIER_API_URL}/markets/options/chains"
    params = {"symbol": symbol}
    if expiration:
        params["expiration"] = expiration
    response = resilient_get(url, headers=HEADERS, params=params)
    return response.json() if response else {}


def get_quote(symbol):
    url = f"{TRADIER_API_URL}/markets/quotes"
    params = {"symbols": symbol}
    response = resilient_get(url, headers=HEADERS, params=params)
    return response.json() if response else {}


def cancel_order(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}/cancel"
    response = resilient_post(url, headers=HEADERS, method="DELETE")
    return response.json() if response else {}


def get_order_status(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}"
    response = resilient_get(url, headers=HEADERS)
    return response.json() if response else {}


def parse_account_balances(data):
    """
    Extract buying power and equity from Tradier balance response.
    Returns (buying_power, equity) in USD as floats.
    """
    balances = data.get("balances", {})
    equity_keys = ["equity", "account_value", "total_equity", "cash_available"]
    equity = 0.0

    for key in equity_keys:
        try:
            val = balances.get(key)
            if isinstance(val, dict):
                for subval in val.values():
                    if isinstance(subval, (int, float)):
                        equity = max(equity, subval)
            else:
                equity = float(val)
            if equity > 0:
                break
        except:
            continue

    try:
        buying_power = float(balances.get("margin", {}).get("option_buying_power", 0.0))
    except:
        buying_power = 0.0

    return buying_power, equity
