#!/bin/bash

echo "🔄 Sourcing environment..."
source .env

echo "🚀 Running Preflight Check..."
python3 preflight_check.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "🛑 Preflight check failed. Q-ALGO will not launch."
  exit 1
fi

echo "✅ Preflight passed. Launching Q-ALGO..."
python3 run_q_algo_live.py
