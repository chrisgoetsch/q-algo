import os, base64, hashlib, urllib.parse
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv("TRADESTATION_CLIENT_ID")
redirect_uri = os.getenv("TRADESTATION_REDIRECT_URI")

if not client_id or not redirect_uri:
    print("❌ Missing TRADESTATION_CLIENT_ID or TRADESTATION_REDIRECT_URI in .env")
    exit(1)

code_verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b'=').decode('utf-8')
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).rstrip(b'=').decode('utf-8')

scopes = [
    "openid", "offline_access", "profile",
    "MarketData", "ReadAccount", "Trade", "OptionSpreads", "Matrix"
]

params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "audience": "https://api.tradestation.com",
    "scope": " ".join(scopes),
    "code_challenge": code_challenge,
    "code_challenge_method": "S256"
}

url = "https://signin.tradestation.com/authorize?" + urllib.parse.urlencode(params)

print("✅ Login URL:\n", url)
print("\n🔐 Save this code_verifier:")
print(code_verifier)
