# ──────────────────────────────────────────────────────────────────────────────
# File: core/resilient_request.py      (v2-HF: Hedge-Fund hardened)
# ──────────────────────────────────────────────────────────────────────────────
"""
Thin HTTP helpers with built-in exponential back-off, jitter and structured
logging.  Used throughout the Q-ALGO stack for *every* outbound REST call.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, Mapping, Sequence

import backoff
import requests

from core.logger_setup import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _log(event: str, **kv):
    logger.info({"src": "resilient_http", "event": event, **kv})


def _jitter(value: float, pct: float = 0.25) -> float:
    """Return *value* ± *pct*% random jitter."""
    return value * random.uniform(1 - pct, 1 + pct)


# ---------------------------------------------------------------------------
# Public decorator
# ---------------------------------------------------------------------------

def backoff_retry(
    *,
    exceptions: Sequence[type[Exception]] | tuple[type[Exception], ...] = (Exception,),
    max_time: int = 30,
    giveup: Any | None = None,
):
    """
    Decorator factory that retries a function with exponential back-off + jitter
    on the supplied *exceptions*.

    Example
    -------
    ```python
    @backoff_retry(max_time=10)
    def flaky_io_call():
        ...
    ```
    """
    return backoff.on_exception(
        backoff.expo,
        exceptions,
        max_time=max_time,
        jitter=_jitter,
        giveup=giveup,
    )


# ---------------------------------------------------------------------------
# Low-level HTTP wrappers
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = 10  # seconds


@backoff_retry(max_time=20)
def resilient_get(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> requests.Response:
    """GET with retries, logging and sane defaults."""
    _log("http_get", url=url, params=params)
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)

    if resp.status_code >= 500:
        # trigger back-off retry
        _log("server_error", code=resp.status_code, body=resp.text[:200])
        resp.raise_for_status()

    _log("http_ok", code=resp.status_code, ms=int(resp.elapsed.total_seconds() * 1000))
    return resp


@backoff_retry(max_time=20)
def resilient_post(
    url: str,
    *,
    data: Mapping[str, Any] | None = None,
    json_body: Any | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> requests.Response:
    """POST with retries, logging and sane defaults."""
    _log("http_post", url=url, json=bool(json_body), data_keys=list(data or {}))
    resp = requests.post(
        url,
        data=data,
        json=json_body,
        headers=headers,
        timeout=timeout,
    )

    if resp.status_code >= 500:
        _log("server_error", code=resp.status_code, body=resp.text[:200])
        resp.raise_for_status()

    _log("http_ok", code=resp.status_code, ms=int(resp.elapsed.total_seconds() * 1000))
    return resp
