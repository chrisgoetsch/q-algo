# File: core/qthink_scenario_planner.py

import random
from datetime import datetime
import os
import json
from core.resilient_request import resilient_post

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_COMPLETION_URL = "https://api.openai.com/v1/chat/completions"

def simulate_market_scenario(base_context):
    """
    Simulates a synthetic market context to test QThink's response.
    Injects randomized changes to volatility, trend, and other factors.
    """
    scenario = base_context.copy()
    scenario["timestamp"] = datetime.utcnow().isoformat()

    # Random VIX movement
    vix = scenario.get("vix", 16.0)
    vix_change = random.uniform(-2.0, 3.0)
    scenario["vix"] = round(max(10.0, vix + vix_change), 2)

    # Simulate price momentum shift
    scenario["momentum"] = random.choice(["rising", "falling", "choppy"])

    # Simulate mesh signal confidence change
    scenario["mesh_confidence"] = round(random.uniform(0.0, 1.0), 2)

    # Simulate capital stress / drawdown environment
    scenario["capital_pressure"] = round(random.uniform(0.0, 1.0), 2)

    # Optionally: add shock flags
    scenario["macro_shock"] = random.choice([True, False])

    # Add GPT-based regime interpretation
    scenario["regime"] = classify_regime_with_gpt(scenario)

    return scenario

def classify_regime_with_gpt(scenario):
    """
    Use GPT to classify the market regime given scenario features.
    Returns a simple regime label.
    """
    if not OPENAI_API_KEY:
        return "unknown"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Given the following market context:
    {json.dumps(scenario, indent=2)}
    
    Classify the current market regime using one word: trending, volatile, stable, choppy, panic, bullish, bearish, compressing.
    """

    payload = {
        "model": os.getenv("GPT_MODEL", "gpt-4-turbo"),
        "messages": [
            {"role": "system", "content": "You are a market regime classifier."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 10
    }

    try:
        response = resilient_post(OPENAI_COMPLETION_URL, headers=headers, json=payload)
        if not response:
            return "unknown"
        result = response.json()
        label = result["choices"][0]["message"]["content"].strip().lower()
        return label
    except Exception as e:
        print(f"🛑 GPT regime classification failed: {e}")
        return "unknown"
