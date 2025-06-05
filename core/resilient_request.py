# core/resilient_request.py
# Unified HTTP request handler with retry/backoff and structured error logging

import time
from core.logger_setup import logger
import random
import requests
import logging

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

def resilient_post(url, headers=None, data=None, json=None, retries=3, backoff_factor=0.5, jitter=True):
    """
    Retry-safe POST request handler using exponential backoff and optional JSON body.
    """
    for attempt in range(retries):
        try:
            if json is not None:
                response = requests.post(url, headers=headers, json=json)
            else:
                response = requests.post(url, headers=headers, data=data)

            response.raise_for_status()
            return response
        except requests.RequestException as e:
            wait_time = backoff_factor * (2 ** attempt)
            if jitter:
                wait_time += random.uniform(0, 0.2)

            logging.warning({
                "event": "resilient_post_retry",
                "attempt": attempt + 1,
                "url": url,
                "error": str(e),
                "wait_time": round(wait_time, 2)
            })

            time.sleep(wait_time)

    logging.error({
        "event": "resilient_post_failure",
        "url": url,
        "retries": retries,
        "data": data,
        "json": json
    })
    return None
