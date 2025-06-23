# File: tests/test_tradier.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add project root

from dotenv import load_dotenv
from core.capital_manager import fetch_tradier_equity, get_tradier_buying_power
from core.trade_engine import open_position
from core.option_selector import select_best_0dte_option

load_dotenv()

def test_tradier_status():
    print("🔍 Fetching account balance...")
    eq = fetch_tradier_equity()
    bp = get_tradier_buying_power()
    print(f"✅ Equity: ${eq:,.2f}")
    print(f"✅ Buying Power: ${bp:,.2f}")

def test_place_order():
    print("🚀 Selecting best SPY 0DTE contract...")

    opt = select_best_0dte_option("SPY", side="call", verbose=True)
    if not opt or not opt.get("symbol"):
        print("❌ No valid contract returned by option selector.")
        return

    symbol = opt["symbol"]
    strike = opt["strike"]
    expiry = opt["expiry"]
    contracts = 1
    option_type = "C" if opt.get("call_put", "call") == "call" else "P"

    print(f"✅ Chosen: {symbol} | strike: {strike} | expiry: {expiry}")

    try:
        result = open_position(
            symbol=symbol,
            quantity=contracts,
            call_put=option_type,
            score=0.65,
            rationale="test contract selected via option_selector.py"
        )
        print("🟢 Order Result:", result)
    except Exception as e:
        print("❌ Failed to place order:", str(e))

if __name__ == "__main__":
    print("== Tradier Account Diagnostic ==")
    test_tradier_status()

    print("\n== Option Trade Dry Run ==")
    test_place_order()
