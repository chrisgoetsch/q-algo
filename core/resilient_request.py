# core/resilient_request.py
# Unified HTTP request handler with retry/backoff and structured error logging

import time
import requests
from core.logger_setup import logger

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 2  # seconds exponent base
DEFAULT_TIMEOUT = 10  # seconds per request

def resilient_request(method, url, retries=DEFAULT_RETRIES, backoff=DEFAULT_BACKOFF,
                      timeout=DEFAULT_TIMEOUT, **kwargs):
    """
    Sends an HTTP request with exponential backoff retry.
    Returns a Response on success, or None if all attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"HTTP {method} → {url} (attempt {attempt}/{retries})")
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error({
                "event": "api_error",
                "method": method,
                "url": url,
                "attempt": attempt,
                "error": str(e)
            })
            # on last failure, break; else back off
            if attempt < retries:
                sleep_time = backoff ** attempt
                logger.info(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
    logger.critical({
        "event": "api_failure",
        "method": method,
        "url": url,
        "retries": retries
    })
    return None

def resilient_get(url, **kwargs):
    return resilient_request("GET", url, **kwargs)

def resilient_post(url, **kwargs):
    return resilient_request("POST", url, **kwargs)
