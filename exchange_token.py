import requests
import json

# 🛂 TradeStation credentials
client_id = "8uCRRizNTzgBuTdkIZF7zaZiouYcKZH7"  # Your client_id
redirect_uri = "https://q-algo.com/callback"  # Your redirect URI
token_url = "https://signin.tradestation.com/oauth/token"  # Token 
endpoint

# 🎯 Get the authorization code from the URL (the one you received in the 
browser)
authorization_code = "XYZ123"  # <-- Replace with the code you received in 
the URL!

# 🔑 Read code_verifier from pkce_state.json
with open("pkce_state.json", "r") as f:
    code_verifier = json.load(f)["code_verifier"]

# 📡 Exchange code for access/refresh tokens
payload = {
    "grant_type": "authorization_code",
    "client_id": client_id,
    "code": authorization_code,
    "redirect_uri": redirect_uri,
    "code_verifier": code_verifier,
}

response = requests.post(token_url, data=payload)

# Output the response
if response.status_code == 200:
    print("\n🎟️ Token Response:\n", response.json())
else:
    print(f"❌ Error: {response.status_code} - {response.text}")

