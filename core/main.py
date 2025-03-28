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
nano requirements.txt
fastapi
uvicorn
requests
python-dotenv
nano .env.example
TRADESTATION_CLIENT_ID=your-client-id
TRADESTATION_CLIENT_SECRET=your-client-secret
TRADESTATION_REDIRECT_URI=https://your-domain.com/callback
TRADESTATION_ACCOUNT_ID=SIM3001509F
POLYGON_API_KEY=your-polygon-api-key
MODE=live
echo "# Q Algo\nLive SPY trading engine backend" > README.md
git init
git remote add origin https://github.com/YOUR-USERNAME/Q-algo.git
git add .
git commit -m "Initial commit – created Q Algo backend on EC2"
git branch -M main
git push -u origin main

