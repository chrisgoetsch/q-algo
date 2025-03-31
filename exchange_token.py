import os
import requests
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("TRADESTATION_CLIENT_ID")
redirect_uri = os.getenv("TRADESTATION_REDIRECT_URI")
code = input("Paste the code from callback URL: ").strip()
code_verifier = input("Paste the code_verifier from gen_auth_url.py: ").strip()

# 📡 Token exchange request
data = {
    "grant_type": "authorization_code",
    "client_id": client_id,
    "code": code,
    "redirect_uri": redirect_uri,
    "code_verifier": code_verifier
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post("https://signin.tradestation.com/oauth/token", data=data, headers=headers)

if response.status_code != 200:
    print("❌ Error exchanging token:")
    print(response.status_code, response.text)
    exit(1)

token_data = response.json()
access_token = token_data["access_token"]
refresh_token = token_data["refresh_token"]

print("✅ Token exchange successful.")
print(f"🔐 Access Token (first 40): {access_token[:40]}...")
print(f"🔁 Refresh Token (first 40): {refresh_token[:40]}...")

# 🧪 Load existing .env and replace token lines
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path, "r") as file:
    lines = file.readlines()

with open(env_path, "w") as file:
    for line in lines:
        if line.startswith("TRADESTATION_ACCESS_TOKEN="):
            file.write(f"TRADESTATION_ACCESS_TOKEN={access_token}\n")
        elif line.startswith("TRADESTATION_REFRESH_TOKEN="):
            file.write(f"TRADESTATION_REFRESH_TOKEN={refresh_token}\n")
        else:
            file.write(line)

print("💾 Tokens saved to .env successfully.")
