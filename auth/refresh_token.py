k# refresh_token.py
# Q-ALGO v2 - Manually refreshes TradeStation access token

import os
import json
from dotenv import load_dotenv
from core.resilient_request import resilient_post

load_dotenv()

TOKENS_PATH = "auth/tokens.json"
client_id = os.getenv("TRADESTATION_CLIENT_ID")
redirect_uri = os.getenv("TRADESTATION_REDIRECT_URI")
auth_code = os.getenv("TRADESTATION_AUTHORIZATION_CODE")

with open("auth/pkce_verifier.txt", "r") as f:
    code_verifier = f.read().strip()

data = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "code_verifier": code_verifier
}

url = "https://signin.tradestation.com/oauth/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = resilient_post(url, data=data, headers=headers)

if response:
    try:
        tokens = response.json()
        print("✅ Token exchange successful.")
        with open(TOKENS_PATH, "w") as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        print("❌ Failed to parse token response:", e)
else:
    print("❌ Token request failed: No response from TradeStation")

