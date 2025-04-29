# polygon_utils.py
# Helper tools for working with Polygon data formats

def round_to_nearest_strike(price, interval=5):
    return int(round(price / interval) * interval)

def format_option_symbol(symbol, expiry, strike, call_put):
    return f"{symbol}{expiry}{strike:05d}{call_put.upper()}"

def normalize_chain(chain, side="call"):
    return [opt for opt in chain if opt["details"]["contract_type"] == 
side]

