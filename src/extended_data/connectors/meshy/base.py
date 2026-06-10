"""Base HTTP client - auth, retries, rate limiting.

This module handles ALL the HTTP infrastructure. API modules import this.

Uses InputProvider for credential loading, consistent with all other
extended-data. Credentials can come from:
- Environment variables (MESHY_API_KEY)
- Direct parameters
- stdin JSON input
"""

from __future__ import annotations

import threading
import time

from typing import Any

import httpx

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from extended_data.inputs import InputProvider


class RateLimitError(Exception):
    """Raised when API rate limit is hit."""


class MeshyAPIError(Exception):
    """Raised when API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


# Global client state
_client: httpx.Client | None = None
_inputs: InputProvider | None = None
_last_request_time: float = 0
_rate_limit_lock = threading.Lock()
_min_request_interval: float = 0.5  # 500ms between requests

BASE_URL = "https://api.meshy.ai"


def _get_inputs() -> InputProvider:
    """Get or create the InputProvider instance."""
    global _inputs
    if _inputs is None:
        _inputs = InputProvider()
    return _inputs


def configure(api_key: str | None = None, **kwargs: Any) -> None:
    """Configure Meshy API credentials.

    Args:
        api_key: Meshy API key (overrides environment variable)
        **kwargs: Additional inputs to merge
    """
    global _inputs
    inputs = {"MESHY_API_KEY": api_key} if api_key else {}
    inputs.update(kwargs)
    if _inputs is None:
        _inputs = InputProvider(inputs=inputs)
    else:
        _inputs.merge_inputs(inputs)


def get_api_key() -> str:
    """Get API key from InputProvider (env vars, direct inputs, or stdin)."""
    inputs = _get_inputs()
    return inputs.get_input("MESHY_API_KEY", required=True)


def get_client() -> httpx.Client:
    """Get or create HTTP client."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=300.0)
    return _client


def close() -> None:
    """Close the HTTP client."""
    global _client
    if _client:
        _client.close()
        _client = None


def _rate_limit() -> None:
    """Simple rate limiting with thread safety."""
    global _last_request_time

    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < _min_request_interval:
            time.sleep(_min_request_interval - elapsed)
        _last_request_time = time.time()


def _headers() -> dict[str, str]:
    """Build request headers."""
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


@retry(
    retry=retry_if_exception_type((RateLimitError, httpx.TimeoutException)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def request(
    method: str,
    endpoint: str,
    *,
    version: str = "v2",
    **kwargs: Any,
) -> httpx.Response:
    """Make HTTP request with retries and rate limiting.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., "text-to-3d")
        version: API version (v1 or v2)
        **kwargs: Passed to httpx.request (json, params, etc.)

    Returns:
        httpx.Response

    Raises:
        RateLimitError: On 429 (will retry)
        MeshyAPIError: On other API errors
    """
    _rate_limit()

    url = f"{BASE_URL}/openapi/{version}/{endpoint}"
    response = get_client().request(method, url, headers=_headers(), **kwargs)

    # Handle rate limiting
    if response.status_code == 429:
        retry_after = response.headers.get("retry-after", "5")
        try:
            time.sleep(float(retry_after))
        except ValueError:
            time.sleep(5)
        msg = f"Rate limit exceeded, retried after {retry_after}s"
        raise RateLimitError(msg)

    # Retry on 5xx
    if response.status_code >= 500:
        msg = f"Server error {response.status_code}"
        raise RateLimitError(msg)

    # Raise on 4xx
    if response.status_code >= 400:
        msg = f"API error: {response.text}"
        raise MeshyAPIError(
            msg,
            status_code=response.status_code,
        )

    return response


def download(url: str, output_path: str) -> int:
    """Download file from URL.

    Args:
        url: URL to download from
        output_path: Local path to save to

    Returns:
        File size in bytes
    """
    import os as _os

    dirname = _os.path.dirname(output_path)
    if dirname:
        _os.makedirs(dirname, exist_ok=True)

    response = httpx.get(url)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    return len(response.content)
