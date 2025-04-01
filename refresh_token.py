# refresh_token.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("TRADESTATION_CLIENT_ID")
client_secret = os.getenv("TRADESTATION_CLIENT_SECRET")
refresh_token = os.getenv("TRADESTATION_REFRESH_TOKEN")

data = {
    "grant_type": "refresh_token",
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": refresh_token,
}

response = requests.post("https://signin.tradestation.com/oauth/token", data=data)

if response.status_code == 200:
    token_data = response.json()
    print("✅ Refreshed token:")
    print(token_data)
else:
    print("❌ Failed to refresh token:")
    print(response.status_code, response.text)
