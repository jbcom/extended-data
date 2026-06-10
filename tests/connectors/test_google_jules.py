"""Tests for the Google Jules connector."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from extended_data.connectors.google.jules import JulesConnector, JulesError, Session
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


def _response(payload: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("GET", "https://jules.googleapis.com/v1alpha/test"),
    )


def _text_response(text: str, status_code: int = 500, url: str = "https://jules.googleapis.com/v1alpha/test") -> httpx.Response:
    return httpx.Response(
        status_code,
        text=text,
        request=httpx.Request("GET", url),
    )


def test_session_pull_request_model_property() -> None:
    """The standalone Session model still exposes typed convenience properties."""
    session = Session(
        name="sessions/123",
        outputs=[
            {
                "pullRequest": {
                    "url": "https://github.com/org/repo/pull/1",
                    "title": "Fix",
                }
            }
        ],
    )

    assert session.pull_request is not None
    assert session.pull_request.url == "https://github.com/org/repo/pull/1"
    assert session.pull_request.title == "Fix"


def test_list_sources_returns_extended_payloads() -> None:
    """Jules source lists are promoted into extended containers."""
    connector = JulesConnector(api_key="test-key")
    connector.get = MagicMock(
        return_value=_response(
            {
                "sources": [
                    {
                        "name": "sources/github/org/repo",
                        "id": "repo",
                        "githubRepo": {"owner": "org", "name": "repo"},
                    }
                ]
            }
        )
    )

    result = connector.list_sources(page_size=10, page_token="next")

    assert isinstance(result, ExtendedList)
    assert isinstance(result[0], ExtendedDict)
    assert isinstance(result[0]["name"], ExtendedString)
    assert isinstance(result[0]["githubRepo"], ExtendedDict)
    assert result[0]["githubRepo"]["owner"] == "org"
    connector.get.assert_called_once_with("/sources", params={"pageSize": 10, "pageToken": "next"})


def test_create_session_returns_extended_payload() -> None:
    """Created sessions are returned as extended payloads."""
    connector = JulesConnector(api_key="test-key")
    connector.post = MagicMock(
        return_value=_response(
            {
                "name": "sessions/123",
                "id": "123",
                "title": "Fix login",
                "state": "RUNNING",
                "sourceContext": {
                    "source": "sources/github/org/repo",
                    "githubRepoContext": {"startingBranch": "main"},
                },
            }
        )
    )

    result = connector.create_session(
        prompt="Fix login",
        source="sources/github/org/repo",
        title="Fix login",
        require_plan_approval=True,
    )

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["sourceContext"], ExtendedDict)
    assert isinstance(result["sourceContext"]["githubRepoContext"], ExtendedDict)
    assert result["name"] == "sessions/123"
    connector.post.assert_called_once()
    body = connector.post.call_args.kwargs["json"]
    assert body["requirePlanApproval"] is True
    assert body["sourceContext"]["githubRepoContext"]["startingBranch"] == "main"


def test_get_session_accepts_id_and_returns_extended_payload() -> None:
    """Session lookup accepts a bare ID and returns an extended session payload."""
    connector = JulesConnector(api_key="test-key")
    connector.get = MagicMock(return_value=_response({"name": "sessions/123", "id": "123", "state": "COMPLETED"}))

    result = connector.get_session("123")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["state"], ExtendedString)
    assert result["name"] == "sessions/123"
    connector.get.assert_called_once_with("/sessions/123")


def test_list_sessions_returns_extended_payloads() -> None:
    """Jules session lists are promoted into extended containers."""
    connector = JulesConnector(api_key="test-key")
    connector.get = MagicMock(
        return_value=_response(
            {
                "sessions": [
                    {"name": "sessions/1", "id": "1", "state": "RUNNING"},
                    {"name": "sessions/2", "id": "2", "state": "COMPLETED"},
                ]
            }
        )
    )

    result = connector.list_sessions(page_size=2)

    assert isinstance(result, ExtendedList)
    assert isinstance(result[0], ExtendedDict)
    assert result[1]["state"] == "COMPLETED"


def test_approve_plan_returns_updated_extended_session() -> None:
    """Plan approval fetches and returns the updated extended session."""
    connector = JulesConnector(api_key="test-key")
    connector.post = MagicMock(return_value=_response({}))
    connector.get_session = MagicMock(return_value=ExtendedDict({"name": "sessions/123", "state": "RUNNING"}))

    result = connector.approve_plan("123")

    assert isinstance(result, ExtendedDict)
    assert result["name"] == "sessions/123"
    connector.post.assert_called_once_with("/sessions/123:approvePlan")
    connector.get_session.assert_called_once_with("sessions/123")


def test_handle_response_raises_jules_error() -> None:
    """Jules API errors preserve vendor message and status details."""
    connector = JulesConnector(api_key="test-key")
    response = _response({"error": {"message": "denied", "code": 403, "details": [{"reason": "forbidden"}]}}, 403)

    with pytest.raises(JulesError) as exc_info:
        connector._handle_response(response)

    assert exc_info.value.code == 403
    assert exc_info.value.details == [{"reason": "forbidden"}]


def test_handle_response_redacts_sensitive_jules_error_details() -> None:
    """Jules API errors should not expose raw secret-bearing fields."""
    connector = JulesConnector(api_key="test-key")
    response = _response(
        {
            "error": {
                "message": "denied password=hunter2 Bearer raw_token",
                "code": 403,
                "details": [{"api_key": "key_123"}],
            }
        },
        403,
    )

    with pytest.raises(JulesError) as exc_info:
        connector._handle_response(response)

    message = str(exc_info.value)
    assert "hunter2" not in message
    assert "raw_token" not in message
    assert exc_info.value.details == [{"api_key": "[REDACTED]"}]


def test_handle_response_redacts_request_url_in_jules_error() -> None:
    """Jules API errors should redact caller-controlled request URLs."""
    connector = JulesConnector(api_key="test-key")
    request_url = "https://jules.googleapis.com/v1alpha/sessions/private-session?api_key=raw_key"
    response = httpx.Response(
        403,
        json={
            "error": {
                "message": f"denied while calling {request_url}",
                "code": 403,
                "details": [{"debug": request_url}],
            }
        },
        request=httpx.Request("GET", request_url),
    )

    with pytest.raises(JulesError) as exc_info:
        connector._handle_response(response)

    error = exc_info.value
    assert request_url not in str(error)
    assert request_url not in repr(error.details)
    assert error.__cause__ is None


def test_handle_response_malformed_error_has_sanitized_message_without_cause() -> None:
    """Malformed Jules errors should not chain parser internals or expose request URLs."""
    connector = JulesConnector(api_key="test-key")
    request_url = "https://jules.googleapis.com/v1alpha/sessions/private-session?api_key=raw_key"
    response = _text_response(
        f"upstream failed while calling {request_url} with password=hunter2",
        status_code=502,
        url=request_url,
    )

    with pytest.raises(JulesError) as exc_info:
        connector._handle_response(response)

    error = exc_info.value
    message = str(error)
    assert error.code == 502
    assert error.__cause__ is None
    assert request_url not in message
    assert "hunter2" not in message
