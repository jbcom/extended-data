"""Tests for base connector data helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx

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
