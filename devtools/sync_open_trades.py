def sync_open_trades_with_tradier():
    from core.tradier_client import get_positions
    import json
    import os

    OPEN_TRADES_PATH = "logs/open_trades.jsonl"

    raw = get_positions()
    if not isinstance(raw, dict):
        print("🛑 'positions' field not a dict: null or invalid response.")
        return

    tradier_symbols = {
        pos.get("symbol") or pos.get("option_symbol") for pos in raw.get("positions", [])
        if "symbol" in pos or "option_symbol" in pos
    }

    if not os.path.exists(OPEN_TRADES_PATH):
        print("⚠️ No open trades file to sync.")
        return

    cleaned_trades = []
    with open(OPEN_TRADES_PATH, "r") as f:
        for line in f:
            try:
                trade = json.loads(line)
                symbol = trade.get("symbol") or trade.get("option_symbol")
                if symbol in tradier_symbols:
                    cleaned_trades.append(trade)
                else:
                    print(f"🧹 Removing stale trade: {trade.get('trade_id')} (symbol={symbol})")
            except Exception as e:
                print(f"⚠️ Skipping malformed line: {e}")

    with open(OPEN_TRADES_PATH, "w") as f:
        for trade in cleaned_trades:
            f.write(json.dumps(trade) + "\n")

    print(f"🔄 Synced open trades. {len(cleaned_trades)} valid entries remain.")

def wipe_all_open_trades():
    with open(OPEN_TRADES_PATH, "w") as f:
        f.write("")
    print("🧨 All open trades wiped manually.")
