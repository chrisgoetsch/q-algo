import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

TRADIER_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
HEADERS = {
    "Authorization": f"Bearer {TRADIER_TOKEN}",
    "Accept": "application/json"
}

BALANCE_URL = f"https://api.tradier.com/v1/accounts/{ACCOUNT_ID}/balances"
INFO_URL = "https://api.tradier.com/v1/user/profile"

def fetch_account_summary():
    print("🔍 Starting Tradier account fetch...")

    try:
        res = requests.get(BALANCE_URL, headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ Balance fetch error {res.status_code}: {res.text}")
            return
        balances = res.json()['balances']
        margin = balances.get('margin', {})

        res_info = requests.get(INFO_URL, headers=HEADERS)
        if res_info.status_code != 200:
            print(f"❌ Profile fetch error {res_info.status_code}: {res_info.text}")
            return
        account_info = res_info.json()['profile']['account']  # Not a list

        output = {
            "timestamp": res.headers.get("date"),
            "account_number": account_info['account_number'],
            "account_type": account_info['type'],
            "cash_available": balances.get('total_cash', 0),
            "cash_balance": balances.get('total_cash', 0),
            "option_buying_power": margin.get('option_buying_power', 0),
            "equity": balances.get('equity', 0),
            "unrealized_pl": balances.get('open_pl', 0),
            "realized_pl": balances.get('close_pl', 0),
            "margin_balance": margin.get('maintenance_call', 0),
            "day_trade_buying_power": margin.get('stock_buying_power', 0)
        }

        os.makedirs("logs", exist_ok=True)
        with open("logs/account_summary.json", "w") as f:
            json.dump(output, f, indent=2)

        print("✅ Account summary saved.")

    except Exception as e:
        print(f"❌ Error fetching account data: {type(e).__name__} → {e}")

if __name__ == "__main__":
    fetch_account_summary()
