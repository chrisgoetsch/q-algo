# File: core/reconciliation.py
# Performs account-level reconciliation between Tradier and open_trades.jsonl

import os
import json
from datetime import datetime
from core.open_trade_tracker import (
    load_open_trades, fetch_open_tradier_orders,
    remove_trade, _atomic_append_line, OPEN_TRADES_PATH, log_reconciliation
)
from core.logger_setup import logger
from core.entry_learner import score_entry
from polygon.polygon_websocket import SPY_LIVE_PRICE
from pathlib import Path

UI_STATUS_PATH = Path("logs/ui_sync_status.json")


def _write_ui_summary(summary: dict):
    try:
        summary["last_check"] = datetime.utcnow().isoformat()
        UI_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(UI_STATUS_PATH, "w") as f:
            json.dump(summary, f, indent=2)
    except Exception as e:
        logger.error({"event": "ui_sync_status_write_fail", "error": str(e)})


def enrich_trade(order: dict) -> dict:
    opt_sym = order.get("option_symbol") or order.get("symbol")
    now = datetime.utcnow().isoformat()
    base = {
        "trade_id": f"{opt_sym}_{order['id']}",
        "symbol": opt_sym,
        "quantity": int(order.get("quantity", 1)),
        "entry_time": order.get("create_date", now),
        "status": order.get("status"),
        "order_id": order["id"],
        "reconciled": True,
        "reconciled_reason": "missing_in_local",
        "entry_price": SPY_LIVE_PRICE.get("mid") or SPY_LIVE_PRICE.get("last_trade") or 0.0,
    }
    try:
        score, rationale, regime, mesh = score_entry({"symbol": opt_sym, "price": base["entry_price"]})
        base.update({
            "score": score,
            "regime": regime,
            "rationale": rationale,
            "mesh_score": mesh.get("score", 0),
            "agent_signals": mesh.get("agent_signals", {})
        })
    except Exception as e:
        logger.warning({"event": "reconcile_enrich_fail", "symbol": opt_sym, "err": str(e)})
    return base


def reconcile_open_trades():
    local_trades = load_open_trades()
    broker_trades = fetch_open_tradier_orders()

    local_ids = {t.get("order_id") for t in local_trades if t.get("order_id")}
    broker_ids = {b.get("id") for b in broker_trades if b.get("id")}

    missing_locally = [b for b in broker_trades if b.get("id") not in local_ids]
    phantom_local = [t for t in local_trades if t.get("order_id") not in broker_ids]

    added_ids = []
    removed_ids = []

    for order in missing_locally:
        opt_sym = order.get("option_symbol") or order.get("symbol")
        if not opt_sym:
            continue
        enriched = enrich_trade(order)
        _atomic_append_line(OPEN_TRADES_PATH, enriched)
        added_ids.append(order["id"])
        print(f"➕ Added missing trade from Tradier: {opt_sym} #{order['id']}")

    for phantom in phantom_local:
        trade_id = phantom.get("trade_id")
        if trade_id:
            remove_trade(trade_id)
            removed_ids.append(trade_id)
            print(f"❌ Removed phantom trade not found in Tradier: {trade_id}")

    rescored_count = 0
    rescored_trades = []
    for trade in local_trades:
        if trade.get("mesh_score") in (None, 0) or trade.get("regime") in (None, "unknown"):
            try:
                score, rationale, regime, mesh = score_entry({"symbol": trade["symbol"], "price": trade.get("entry_price", 0.0)})
                trade.update({
                    "score": score,
                    "regime": regime,
                    "rationale": rationale,
                    "mesh_score": mesh.get("score", 0),
                    "agent_signals": mesh.get("agent_signals", {})
                })
                rescored_trades.append(trade)
                rescored_count += 1
            except Exception as e:
                logger.warning({"event": "rescore_trade_fail", "symbol": trade.get("symbol"), "err": str(e)})

    try:
        OPEN_TRADES_PATH.write_text(
            "\n".join(json.dumps(t, separators=(",", ":")) for t in local_trades) + "\n"
        )
    except Exception as e:
        logger.error({"event": "open_trades_rewrite_fail", "error": str(e)})

    summary = {
        "event": "reconciliation_complete",
        "added": added_ids,
        "removed": removed_ids,
        "rescored": rescored_count,
        "summary": {
            "broker_total": len(broker_trades),
            "local_total": len(local_trades),
            "added": len(missing_locally),
            "removed": len(phantom_local),
            "rescored": rescored_count
        }
    }
    log_reconciliation(source="reconciliation", matched=summary)

    _write_ui_summary(summary["summary"])
    print("✅ Reconciliation complete.")


if __name__ == "__main__":
    reconcile_open_trades()
