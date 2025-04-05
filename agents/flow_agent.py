from market.live_price_feed import get_live_price

class FlowAgent:
    def __init__(self, symbol="SPY"):
        self.symbol = symbol

    def pressure(self):
        data = get_live_price(self.symbol)
        volume = data["volume"]
        price = data["price"]

        # Simulated pressure logic (upgrade to real L2 data later)
        if volume > 1800000 and price > 441:
            return "buy_pressure"
        elif volume > 1800000 and price < 439:
            return "sell_pressure"
        else:
            return "neutral"
