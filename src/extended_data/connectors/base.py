"""Base class for all extended data connectors.

This module provides VendorConnectorBase - the foundation for ALL connectors
in this library. It extends InputProvider and provides:

1. Credential loading from env vars, stdin, or direct inputs
2. HTTP client with retries and rate limiting
3. MCP server scaffolding
4. LangChain tool registration helpers

ALL connectors should extend this class instead of InputProvider directly.

Usage:
    from extended_data.connectors.base import VendorConnectorBase

    class MyConnector(VendorConnectorBase):
        API_KEY_ENV = "MY_API_KEY"  # Required env var name
        BASE_URL = "https://api.example.com"

        def __init__(self, api_key: str | None = None, **kwargs):
            super().__init__(**kwargs)
            self._api_key = api_key or self.get_input(self.API_KEY_ENV, required=True)

        def my_operation(self) -> dict:
            return self.request("GET", "/endpoint")
"""

from __future__ import annotations

import builtins
import sys
import threading
import time

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

import httpx

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from extended_data.inputs import InputProvider
from extended_data.logging import Logging


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    from langchain_core.tools import StructuredTool
    from pydantic import BaseModel


class RateLimitError(Exception):
    """Raised when API rate limit is hit - triggers retry."""


class ConnectorAPIError(Exception):
    """Raised when API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class VendorConnectorBase(InputProvider, ABC):
    """Base class for all extended data connectors.

    Provides:
    - InputProvider for credential loading (env, stdin, direct)
    - HTTP client with connection pooling
    - Automatic retries with exponential backoff
    - Rate limiting
    - MCP tool registration scaffolding
    - LangChain tool helpers

    Class Attributes:
        BASE_URL: API base URL (required for HTTP connectors)
        API_KEY_ENV: Environment variable name for API key
        TIMEOUT: HTTP timeout in seconds (default 300)
        MIN_REQUEST_INTERVAL: Minimum seconds between requests (rate limiting)
        MAX_RETRIES: Maximum retry attempts (default 5)

    Instance Attributes:
        logger: Logger instance
        _client: HTTP client (lazy-initialized)
        _tools: Registered LangChain tools
    """

    # Class-level configuration - override in subclasses
    BASE_URL: ClassVar[str] = ""
    API_KEY_ENV: ClassVar[str] = ""
    TIMEOUT: ClassVar[float] = 300.0
    MIN_REQUEST_INTERVAL: ClassVar[float] = 0.0  # No rate limit by default
    MAX_RETRIES: ClassVar[int] = 5

    # Per-connector-type rate limiting state
    # Each subclass gets its own lock and timestamp to avoid cross-connector interference.
    # This is intentionally class-level (not instance-level) so all instances of the same
    # connector type share rate limiting, but different connector types are independent.
    _rate_limit_locks: ClassVar[dict[builtins.type[VendorConnectorBase], threading.Lock]] = {}
    _last_request_times: ClassVar[dict[builtins.type[VendorConnectorBase], float]] = {}

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        logger: Logging | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the connector.

        Args:
            api_key: API key (overrides environment variable)
            base_url: Base URL (overrides class default)
            timeout: HTTP timeout in seconds
            logger: Logger instance
            **kwargs: Passed to InputProvider
        """
        super().__init__(**kwargs)

        # Set up logging
        self.logging = logger or Logging(logger_name=self.__class__.__name__)
        self.logger = self.logging.logger

        # Configuration with fallbacks
        self._base_url = base_url or self.BASE_URL
        self._timeout = timeout or self.TIMEOUT

        # Load API key from inputs if API_KEY_ENV is set
        self._api_key: str | None = None
        if api_key:
            self._api_key = api_key
        elif self.API_KEY_ENV:
            self._api_key = self.get_input(self.API_KEY_ENV, required=False)

        # Lazy-initialized HTTP client
        self._client: httpx.Client | None = None

        # Tool registry for LangChain/MCP
        self._tools: list[StructuredTool] = []
        self._tool_functions: dict[str, Callable[..., Any]] = {}
        self._tool_schemas: dict[str, builtins.type[BaseModel]] = {}

    @property
    def api_key(self) -> str:
        """Get API key, raising if not set."""
        if not self._api_key:
            msg = f"{self.API_KEY_ENV or 'API key'} not set"
            raise ValueError(msg)
        return self._api_key

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: builtins.type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - close client."""
        self.close()

    # -------------------------------------------------------------------------
    # HTTP Methods with Retry and Rate Limiting
    # -------------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests.

        Rate limiting is per-connector-type (not global), so different connector
        types (e.g., MeshyConnector vs AWSConnector) don't interfere with each other.
        """
        if self.MIN_REQUEST_INTERVAL <= 0:
            return

        connector_type = type(self)

        # Lazily initialize lock and timestamp for this connector type
        if connector_type not in self._rate_limit_locks:
            self._rate_limit_locks[connector_type] = threading.Lock()
            self._last_request_times[connector_type] = 0.0

        with self._rate_limit_locks[connector_type]:
            now = time.time()
            elapsed = now - self._last_request_times[connector_type]
            if elapsed < self.MIN_REQUEST_INTERVAL:
                time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
            self._last_request_times[connector_type] = time.time()

    def _build_headers(self) -> dict[str, str]:
        """Build request headers. Override in subclasses for custom auth."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        base = self._base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base}/{endpoint}"

    @retry(
        retry=retry_if_exception_type((RateLimitError, httpx.TimeoutException)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retries and rate limiting.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to BASE_URL)
            headers: Additional headers (merged with defaults)
            **kwargs: Passed to httpx.request (json, params, data, etc.)

        Returns:
            httpx.Response

        Raises:
            RateLimitError: On 429 (will retry automatically)
            ConnectorAPIError: On other API errors
        """
        self._rate_limit()

        url = self._build_url(endpoint)
        request_headers = self._build_headers()
        if headers:
            request_headers.update(headers)

        response = self.client.request(method, url, headers=request_headers, **kwargs)

        # Handle rate limiting - retry
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after", "5")
            try:
                time.sleep(float(retry_after))
            except ValueError:
                time.sleep(5)
            msg = f"Rate limit exceeded, retrying after {retry_after}s"
            raise RateLimitError(msg)

        # Retry on 5xx server errors
        if response.status_code >= 500:
            msg = f"Server error {response.status_code}: {response.text}"
            raise RateLimitError(msg)

        # Raise on 4xx client errors (don't retry)
        if response.status_code >= 400:
            msg = f"API error {response.status_code}: {response.text}"
            raise ConnectorAPIError(msg, status_code=response.status_code)

        return response

    def get(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """HTTP GET request."""
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """HTTP POST request."""
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """HTTP PUT request."""
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """HTTP DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """HTTP PATCH request."""
        return self.request("PATCH", endpoint, **kwargs)

    # -------------------------------------------------------------------------
    # File Downloads
    # -------------------------------------------------------------------------

    def download(self, url: str, output_path: str) -> int:
        """Download file from URL.

        Args:
            url: URL to download from
            output_path: Local path to save to

        Returns:
            File size in bytes
        """
        import os

        dirname = os.path.dirname(output_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        # Use a separate client for downloads (different timeout)
        response = httpx.get(url, timeout=600.0)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        return len(response.content)

    # -------------------------------------------------------------------------
    # LangChain Tool Registration
    # -------------------------------------------------------------------------

    def register_tool(
        self,
        func: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
        schema: builtins.type[BaseModel] | None = None,
    ) -> None:
        """Register a function as a LangChain tool.

        Args:
            func: The function to register
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            schema: Pydantic model for input schema.
        """
        tool_name = name or func.__name__
        self._tool_functions[tool_name] = func
        if schema:
            self._tool_schemas[tool_name] = schema

    def get_tools(self) -> list[StructuredTool]:
        """Get all registered tools as LangChain StructuredTools.

        Returns:
            List of StructuredTool instances
        """
        try:
            from langchain_core.tools import StructuredTool
        except ImportError:
            self.logger.warning("langchain-core not installed, returning empty tools list")
            return []

        tools = []
        for name, func in self._tool_functions.items():
            tool = StructuredTool.from_function(
                func=func,
                name=name,
                description=func.__doc__ or f"Tool: {name}",
            )
            tools.append(tool)

        return tools

    # -------------------------------------------------------------------------
    # AI Tool Definition Helpers
    # -------------------------------------------------------------------------

    def get_ai_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions in Vercel AI SDK-compatible format.

        Returns:
            List of AI tool definition dicts
        """
        import inspect

        from extended_data.connectors.ai_tools import get_pydantic_schema

        definitions = []
        for name, func in self._tool_functions.items():
            # Use Pydantic schema if available
            if name in self._tool_schemas:
                input_schema = get_pydantic_schema(self._tool_schemas[name])
            else:
                # Fallback to inspect-based schema generation
                sig = inspect.signature(func)
                properties = {}
                required = []

                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    param_type = "string"
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation in (int, float):
                            param_type = "number"
                        elif param.annotation is bool:
                            param_type = "boolean"

                    properties[param_name] = {"type": param_type}

                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)

                input_schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }

            definitions.append(
                {
                    "name": name,
                    "description": func.__doc__ or f"Tool: {name}",
                    "inputSchema": input_schema,
                }
            )

        return definitions

    def handle_ai_tool_call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Handle an AI tool call.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if name not in self._tool_functions:
            msg = f"Unknown tool: {name}"
            raise ValueError(msg)

        func = self._tool_functions[name]
        return func(**arguments)
