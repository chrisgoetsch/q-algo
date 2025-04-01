from core.trade_engine import TradeEngine

# Simulated values for current and peak equity
CURRENT_EQUITY = 3_540_000
PEAK_EQUITY = 3_920_000
POSITIONS = []  # No open trades

# Instantiate and run Q Algo
engine = TradeEngine()
engine.run(CURRENT_EQUITY, PEAK_EQUITY, POSITIONS)
