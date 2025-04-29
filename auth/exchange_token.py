# exchange_token.py
# Q-ALGO v2 - Exchanges authorization code for access and refresh tokens

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

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

headers = {"Content-Type": "application/x-www-form-urlencoded"}
response = requests.post("https://signin.tradestation.com/oauth/token", 
data=data, headers=headers)

if response.ok:
    tokens = response.json()
    print("✅ Token exchange successful.")
    with open("auth/tokens.json", "w") as f:
        json.dump(tokens, f, indent=2)
else:
    print("❌ Exchange failed:", response.status_code)
    print(response.text)

