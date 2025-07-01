# File: analytics/build_training_dataset.py
# Purpose: Build unified SPY 0DTE training dataset from logs

import os
import json
import pandas as pd
from glob import glob
from datetime import datetime

# Paths to input logs
MEMORY_LOG = "logs/q_0dte_memory.jsonl"
SCORE_LOG = "logs/qthink_score_breakdown.jsonl"
CLOSED_TRADES = "logs/closed_trades.jsonl"
SYNC_LOG = "logs/sync_log.jsonl"
MESH_LOG = "logs/mesh_signals.jsonl"

# Output CSV
OUTPUT_CSV = "analytics/spy_0dte_training_dataset.csv"

# Helper to load JSONL as list of dicts
def load_jsonl(path):
    if not os.path.exists(path): return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

# Load logs
mem = load_jsonl(MEMORY_LOG)
scores = load_jsonl(SCORE_LOG)
trades = load_jsonl(CLOSED_TRADES)
sync = load_jsonl(SYNC_LOG)
mesh = load_jsonl(MESH_LOG)

# Build dataframe from memory snapshots
rows = []
for snap in mem:
    ts = snap.get("timestamp")
    features = snap.get("state_vector", snap)
    features["timestamp"] = ts
    features["pattern_tag"] = snap.get("pattern_tag", "unknown")
    rows.append(features)

df = pd.DataFrame(rows)

# Join mesh scores and sync outcomes by nearest timestamp
score_df = pd.DataFrame(scores)
mesh_df = pd.DataFrame(mesh)
trade_df = pd.DataFrame(trades)
sync_df = pd.DataFrame(sync)

# Normalize timestamps
for d in (df, score_df, mesh_df, trade_df, sync_df):
    if "timestamp" in d.columns:
        d["timestamp"] = pd.to_datetime(d["timestamp"])

# Merge features with outcome (based on sync/trade logs)
if not trade_df.empty:
    df = pd.merge_asof(df.sort_values("timestamp"), trade_df.sort_values("timestamp"), direction="nearest", tolerance=pd.Timedelta("5min"))
if not score_df.empty:
    df = pd.merge_asof(df.sort_values("timestamp"), score_df.sort_values("timestamp"), direction="nearest", tolerance=pd.Timedelta("5min"))
if not mesh_df.empty:
    mesh_pivot = mesh_df.pivot_table(index="timestamp", columns="agent", values="agent_score")
    df = df.join(mesh_pivot, on="timestamp")

# Only keep rows with valid outcome if 'pnl' is present
if "pnl" in df.columns:
    df = df[df["pnl"].notnull()]
else:
    print("⚠️ 'pnl' column not found — skipping filter.")

# Save
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Training dataset written → {OUTPUT_CSV} | Rows: {len(df)}")
