import os
import json
import datetime
import requests

TOKENS_FILE = ".env"

def load_tokens():
    with open(TOKENS_FILE, "r") as f:
        lines = f.readlines()
    tokens = {}
    for line in lines:
        if "=" in line:
            key, value = line.strip().split("=", 1)
            tokens[key] = value
    return tokens

def update_env_var(key, value):
    with open(TOKENS_FILE, "r") as f:
        lines = f.readlines()
    with open(TOKENS_FILE, "w") as f:
        found = False
        for line in lines:
            if line.startswith(key + "="):
                f.write(f"{key}={value}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"{key}={value}\n")

def token_expired():
    tokens = load_tokens()
    expiration = tokens.get("ACCESS_TOKEN_EXPIRES_AT")
    if not expiration:
        return True
    try:
        expire_time = datetime.datetime.fromisoformat(expiration)
    except ValueError:
        return True
    return datetime.datetime.now() >= expire_time

def refresh_token():
    tokens = load_tokens()
    refresh_token = tokens.get("REFRESH_TOKEN")
    client_id = tokens.get("CLIENT_ID")
    redirect_uri = tokens.get("REDIRECT_URI")

    if not refresh_token:
        raise Exception("Missing REFRESH_TOKEN in .env")

    url = "https://signin.tradestation.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
        "redirect_uri": redirect_uri
    }

    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        new_tokens = response.json()
        update_env_var("ACCESS_TOKEN", new_tokens["access_token"])
        update_env_var("REFRESH_TOKEN", new_tokens["refresh_token"])
        expire_time = datetime.datetime.now() + datetime.timedelta(seconds=new_tokens["expires_in"])
        update_env_var("ACCESS_TOKEN_EXPIRES_AT", expire_time.isoformat())
        print("🔁 Token refreshed successfully.")
    else:
        raise Exception(f"Failed to refresh token: {response.text}")
