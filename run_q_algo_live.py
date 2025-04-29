# File: run_q_algo_live.py

import time
from core.trade_engine import open_position
from core.position_manager import manage_positions
from core.entry_learner import evaluate_entry

def main_loop():
    print("[Q Algo] Live Trading Session Starting with Tradier...")
    while True:
        try:
            # Example: Daily 0DTE Scalp Check
            symbol = "SPY"

            if evaluate_entry(symbol):
                open_position(symbol=symbol, quantity=1, call_put="C")

            # Manage any open trades
            manage_positions()

            # Sleep between trading cycles
            time.sleep(60)  # Check every 60 seconds (adjust as needed)

        except Exception as e:
            print(f"[Q Algo] Exception caught in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
