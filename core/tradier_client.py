# File: core/tradier_client.py

import os
import json
import requests
from dotenv import load_dotenv
from core.resilient_request import resilient_post
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
    response = requests.get(url, headers=HEADERS)
    return response.json()

def get_account_balances(verbose=False):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/balances"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if verbose:
            print(json.dumps(data, indent=2))
        return parse_account_balances(data)
    except Exception as e:
        print(f"⚠️ Error retrieving Tradier balances: {e}")
        return 0.0, 0.0


def get_positions():
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/positions"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"🛑 Tradier API request failed: {e}")
        return []

    try:
        # Parse and validate JSON
        data = response.json()
    except Exception as e:
        print(f"🛑 Failed to parse JSON from Tradier response: {e}")
        print("Raw response text:", response.text)
        return []

    # 🧱 ABSOLUTE GUARD against invalid format
    if not isinstance(data, dict):
        print(f"🛑 Expected dict, but got {type(data)}: {data}")
        return []

    # 🧠 Defensive `.get()` only now that data is confirmed safe
    positions_field = data.get("positions", {})
    if not isinstance(positions_field, dict):
        print(f"🛑 'positions' field not a dict: {positions_field}")
        return []

    positions_data = positions_field.get("position", [])

    # Normalize
    if isinstance(positions_data, dict):
        return [positions_data]
    elif isinstance(positions_data, list):
        return positions_data
    else:
        print(f"🛑 Unexpected positions type: {type(positions_data)} → {positions_data}")
        return []




def get_option_chain(symbol, expiration=None):
    url = f"{TRADIER_API_URL}/markets/options/chains"
    params = {"symbol": symbol}
    if expiration:
        params["expiration"] = expiration
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

def get_quote(symbol):
    url = f"{TRADIER_API_URL}/markets/quotes"
    params = {"symbols": symbol}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

# ✅ Trade Execution Functions

def submit_order(option_symbol, quantity, action="buy_to_open", order_type="market", duration="day"):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    payload = {
        "class": "option",
        "symbol": option_symbol,
        "side": action,
        "quantity": quantity,
        "type": order_type,
        "duration": duration
    }
    try:
        response = resilient_post(
            url,
            headers=HEADERS,
            data=payload
        )
        if response is None:
            print(f"🛑 Tradier order failed after retries for {option_symbol}")
            return {"status": "failed", "error": "resilient_post returned None"}

        resp_json = response.json()
        if resp_json.get("status") != "ok":
            print(f"⚠️ Tradier returned non-ok status: {resp_json}")
        return resp_json
    except Exception as e:
        print(f"🛑 Unexpected error submitting order via resilient_post: {e}")
        return {"status": "error", "exception": str(e)}

def cancel_order(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}/cancel"
    response = requests.delete(url, headers=HEADERS)
    return response.json()

def get_order_status(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def parse_account_balances(data):
    balances = data.get("balances", {})
    # Fallback to find equity in any nested structure
    equity_keys = ["equity", "account_value", "total_equity", "cash_available"]
    equity = 0.0
    for key in equity_keys:
        try:
            val = balances.get(key)
            if isinstance(val, dict):  # handle nested
                for subval in val.values():
                    if isinstance(subval, (int, float)):
                        equity = max(equity, subval)
            else:
                equity = float(val)
            if equity > 0:
                break
        except:
            continue

    buying_power = float(balances.get("margin", {}).get("option_buying_power", 0.0))
    return buying_power, equity
