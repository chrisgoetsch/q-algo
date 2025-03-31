from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import datetime

load_dotenv()
app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "Q Algo engine running",
        "mode": os.getenv("MODE", "unknown"),
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/token-status")
def token_status():
    return {
        "tradeStationClientId": bool(os.getenv("TRADESTATION_CLIENT_ID")),
        "polygonKeyLoaded": bool(os.getenv("POLYGON_API_KEY")),
        "account": os.getenv("TRADESTATION_ACCOUNT_ID", "unknown"),
        "tokenHealth": "manual check required unless connected to API"
    }

@app.get("/live-trade")
def live_trade_test():
    return JSONResponse(status_code=501, content={"message": "Live trade logic not yet connected."})

