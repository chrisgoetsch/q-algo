import random

def get_live_price(symbol="SPY"):
    # 🔄 Simulate polling TradeStation API (real implementation will use REST or WebSocket)
    price = round(440 + random.uniform(-1.5, 1.5), 2)
    volume = random.randint(1000000, 2000000)
    return {
        "symbol": symbol,
        "price": price,
        "volume": volume
    }
