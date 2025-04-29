# q_0dte_memory.py
# Logs real-time SPY 0DTE market state snapshots to SQLite for pattern 
recognition and learning

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("memory/q0dte/q0dte_snapshots.db")

def store_snapshot(state: dict, pattern_tag: str = None, result: str = 
None):
    """Logs a single market state with optional pattern tag and 
outcome."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshot_patterns (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            spy_price REAL,
            vix REAL,
            gex REAL,
            dex REAL,
            vwap_diff REAL,
            skew REAL,
            pattern_tag TEXT,
            result TEXT
        );
        """
    )

    cursor.execute(
        """
        INSERT INTO snapshot_patterns (
            timestamp, spy_price, vix, gex, dex,
            vwap_diff, skew, pattern_tag, result
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            state.get("spy_price"),
            state.get("vix"),
            state.get("gex"),
            state.get("dex"),
            state.get("vwap_diff"),
            state.get("skew"),
            pattern_tag,
            result
        )
    )

    conn.commit()
    conn.close()

def fetch_recent_snapshots(limit: int = 25):
    """Fetch recent market states for review or backtesting."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT timestamp, spy_price, vix, gex, dex,
               vwap_diff, skew, pattern_tag, result
        FROM snapshot_patterns
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "spy_price": r[1],
            "vix": r[2],
            "gex": r[3],
            "dex": r[4],
            "vwap_diff": r[5],
            "skew": r[6],
            "pattern_tag": r[7],
            "result": r[8]
        } for r in rows
    ]

