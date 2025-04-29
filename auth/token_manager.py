# token_manager.py
# Q-ALGO v2 - Refreshes TradeStation token with retry + atomic write

import os
import json
import time
import base64
from dotenv import load_dotenv
from core.resilient_request import resilient_post
from datetime import datetime

load_dotenv()

TOKENS_PATH = "auth/tokens.json"
client_id = os.getenv("TRADESTATION_CLIENT_ID")
redirect_uri = os.getenv("TRADESTATION_REDIRECT_URI")

def load_tokens():
    try:
        if os.path.exists(TOKENS_PATH):
            with open(TOKENS_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load tokens: {e}")
    return {}

def save_tokens(tokens):
    try:
        tmp_path = TOKENS_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(tokens, f, indent=2)
        os.replace(tmp_path, TOKENS_PATH)
    except Exception as e:
        print(f"❌ Failed to save tokens: {e}")

def is_token_expired(token):
    try:
        payload = token.split('.')[1]
        padded = payload + '=' * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        return decoded['exp'] <= int(time.time()) + 60
    except Exception as e:
        print(f"❌ Token decode error: {e}")
        return True

def refresh_access_token():
    tokens = load_tokens()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise Exception("Missing refresh_token")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "redirect_uri": redirect_uri
    }

    url = "https://signin.tradestation.com/oauth/token"
    response = resilient_post(url, data=data, headers={"Content-Type": 
"application/x-www-form-urlencoded"})

    if response:
        try:
            new_tokens = response.json()
            save_tokens(new_tokens)
            print("🔁 Token refreshed.")
            return new_tokens
        except Exception as e:
            print(f"❌ Failed to parse refreshed token JSON: {e}")
    else:
        print("❌ No response from TradeStation on token refresh.")
        raise Exception("Token refresh failed")

def get_access_token():
    tokens = load_tokens()
    token = tokens.get("access_token")
    if not token or is_token_expired(token):
        return refresh_access_token().get("access_token")
    return token

