# core/capital_manager.py

import json
import logging
import os
import threading

LOCK = threading.Lock()

CAPITAL_TRACKER_FILE = "logs/capital_tracker.json"

class CapitalManager:
    def __init__(self):
        self.capital_state = self.load_capital()

    def load_capital(self):
        try:
            if not os.path.exists(CAPITAL_TRACKER_FILE):
                logging.warning(f"{CAPITAL_TRACKER_FILE} not found. Initializing new tracker.")
                return {"starting_balance": 100000, "current_balance": 100000, "max_drawdown": 0}

            with open(CAPITAL_TRACKER_FILE, "r") as f:
                return json.load(f)

        except Exception as e:
            logging.error(f"Failed to load capital tracker: {str(e)}", exc_info=True)
            return {"starting_balance": 100000, "current_balance": 100000, "max_drawdown": 0}

    def save_capital(self):
        try:
            with LOCK:
                with open(CAPITAL_TRACKER_FILE, "w") as f:
                    json.dump(self.capital_state, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save capital tracker: {str(e)}", exc_info=True)

    def update_capital_state(self):
        try:
            # Placeholder logic for PnL adjustment
            simulated_pnl = 100  # Replace with real session PnL
            self.capital_state["current_balance"] += simulated_pnl
            self.save_capital()

            logging.info(f"Updated capital state: {self.capital_state}")

        except Exception as e:
            logging.error(f"Error updating capital state: {str(e)}", exc_info=True)

