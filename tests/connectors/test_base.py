"""Tests for base connector data helpers."""

from __future__ import annotations

import builtins

from unittest.mock import MagicMock

import httpx
import pytest

from extended_data.connectors.base import VendorConnectorBase
from extended_data.containers import ExtendedDict, ExtendedString
from extended_data.logging import Logging


class ExampleConnector(VendorConnectorBase):
    """Small connector used to exercise the base class."""

    BASE_URL = "https://api.example.com"


def _connector() -> ExampleConnector:
    logger = MagicMock(spec=Logging)
    logger.logger = MagicMock()
    return ExampleConnector(from_environment=False, logger=logger)


def test_connector_default_logging_does_not_create_cwd_log_file(tmp_path, monkeypatch) -> None:
    """Default connector construction should not write log files as a side effect."""
    monkeypatch.chdir(tmp_path)

    connector = ExampleConnector(from_environment=False)

    assert connector.logging.enable_file is False
    assert not (tmp_path / "ExampleConnector.log").exists()


def test_decode_response_promotes_json_to_extended_containers() -> None:
    """JSON responses flow through the Tier 2 container bridge."""
    connector = _connector()
    response = httpx.Response(
        200,
        content=b'{"service":{"name":"api"}}',
        headers={"content-type": "application/json; charset=utf-8"},
    )

    data = connector.decode_response(response)

    assert isinstance(data, ExtendedDict)
    assert isinstance(data["service"], ExtendedDict)
    assert isinstance(data["service"]["name"], ExtendedString)
    assert data["service"]["name"].upper_first() == "Api"


def test_decode_response_can_return_plain_json() -> None:
    """Response decoding can opt out of extended containers."""
    connector = _connector()
    response = httpx.Response(
        200,
        content=b'{"service":{"name":"api"}}',
        headers={"content-type": "application/vnd.example+json"},
    )

    data = connector.decode_response(response, as_extended=False)

    assert data == {"service": {"name": "api"}}
    assert not isinstance(data["service"]["name"], ExtendedString)


def test_decode_response_promotes_text_to_extended_string() -> None:
    """Text responses become ExtendedString values by default."""
    connector = _connector()
    response = httpx.Response(
        200,
        content=b"api response",
        headers={"content-type": "text/plain"},
    )

    data = connector.decode_response(response)

    assert isinstance(data, ExtendedString)
    assert data.to_snake_case() == "api_response"


def test_decode_response_preserves_unknown_binary_data() -> None:
    """Unknown binary responses are left as bytes."""
    connector = _connector()
    response = httpx.Response(
        200,
        content=b"\x00\x01\x02",
        headers={"content-type": "application/octet-stream"},
    )

    assert connector.decode_response(response) == b"\x00\x01\x02"


def test_request_data_decodes_response_body() -> None:
    """request_data combines the raw request primitive with response decoding."""
    connector = _connector()
    mock_client = MagicMock()
    mock_client.request.return_value = httpx.Response(
        200,
        content=b'{"ok":true}',
        headers={"content-type": "application/json"},
    )
    connector._client = mock_client

    data = connector.request_data("GET", "/status")

    assert data == {"ok": True}
    assert isinstance(data, ExtendedDict)
    mock_client.request.assert_called_once()
    assert mock_client.request.call_args.args[0] == "GET"
    assert mock_client.request.call_args.args[1] == "https://api.example.com/status"


def test_request_uses_connector_max_retries(mocker) -> None:
    """Connector subclasses control the retry attempt count."""

    class TwoAttemptConnector(ExampleConnector):
        MAX_RETRIES = 2

    connector = TwoAttemptConnector(from_environment=False)
    mocker.patch("extended_data.connectors.base.time.sleep")
    mock_client = MagicMock()
    mock_client.request.side_effect = [
        httpx.Response(500, content=b"temporary failure"),
        httpx.Response(200, content=b"ok"),
    ]
    connector._client = mock_client

    response = connector.request("GET", "/status")

    assert response.status_code == 200
    assert mock_client.request.call_count == 2


def test_request_rejects_invalid_max_retries() -> None:
    """Invalid retry configuration fails before issuing a request."""

    class InvalidRetryConnector(ExampleConnector):
        MAX_RETRIES = 0

    connector = InvalidRetryConnector(from_environment=False)
    mock_client = MagicMock()
    connector._client = mock_client

    with pytest.raises(ValueError, match="MAX_RETRIES must be at least 1"):
        connector.request("GET", "/status")

    mock_client.request.assert_not_called()


def test_get_tools_requires_langchain_extra(monkeypatch) -> None:
    """Base LangChain tool export should fail visibly when langchain-core is missing."""
    connector = _connector()
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "langchain_core.tools":
            raise ImportError("blocked langchain-core")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match=r"extended-data\[langchain\]"):
        connector.get_tools()
