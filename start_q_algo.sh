#!/bin/bash
# File: start_q_algo.sh — Q-ALGO V2 Startup Script

echo "🔄 Activating virtual environment..."
source .venv/bin/activate || { echo "❌ Failed to activate venv"; exit 1; }

echo "🔄 Sourcing environment..."
export $(grep -v '^#' .env | xargs)

echo "🚀 Running Preflight Check..."
python3 preflight_check.py || { echo "❌ Preflight failed. Aborting."; exit 1; }

echo "✅ Preflight complete. Starting Q-ALGO live loop..."
python3 run_q_algo_live_async.py
