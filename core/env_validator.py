# env_validator.py
# Validates required environment variables at startup and aborts on failure.

import os
import sys
from dotenv import load_dotenv

def validate_env():
    # Load the specified .env file (default to .env)
    dotenv_path = os.getenv('ENV_PATH', '.env')
    if not os.path.isfile(dotenv_path):
        print(f"❌ Missing environment file at '{dotenv_path}'")
        sys.exit(1)

    load_dotenv(dotenv_path)

    broker = os.getenv("BROKER", "tradier").lower()

    # Define required variables and their descriptions
    required = {
        'POLYGON_API_KEY': 'Polygon.io API key',
        'OPENAI_API_KEY': 'OpenAI API key',
        'TRADIER_ACCESS_TOKEN': 'Tradier access token',
        'TRADIER_ACCOUNT_ID': 'Tradier account ID',
    }

    if broker == "tradestation":
        required.update({
            'TRADESTATION_CLIENT_ID': 'TradeStation API client ID',
            'TRADESTATION_CLIENT_SECRET': 'TradeStation API client secret',
            'TRADESTATION_ACCOUNT_ID': 'TradeStation account ID',
            'TRADESTATION_ACCESS_TOKEN': 'TradeStation access token',
            'TRADESTATION_REFRESH_TOKEN': 'TradeStation refresh token',
        })

    missing = []
    for var, desc in required.items():
        val = os.getenv(var)
        if not val or val.startswith('your_') or 'placeholder' in val.lower():
            missing.append(f"{var} ({desc})")

    if missing:
        print("❌ Missing or invalid environment variables:")
        for item in missing:
            print(f"   • {item}")
        sys.exit(1)

# Run validation if this module is executed directly
if __name__ == "__main__":
    validate_env()
