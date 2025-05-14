# File: core/tradier_execution.py

import os
import requests
import datetime
from core.resilient_request import resilient_get
import polygon.polygon_rest as polygon
from core.logger_setup import logger
from core.capital_manager import get_tradier_buying_power

TRADIER_API_KEY = os.getenv("TRADIER_ACCESS_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")

HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}",
    "Accept": "application/json"
}

def submit_order(option_symbol: str, quantity: int, action: str):
    """
    Submits a market order to Tradier to open or close an option position.
    Prevents execution if ALLOW_ORDER_SUBMISSION=0 or buying power is zero.
    """
    # 🧪 Test mode override
    if os.getenv("ALLOW_ORDER_SUBMISSION") == "0":
        logger.info({"event": "order_skipped_due_to_test_mode", "symbol": option_symbol})
        print(f"🚫 Order skipped (test mode): {option_symbol}")
        return {"status": "skipped", "reason": "test_mode"}

    # 🛡️ Check available funds
    buying_power = get_tradier_buying_power()
    if buying_power <= 0:
        logger.warning({
            "event": "order_blocked_insufficient_funds",
            "symbol": option_symbol,
            "buying_power": buying_power
        })
        print(f"🚫 Order blocked — no available buying power. Symbol: {option_symbol}")
        return {"status": "skipped", "reason": "no_funds"}

    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    data = {
        "class": "option",
        "symbol": option_symbol,
        "side": action,
        "quantity": quantity,
        "type": "market",
        "duration": "day"
    }

    try:
        response = requests.post(url, headers=HEADERS, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error({
            "event": "tradier_order_failed",
            "error": str(e),
            "symbol": option_symbol
        })
        print(f"🛑 Tradier order submission failed: {e}")
        return None

def get_atm_option_symbol(symbol: str = "SPY", call_put: str = "C"):
    """
    Fetch ATM option symbol using Tradier's strikes API and Polygon's snapshot price.
    """
    today = datetime.date.today()
    expiry = today.strftime("%Y-%m-%d")
    expiry_fmt = today.strftime("%y%m%d")

    price = polygon.get_underlying_from_option_snapshot(symbol)
    if not price:
        print("⚠️ Unable to fetch underlying price for ATM logic.")
        logger.warning({"event": "missing_price", "symbol": symbol})
        return None

    strike_url = f"{TRADIER_API_BASE}/markets/options/strikes"
    params = {"symbol": symbol, "expiration": expiry}
    response = resilient_get(strike_url, params=params, headers=HEADERS)

    if not response:
        print("⚠️ Could not retrieve strikes from Tradier.")
        logger.warning({"event": "tradier_strike_fetch_fail", "symbol": symbol})
        return None

    try:
        data = response.json()
    except Exception as e:
        logger.error({
            "event": "tradier_strike_json_fail",
            "error": str(e),
            "raw_text": response.text
        })
        return None

    try:
        raw_strikes = data.get("strikes", {})
        strike_list = raw_strikes.get("strike", [])
        strikes = [float(s) for s in strike_list]
    except Exception as e:
        logger.error({
            "event": "strike_type_conversion_fail",
            "error": str(e),
            "strikes_raw": data.get("strikes", {})
        })
        return None

    if not strikes:
        print("⚠️ No usable strikes found.")
        return None

    atm_strike = min(strikes, key=lambda x: abs(x - price))
    strike_code = f"{int(atm_strike * 1000):08d}"  # e.g., 450.0 → "00450000"
    option_symbol = f"{symbol}{expiry_fmt}{call_put.upper()}{strike_code}"

    logger.info({
        "event": "atm_option_resolved",
        "price": price,
        "strike": atm_strike,
        "option_symbol": option_symbol
    })

    return option_symbol
