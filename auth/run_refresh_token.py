# run_refresh_token.py
# Q-ALGO v2 - Background token refresher for long-running sessions

import time
from auth.token_manager import refresh_access_token

def auto_refresh_loop():
    print("🔁 Running auto-refresh loop for TradeStation tokens...")
    while True:
        try:
            refresh_access_token()
        except Exception as e:
            print("❌ Token refresh error:", e)
        time.sleep(300)  # Refresh every 5 min

if __name__ == "__main__":
    auto_refresh_loop()

