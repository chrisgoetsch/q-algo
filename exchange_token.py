import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 🚀 Inputs
code = input("Paste the code from callback URL: ").strip()
code_verifier = input("Paste the code_verifier from gen_auth_url.py: ").strip()

# 🔐 Config
client_id = os.getenv("TRADESTATION_CLIENT_ID")
redirect_uri = os.getenv("TRADESTATION_REDIRECT_URI")

# 📡 Exchange code for tokens
data = {
    "grant_type": "authorization_code",
    "client_id": client_id,
    "code": code,
    "redirect_uri": redirect_uri,
    "code_verifier": code_verifier
}
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.post("https://signin.tradestation.com/oauth/token", data=data, headers=headers)

# ✅ Handle response
if response.status_code == 200:
    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 💾 Update .env file
    def replace_env_var(file_path, key, new_value):
        with open(file_path, "r") as f:
            lines = f.readlines()
        with open(file_path, "w") as f:
            found = False
            for line in lines:
                if line.startswith(key + "="):
                    f.write(f"{key}={new_value}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"{key}={new_value}\n")

    env_path = ".env"
    replace_env_var(env_path, "TRADESTATION_ACCESS_TOKEN", access_token)
    replace_env_var(env_path, "TRADESTATION_REFRESH_TOKEN", refresh_token)

    print("✅ Token exchange successful.")
    print(f"🔐 Access Token (first 40): {access_token[:40]}...")
    print(f"🔁 Refresh Token (first 40): {refresh_token[:40]}...")
    print("💾 Tokens saved to .env successfully.")

    # 🔁 GitHub push (safe — .env excluded via .gitignore)
    print("📦 Committing updated .env (excluded) and pushing code...")
    os.system("git add .")
    os.system("git commit -m '🔁 Auto token refresh and project sync'")
    os.system("git push")

else:
    print("❌ Error exchanging token:")
    print(response.status_code, response.text)
