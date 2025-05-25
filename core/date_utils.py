# File: core/date_utils.py
from datetime import datetime

def get_today_expiry():
    return datetime.now().strftime("%Y%m%d")
