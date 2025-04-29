# generate_auth_url.py
# Starts the OAuth2 PKCE authorization flow for TradeStation

import urllib.parse
import os
import json

CLIENT_ID = os.getenv("TRADESTATION_CLIENT_ID")
REDIRECT_URI = os.getenv("TRADESTATION_REDIRECT_URI")
SCOPES = [
    "openid",
    "offline_access",
    "profile",
    "MarketData",
    "Trade",
    "ReadAccount",
    "OptionSpreads",
    "Matrix"
]

def generate_auth_url(code_challenge):
    """
    Generates the PKCE-compliant TradeStation auth URL
    """
    base_url = "https://api.tradestation.com/v2/authorize"

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    print(f"[Auth] Navigate to:\n{url}")
    return url

if __name__ == "__main__":
    import hashlib, base64, secrets

    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")

    print("[PKCE] Code Verifier (save this):", verifier)
    generate_auth_url(code_challenge=challenge)

