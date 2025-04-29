# position_manager.py
# Manages exits, trailing stops, alpha decay, GPT overrides, and PnL 
tracking

from memory.position_manager.position_memory import log_exit_analysis
from training_data.trade_logger import update_trade_exit
from training_data.mesh_logger import log_mesh_signal
from core.kill_switch import check_kill
from analytics.alpha_tracker import estimate_alpha_decay
from core.q_shield import get_risk_signal
from core.q_0dte import get_reversal_signal
from core.qthink_exit_whisper import suggest_exit_from_gpt
from polygon.polygon_rest import get_option_price
from core.capital_manager import update_capital_on_result
from core.open_trade_tracker import remove_trade

from datetime import datetime

TRAILING_STOP_RATIO = 0.5
MAX_HOLD_MINUTES = 60
STOP_LOSS_THRESHOLD = -0.2


def evaluate_exit(trade_id: str, symbol: str, entry_time: datetime, 
max_pnl: float) -> dict:
    """Main exit decision loop for live trades."""
    now = datetime.utcnow()
    minutes_held = (now - entry_time).total_seconds() / 60

    if check_kill():
        reason = "kill switch triggered"
        force_exit = True
    elif get_risk_signal() == "exit_all":
        reason = "Q Shield: risk off"
        force_exit = True
    elif get_reversal_signal(symbol):
        reason = "Q-0DTE reversal triggered"
        force_exit = True
    else:
        price = get_option_price(symbol)
        pnl = price  # Simplified for now
        decay_score = estimate_alpha_decay(trade_id)
        gpt_exit = suggest_exit_from_gpt(trade_id, pnl=pnl)

        if decay_score > 0.4:
            reason = "alpha decay"
            force_exit = True
        elif pnl < STOP_LOSS_THRESHOLD:
            reason = "hard stop"
            force_exit = True
        elif minutes_held > MAX_HOLD_MINUTES:
            reason = "max hold time"
            force_exit = True
        elif gpt_exit == "exit":
            reason = "GPT: exit advised"
            force_exit = True
        else:
            reason = "hold"
            force_exit = False

    if force_exit:
        update_trade_exit(trade_id, reason=reason)
        log_exit_analysis(trade_id, reason, pnl, max_pnl, 
trailing_stop_triggered=(reason == "alpha decay"))
        update_capital_on_result(trade_id, pnl)
        remove_trade(trade_id)

    return {
        "should_exit": force_exit,
        "exit_reason": reason,
        "minutes_held": round(minutes_held, 2)
    }


if __name__ == "__main__":
    test_id = "SPY437C_TEST"
    test_time = datetime.utcnow()
    print(evaluate_exit(test_id, "SPY437C", test_time, max_pnl=0.6))

