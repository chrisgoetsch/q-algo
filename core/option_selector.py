# File: core/option_selector.py

from polygon.polygon_rest import get_polygon_snapshot_options
from polygon.polygon_websocket import SPY_LIVE_PRICE
from datetime import datetime
from math import log

def select_best_0dte_option(symbol: str, side: str = "call", verbose: bool = False) -> dict:
    chain = get_polygon_snapshot_options(symbol)
    if not chain or not isinstance(chain, list):
        if verbose:
            print("⚠️ No chain data from Polygon.")
        return {}

    now = datetime.utcnow().date()
    price = SPY_LIVE_PRICE.get("price")
    if not price:
        if verbose:
            print("⚠️ SPY price unavailable from WebSocket.")
        return {}

    side = side.lower()
    best = None
    best_score = float("-inf")

    for opt in chain:
        details = opt.get("details", {})
        if not details:
            continue

        exp = details.get("expiration_date")
        strike = details.get("strike_price")
        opt_type = details.get("contract_type", "").lower()
        greeks = opt.get("greeks", {})
        quote = opt.get("last_quote", {})
        volume = opt.get("day", {}).get("volume", 0)
        oi = opt.get("open_interest", 0)

        # Filter only 0DTE contracts of the correct type
        if not strike or opt_type != side:
            continue
        if not exp or datetime.strptime(exp, "%Y-%m-%d").date() != now:
            continue
        if "delta" not in greeks:
            continue

        bid = quote.get("bid", 0)
        ask = quote.get("ask", 0)
        if bid <= 0 or ask <= 0:
            continue
        spread = ask - bid
        if spread > 0.10:
            continue
        if volume < 10 or oi < 250:
            continue

        midpoint = (bid + ask) / 2
        if midpoint < 0.20:
            continue

        delta = abs(greeks.get("delta", 0))
        delta_target = 0.5
        delta_score = max(0, 1 - abs(delta_target - delta) * 2)  # max at 0.5
        dist_score = max(0, 1 - abs(strike - price) / 5)
        liq_score = log(oi + 1) + log(volume + 1)

        score = delta_score * 4 + dist_score * 3 + liq_score * 0.5

        if verbose:
            print(f"[{details.get('symbol')}] score={score:.2f} mid={midpoint:.2f} "
                  f"strike={strike} delta={delta:.2f} vol={volume} oi={oi}")

        if score > best_score:
            best_score = score
            best = details

    if not best:
        if verbose:
            print("❌ No valid option found after filtering.")
        return {}

    return {
        "symbol": best.get("symbol", ""),
        "strike": best.get("strike_price", 0),
        "expiry": best.get("expiration_date", ""),
        "call_put": side
    }
