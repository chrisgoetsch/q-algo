# save_tokens.py

import os
from dotenv import load_dotenv

load_dotenv()

# Paste your new tokens here
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"
REFRESH_TOKEN = "YOUR_REFRESH_TOKEN_HERE"

env_path = ".env"

# Read current lines
with open(env_path, "r") as f:
    lines = f.readlines()

# Overwrite or add the token lines
with open(env_path, "w") as f:
    for line in lines:
        if line.startswith("TRADESTATION_ACCESS_TOKEN"):
            continue
        if line.startswith("TRADESTATION_REFRESH_TOKEN"):
            continue
        f.write(line)
    f.write(f"TRADESTATION_ACCESS_TOKEN={ACCESS_TOKEN}\n")
    f.write(f"TRADESTATION_REFRESH_TOKEN={REFRESH_TOKEN}\n")

print("✅ Tokens saved to .env")
