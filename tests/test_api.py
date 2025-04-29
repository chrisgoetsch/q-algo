# File: tests/test_api.py

import pytest
from brokers.tradier_client import get_quote
from core.live_price_tracker import get_current_spy_price

@pytest.mark.asyncio
def test_tradier_get_quote():
    """
    Test that Tradier API can return a live quote for SPY.
    """
    quote_data = get_quote("SPY")
    assert quote_data is not None, "Tradier quote returned None"
    assert "quotes" in quote_data, "No 'quotes' key in Tradier response"
    assert "quote" in quote_data["quotes"], "No 'quote' key inside 'quotes' response"

def test_polygon_live_price_tracker():
    """
    Test that the live price tracker can return a SPY price (from WebSocket or fallback).
    """
    spy_price = get_current_spy_price()
    assert spy_price is not None, "Live price tracker returned None for SPY price"
    assert spy_price > 0, "Live SPY price is non-positive"
