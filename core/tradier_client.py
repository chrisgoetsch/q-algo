# File: core/tradier_client.py

import os
import requests
from dotenv import load_dotenv

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

def get_account_balances():
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/balances"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def get_positions():
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/positions"
    response = requests.get(url, headers=HEADERS)
    return response.json()

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
        response = requests.post(url, headers=HEADERS, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"🛑 HTTP error submitting order: {e}")
        print(response.text)
        return None
    except Exception as e:
        print(f"🛑 Unexpected error submitting order: {e}")
        return None

def cancel_order(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}/cancel"
    response = requests.delete(url, headers=HEADERS)
    return response.json()

def get_order_status(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()
