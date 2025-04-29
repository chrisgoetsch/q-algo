# trade_engine.py
# Full lifecycle executor: signal → entry → track → exit → close order

import time
from core.mesh_router import get_mesh_signal
from core.entry_learner import score_entry, build_entry_features
from core.tradestation_execution import submit_order
from core.position_manager import evaluate_exit, exit_trade
from training_data.entry_tracker import log_entry_features
from training_data.trade_logger import log_trade
from core.kill_switch import check_kill
from polygon.polygon_rest import get_atm_strike, get_today_expiry, 
get_current_price

SYMBOL = "SPY"

class TradeEngine:
    def __init__(self):
        self.logs = []

    def execute(self):
        if check_kill():
            print("🛑 Kill switch engaged.")
            time.sleep(10)
            return

        signal = get_mesh_signal(symbol=SYMBOL)
        if signal["score"] < 0.6:
            print("⚠️ Mesh signal too weak.")
            time.sleep(10)
            return

        features = build_entry_features(signal)
        entry_score = score_entry(features)
        features["model_score"] = entry_score

        if entry_score < 0.6:
            print(f"🧠 Entry model score too low: {entry_score}")
            time.sleep(10)
            return

        strike = get_atm_strike()
        expiry = get_today_expiry()
        order = submit_order(SYMBOL, signal["direction"], strike, expiry)
        if not order:
            print("❌ Order failed")
            return

        trade_id = order.get("order_id", f"trade_{int(time.time())}")

        trade = {
            "id": trade_id,
            "symbol": SYMBOL,
            "direction": signal["direction"],
            "strike": strike,
            "expiry": expiry,
            "entry_time": time.time(),
            "entry_price": get_current_price(SYMBOL).get("results", {}).get("p", 
440),
            "capital_pct": 0.2,
            "agents": signal.get("agents", []),
            "mesh_signal": signal,
            "take_profit": signal.get("tp"),
            "stop_loss": signal.get("sl")
        }

        log_trade({"trade_id": trade_id, "entry_score": signal["score"]}, 
mesh_signal=signal)
        log_entry_features(features, trade_id, mesh_signal=signal)
        print(f"✅ Trade entered: {trade_id}")

        hold_time = 0
        while hold_time < 600:
            trade["current_price"] = get_current_price(SYMBOL).get("results", 
{}).get("p", trade["entry_price"])
            exit_check = evaluate_exit(trade)
            if exit_check.get("exit_now"):
                exit_trade(trade_id, trade, mesh_signal=signal)
                break
            time.sleep(5)
            hold_time += 5

        self.logs.append({"trade_id": trade_id, "duration_sec": hold_time, 
"timestamp": time.time()})
        print("🔁 Restarting loop...")
        time.sleep(5)

if __name__ == "__main__":
    engine = TradeEngine()
    while True:
        engine.execute()

