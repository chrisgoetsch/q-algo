import os
import datetime
import json
import requests

from core.resilient_request import resilient_get
import polygon.polygon_rest as polygon
from core.logger_setup import logger
from core.capital_manager import get_tradier_buying_power
from core.tradier_client import get_account_balances

TRADIER_API_KEY = os.getenv("TRADIER_ACCESS_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TRADIER_API_BASE = os.getenv("TRADIER_API_BASE", "https://api.tradier.com/v1").rstrip("/")

HEADERS = {
    "Authorization": f"Bearer " + TRADIER_API_KEY,
    "Accept": "application/json"
}


def get_atm_option_symbol(symbol: str = "SPY", call_put: str = "C"):
    """
    Resolve ATM option symbol using Tradier strikes + Polygon underlying snapshot.
    Includes fallback to next expiry if today's chain is empty.
    """
    today = datetime.date.today()
    expiry_dates = [today, today + datetime.timedelta(days=1)]  # Try today, then tomorrow

    price = polygon.get_underlying_from_option_snapshot(symbol)
    if not price:
        logger.warning({"event": "missing_price", "symbol": symbol})
        return None

    for expiry_date in expiry_dates:
        expiry = expiry_date.strftime("%Y-%m-%d")
        expiry_fmt = expiry_date.strftime("%y%m%d")

        strike_url = f"{TRADIER_API_BASE}/markets/options/strikes"
        params = {"symbol": symbol, "expiration": expiry}
        response = resilient_get(strike_url, params=params, headers=HEADERS)

        if not response:
            logger.warning({"event": "tradier_strike_fetch_fail", "symbol": symbol, "expiry": expiry})
            continue

        try:
            data = response.json()
            strike_list = data.get("strikes", {}).get("strike", [])
            strikes = [float(s) for s in strike_list]
        except Exception as e:
            logger.error({
                "event": "strike_parse_fail",
                "error": str(e),
                "raw": response.text
            })
            continue

        if not strikes:
            continue

        atm_strike = min(strikes, key=lambda x: abs(x - price))
        strike_code = f"{int(atm_strike * 1000):08d}"
        option_symbol = f"{symbol}{expiry_fmt}{call_put.upper()}{strike_code}"

        logger.info({
            "event": "atm_option_resolved",
            "price": price,
            "strike": atm_strike,
            "option_symbol": option_symbol
        })

        return option_symbol

    logger.warning({"event": "atm_option_symbol_failed", "symbol": symbol})
    return None


def submit_order(option_symbol: str, quantity: int, action: str, estimated_cost_per_contract: float = 1.00):
    """
    Submits a market order to Tradier for a single-leg SPY option.
    Includes capital check before sending live order.
    """
    if os.getenv("ALLOW_ORDER_SUBMISSION") == "0":
        logger.info({"event": "order_skipped_test_mode", "option_symbol": option_symbol})
        print(f"🚫 Test mode: Skipped order for {option_symbol}")
        return {"status": "skipped", "reason": "test_mode"}

    if quantity < 1:
        print(f"⚠️ Invalid order quantity: {quantity}")
        return {"status": "skipped", "reason": "invalid_quantity"}

    # Capital check
    buying_power = get_tradier_buying_power()
    estimated_total_cost = estimated_cost_per_contract * quantity * 100

    if buying_power < estimated_total_cost:
        logger.warning({
            "event": "order_blocked_low_funds",
            "required": estimated_total_cost,
            "available": buying_power,
            "option_symbol": option_symbol
        })
        print(f"🛑 Order blocked: Not enough capital (${buying_power:.2f} available, need ${estimated_total_cost:.2f})")
        return {"status": "blocked", "reason": "insufficient_capital"}

    url = f"{TRADIER_API_BASE}/accounts/{TRADIER_ACCOUNT_ID}/orders"
    data = {
        "class": "option",
        "symbol": "SPY",
        "option_symbol": option_symbol,
        "side": action,
        "quantity": str(quantity),
        "type": "market",
        "duration": "day"
    }

    print(f"[Q Algo] 🟢 Submitting order: {option_symbol} × {quantity} ({action})")

    try:
        response = requests.post(url, headers=HEADERS, data=data)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            logger.warning({"event": "tradier_order_rejected", "errors": result["errors"]})
            return {"status": "rejected", "errors": result["errors"]}

        order_data = result.get("order", {})
        if order_data.get("status") == "ok":
            order_id = order_data.get("id")
            print(f"✅ Order confirmed → ID: {order_id}")
            return {"status": "ok", "order_id": order_id, "option_symbol": option_symbol}
        else:
            print(f"⚠️ Unexpected Tradier order response:\n{json.dumps(result, indent=2)}")
            return {"status": "unknown", "raw": result}

    except Exception as e:
        logger.error({"event": "tradier_order_exception", "error": str(e)})
        print(f"🛑 Order failed: {e}")
        return {"status": "error", "message": str(e)}
