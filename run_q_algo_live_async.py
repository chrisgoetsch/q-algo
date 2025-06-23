# ─────────────────────────────────────────────────────────────────────────────
# File: run_q_algo_live_async.py   (v4b-HF-0DTE, 2025-06-14)
# Hedge-fund-grade 0-DTE SPY scalper – calls & puts
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import asyncio, signal, time
# --- TaskGroup poly-fill (Python 3.10) --------------------------------------
if not hasattr(asyncio, "TaskGroup"):
    class _TG:                                          # minimal shim
        def __init__(self): self._tasks: list[asyncio.Task] = []
        async def __aenter__(self): return self
        async def __aexit__(self, *_):
            await asyncio.gather(*self._tasks, return_exceptions=True)
        def create_task(self, coro): self._tasks.append(asyncio.create_task(coro))
    asyncio.TaskGroup = _TG                    # type: ignore[attr-defined]

# --- pretty printing --------------------------------------------------------
from importlib.util import find_spec
if find_spec("rich"):
    from rich.console import Console
    _con = Console()
    def cprint(*a, **k): _con.print(*a, **k)
else:
    def cprint(msg, **_): print(msg)

# --- third-party / local ----------------------------------------------------
from datetime import datetime
from dotenv import load_dotenv
import core.asyncio_shim                              # noqa: E402

from core.capital_manager import safe_get_tradier_buying_power
bp = safe_get_tradier_buying_power()
from core.option_selector import select_best_0dte_option
from core.telegram_alerts import send_telegram_alert
from polygon.polygon_websocket import start_polygon_listener, SPY_LIVE_PRICE, subscribe_to_option_symbol
from core.env_validator    import validate_env
from core.trade_engine     import open_position
from core.position_manager import manage_positions
from core.entry_learner    import evaluate_entry
from core.open_trade_tracker import log_open_trade, sync_open_trades_with_tradier
from core.recovery_manager   import run_recovery
from core.runtime_state      import load_runtime_state
from core.market_hours       import (
    is_market_open_now, is_0dte_trading_window_now, get_market_status_string,
)
from core.capital_manager    import (
    fetch_tradier_equity, get_tradier_buying_power, get_current_allocation,
    evaluate_drawdown_throttle, compute_position_size, poll_balance_loop, safe_fetch_tradier_equity
)
from core.logger_setup import get_logger
logger = get_logger(__name__)

# ── constants ───────────────────────────────────────────────────────────────
HEARTBEAT_EVERY     = 10
MAX_WS_IDLE_SECONDS = 300
ENTRY_THRESHOLD     = 0.55
_CYCLE_PAUSE        = 2

# ── shutdown flag ───────────────────────────────────────────────────────────
_shutdown = asyncio.Event()
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda *_: _shutdown.set())

# ── entry worker ────────────────────────────────────────────────────────────
_BULLISH = {"bullish", "trending", "stable"}
_BEARISH = {"bearish", "panic", "choppy"}

async def _entry_worker(eq_now: float, baseline: float):
    print("🔍 Evaluating entry cycle…")
    mid = SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade")
    if mid is None or not is_0dte_trading_window_now():
        return

    regime = "unknown"
    side = "call"

    try:
        opt = select_best_0dte_option("SPY", side)
        if not opt or not opt["symbol"]:
            cprint("⚠️ No valid 0DTE option found", style="yellow")
            return

        # ✅ Sanitize and subscribe to option symbol
        symbol = opt["symbol"]
        if not symbol.startswith("O:"):
            cprint(f"⚠️ missing prefix – patching with 'O:' → was: {symbol}", style="yellow")
            symbol = f"O:{symbol}"
        if not symbol.startswith("O:SPY"):
            cprint(f"❌ symbol format looks invalid: {symbol}", style="red")

            cprint(f"🧩 subscribing to {symbol}", style="magenta")
            subscribe_to_option_symbol(symbol)

        # 🎯 Evaluate entry
        meta = await evaluate_entry(
            symbol=opt["symbol"],
            default_threshold=ENTRY_THRESHOLD,
            want_meta=True
        )
    except Exception as e:
        cprint(f"❌ Entry eval error: {e}", style="red")
        return

    if not meta.get("passes"):
        cprint(f"⚪ Score {meta.get('score', 0):.2f} below {ENTRY_THRESHOLD}", style="white")
        return

    regime = meta.get("regime", "unknown")
    side = "CALL" if regime in _BULLISH else "PUT"

    alloc_base = get_current_allocation()
    throttle = evaluate_drawdown_throttle(eq_now, baseline)
    alloc_pct = round(alloc_base * throttle, 4)
    pos_frac = compute_position_size(alloc_pct, 1, 0.9)
    contracts = max(1, int(pos_frac * 10))

    send_telegram_alert(
        f"*TRADE ALERT 🟢*\n"
        f"{side} {contracts}x SPY\n"
        f"*Score:* {meta['score']:.2f} | *Regime:* {regime}\n"
        f"*Reason:* {meta.get('gpt_reasoning', 'n/a')}\n"
        f"*Alloc:* {alloc_pct:.1%}"
    )

    cprint(f"📊 score {meta['score']:.3f} regime {regime} → {side}", style="cyan")
    cprint(f"🔷 alloc {alloc_base:.3f}×{throttle:.2f}={alloc_pct:.3f} "
           f"→ kelly {pos_frac:.3f} → {contracts} contracts", style="blue")

    try:
        order = await asyncio.to_thread(open_position, opt["symbol"], contracts, "C" if side == "CALL" else "P")
        cprint(f"🟢 Order {side} {contracts}x status {order.get('status')}", style="green")
        logger.info({"event": "order_submitted", "side": side, "contracts": contracts, "resp": order})
        log_open_trade(
            opt["symbol"],
            agent="qthink",
            direction="long" if side == "CALL" else "short",
            strike=opt["strike"],
            expiry=opt["expiry"],
            meta={"allocation": alloc_pct, "contracts": contracts},
        )
    except Exception as e:
        cprint(f"❌ Order failed: {e}", style="red")
        logger.error({"event": "order_fail", "err": str(e)})

# ── heartbeat ───────────────────────────────────────────────────────────────
async def _heartbeat():
    while not _shutdown.is_set():
        try:
            eq  = fetch_tradier_equity()
            bp  = get_tradier_buying_power()
            mid = SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade")
            open_ct = len(load_runtime_state().get("open_trades", []))

            last_ts = SPY_LIVE_PRICE.get("timestamp") or 0
            last_ws = SPY_LIVE_PRICE.get("timestamp")
            ws_ok   = (last_ws is not None and time.time() - last_ws < MAX_WS_IDLE_SECONDS)

            flag    = "OPEN" if is_0dte_trading_window_now() else "CLOSED"

            cprint(f"🫀 {datetime.utcnow().time().isoformat(timespec='seconds')} | "
                   f"eq ${eq:,.0f} bp ${bp:,.0f} open {open_ct} "
                   f"mid {mid if mid else 'n/a'} | 0-DTE {flag} | WS {'✔' if ws_ok else '✖'}",
                   style="bold white")
        except Exception as hb_err:
            cprint(f"❌ heartbeat error: {hb_err}", style="red")
            logger.error({"event":"heartbeat_fail","err":str(hb_err)})
        await asyncio.sleep(HEARTBEAT_EVERY)

# ── main loop ───────────────────────────────────────────────────────────────
async def main():
    cprint("🚀 Q-ALGO hedge-fund loop booting…", style="bold green")
    load_dotenv(); validate_env()
    sync_open_trades_with_tradier(); run_recovery()

    start_polygon_listener()
    asyncio.create_task(poll_balance_loop())
    asyncio.create_task(_heartbeat())

    baseline_eq = safe_fetch_tradier_equity() or 1.0

    while not _shutdown.is_set():
        start = time.time()
        if not is_market_open_now():
            cprint(f"⏳ Market {get_market_status_string()} – sleeping 30 s", style="yellow")
            await asyncio.sleep(30); continue
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(asyncio.to_thread(manage_positions))
                tg.create_task(_entry_worker(fetch_tradier_equity(), baseline_eq))

            last_ts = SPY_LIVE_PRICE.get("timestamp") or 0
            if (time.time() - last_ts) > MAX_WS_IDLE_SECONDS:
                cprint("🔄 WS stale → restart", style="yellow"); start_polygon_listener()

            cprint(f"✅ Cycle {(time.time()-start):.2f}s", style="green")
        except Exception as exc:
            cprint(f"⚠️  Loop exception: {exc}", style="red")
            logger.exception({"event":"main_loop_exception","err":str(exc)})
            await asyncio.sleep(5)
        await asyncio.sleep(_CYCLE_PAUSE)
    cprint("👋 Graceful shutdown", style="bold")

# ── entrypoint ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
