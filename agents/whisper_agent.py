from market.live_price_feed import get_live_price

class WhisperAgent:
    def __init__(self, symbol="SPY"):
        self.symbol = symbol

    def detect(self):
        price_data = get_live_price(self.symbol)
        price = price_data["price"]

        # Simulate a subtle signal (price inside a "fade" zone)
        if 438.50 < price < 439.75:
            return 1  # Whispering long entry
        elif 440.25 < price < 441.25:
            return -1  # Whispering short fade
        return 0  # No signal

