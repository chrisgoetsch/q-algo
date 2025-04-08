# generate_auth_url.py

import secrets
import hashlib
import base64
import urllib.parse

# ⚙️ Config
CLIENT_ID = "8uCRRizNTzgBuTdkIZF7zaZiouYcKZH7"
REDIRECT_URI = "https://q-algo.com/callback"

# 🔐 Generate code verifier + challenge
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')

# 🌐 Build authorization URL
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
    "scope": "openid profile offline_access MarketData Trade OptionSpreads Matrix",
}
auth_url = f"https://signin.tradestation.com/authorize?{urllib.parse.urlencode(params)}"

# ✏️ Save verifier for later token exchange
with open("pkce_state.json", "w") as f:
    f.write(f'{{"code_verifier": "{code_verifier}"}}')

print("\n🔗 Open this URL in your browser to authorize Q Algo:\n")
print(auth_url)
