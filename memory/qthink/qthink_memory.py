# qthink_memory.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("memory/qthink/pattern_memory.db")

def store_summary(trade_data: dict, summary: str, regret_score: float = 
None, tags: list = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO trade_patterns (timestamp, trade_id, summary, 
regret_score, tags)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            trade_data.get("trade_id", "unknown"),
            summary,
            regret_score if regret_score is not None else 0.0,
            ",".join(tags) if tags else None
        )
    )
    conn.commit()
    conn.close()

def retrieve_recent_summaries(limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT trade_id, summary, regret_score, tags
        FROM trade_patterns
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    )
    results = cursor.fetchall()
    conn.close()
    return [
        {
            "trade_id": r[0],
            "summary": r[1],
            "regret_score": r[2],
            "tags": r[3].split(",") if r[3] else []
        } for r in results
    ]

def retrieve_by_tag(tag: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT trade_id, summary, regret_score, tags
        FROM trade_patterns
        WHERE tags LIKE ?
        ORDER BY timestamp DESC
        """,
        (f"%{tag}%",)
    )
    results = cursor.fetchall()
    conn.close()
    return [
        {
            "trade_id": r[0],
            "summary": r[1],
            "regret_score": r[2],
            "tags": r[3].split(",") if r[3] else []
        } for r in results
    ]

