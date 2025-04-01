import os
import requests
from dotenv import load_dotenv

# 🔄 Load environment variables from .env file
load_dotenv()

# ✅ Get token and account from .env
access_token = os.getenv("TRADESTATION_ACCESS_TOKEN")
account_id = os.getenv("TRADESTATION_ACCOUNT_ID")

# 🔍 Safety check to ensure they loaded
if not access_token or not account_id:
    print("❌ Missing token or account ID from .env")
    exit(1)

# 🔗 TradeStation balance endpoint
url = f"https://api.tradestation.com/v3/brokerage/accounts/{account_id}/balances"

# 🧾 Auth headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 📡 Send request
response = requests.get(url, headers=headers)

# 📊 Output result
print("📊 Balance Response:")
print(response.status_code)
try:
    print(response.json())
except Exception as e:
    print(f"❌ Failed to parse response JSON: {e}")
    print(response.text)
