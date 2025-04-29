# polygon_iv_surface.py
# Generates SPY 0DTE IV surface from chain snapshot

from polygon.polygon_options import get_option_chain
from collections import defaultdict

def build_iv_surface(symbol="SPY"):
    chain = get_option_chain(symbol)
    surface = defaultdict(dict)

    for opt in chain:
        strike = opt["details"]["strike_price"]
        expiry = opt["details"]["expiration_date"]
        iv = opt.get("implied_volatility")
        if iv:
            surface[expiry][strike] = round(iv, 4)

    return dict(surface)

if __name__ == "__main__":
    surf = build_iv_surface()
    print("🔍 IV Surface:", surf)

