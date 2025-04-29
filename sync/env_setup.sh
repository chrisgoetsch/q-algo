#!/bin/bash

cd ~/Q-ALGO-v2

echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "🧩 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "✅ Environment setup complete."

