# File: utils/resilient_request.py

import time
import requests
import random

MAX_RETRIES = 5
BASE_SLEEP_SECONDS = 1

def resilient_get(url, headers=None, params=None):
    """
    Perform a resilient HTTP GET with retry and exponential backoff.
    """
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response
            else:
                print(f"[Resilient Request] Non-200 response ({response.status_code}). Retrying...")
        except requests.RequestException as e:
            print(f"[Resilient Request] Exception during GET: {e}. Retrying...")

        retries += 1
        sleep_time = BASE_SLEEP_SECONDS * (2 ** retries) + random.uniform(0, 1)
        time.sleep(sleep_time)

    print(f"[Resilient Request] GET failed after {MAX_RETRIES} retries.")
    return None

def resilient_post(url, headers=None, data=None):
    """
    Perform a resilient HTTP POST with retry and exponential backoff.
    """
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200 or response.status_code == 201:
                return response
            else:
                print(f"[Resilient Request] Non-2xx response ({response.status_code}). Retrying...")
        except requests.RequestException as e:
            print(f"[Resilient Request] Exception during POST: {e}. Retrying...")

        retries += 1
        sleep_time = BASE_SLEEP_SECONDS * (2 ** retries) + random.uniform(0, 1)
        time.sleep(sleep_time)

    print(f"[Resilient Request] POST failed after {MAX_RETRIES} retries.")
    return None
