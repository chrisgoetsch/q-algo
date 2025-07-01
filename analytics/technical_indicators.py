
# File: analytics/technical_indicators.py

import pandas as pd
import numpy as np
import requests
from polygon.polygon_rest import get_historic_bars

def get_rsi(symbol: str = "SPY", period: int = 14) -> float | None:
    try:
        bars = get_historic_bars(symbol, timespan="minute", limit=period+1)
        if not bars or len(bars) < period + 1:
            return None

        df = pd.DataFrame(bars)
        df['close'] = df['c']

        delta = df['close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period).mean().iloc[-1]
        avg_loss = pd.Series(loss).rolling(window=period).mean().iloc[-1]

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi), 2)
    except Exception as e:
        print(f"⚠️ RSI calculation failed: {e}")
        return None

def is_vwap_reclaim(symbol: str = "SPY") -> bool:
    try:
        bars = get_historic_bars(symbol, timespan="minute", limit=20)
        if not bars or len(bars) < 2:
            return False
        df = pd.DataFrame(bars)
        df['vwap'] = (df['v'] * (df['h'] + df['l'] + df['c']) / 3).cumsum() / df['v'].cumsum()
        last_price = df['c'].iloc[-1]
        last_vwap = df['vwap'].iloc[-1]
        return last_price > last_vwap
    except Exception as e:
        print(f"⚠️ VWAP reclaim check failed: {e}")
        return False
