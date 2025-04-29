# File: brokers/tradier_execution.py

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

def place_option_order(option_symbol, quantity, action="buy_to_open", order_type="market", duration="day"):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    payload = {
        "class": "option",
        "symbol": option_symbol,
        "side": action,
        "quantity": quantity,
        "type": order_type,
        "duration": duration
    }
    response = requests.post(url, headers=HEADERS, data=payload)
    return response.json()

def cancel_order(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}/cancel"
    response = requests.delete(url, headers=HEADERS)
    return response.json()

def get_order_status(order_id):
    url = f"{TRADIER_API_URL}/accounts/{TRADIER_ACCOUNT_ID}/orders/{order_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()
