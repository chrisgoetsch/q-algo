# File: brokers/tradier_client.py

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
    response = requests.get(url, headers={"Authorization": f"Bearer {TRADIER_ACCESS_TOKEN}", "Accept": "application/json"}, params=params)
    return response.json()

def get_quote(symbol):
    url = f"{TRADIER_API_URL}/markets/quotes"
    params = {"symbols": symbol}
    response = requests.get(url, headers={"Authorization": f"Bearer {TRADIER_ACCESS_TOKEN}", "Accept": "application/json"}, params=params)
    return response.json()
