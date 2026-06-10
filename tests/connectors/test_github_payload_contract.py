"""Dependency-free GitHub connector payload contract tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import extended_data.connectors.github as github_module

from extended_data.connectors.github import GitHubConnector, GitHubFallbackError
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString, ExtendedTuple


def _connector() -> GitHubConnector:
    """Build a GitHubConnector shell without importing optional SDK dependencies."""
    connector = GitHubConnector.__new__(GitHubConnector)
    connector.GITHUB_OWNER = "test-org"
    connector.GITHUB_TOKEN = "test-token"
    connector.GITHUB_BRANCH = "main"
    connector.logger = MagicMock()
    connector.repo = MagicMock()
    connector.org = MagicMock()
    connector.git = MagicMock()
    connector.graphql_client = MagicMock()
    return connector


def _logged_text(logger: MagicMock) -> str:
    """Collect structured mock log calls into one searchable diagnostic string."""
    messages: list[str] = []
    for method_name in ("debug", "info", "warning", "error", "exception"):
        method = getattr(logger, method_name)
        for call in method.call_args_list:
            messages.extend(str(arg) for arg in call.args)
            messages.extend(str(value) for value in call.kwargs.values())
    return "\n".join(messages)


def test_repository_file_decodes_into_extended_payload_with_metadata() -> None:
    """Decoded repository files should enter the Tier 2 fabric immediately."""
    connector = _connector()
    mock_file = MagicMock()
    mock_file.decoded_content = b'{"service":{"name":"api"}}'
    mock_file.sha = "abc123"
    mock_file.content = "test content"
    connector.repo.get_contents.return_value = mock_file

    result = connector.get_repository_file("service.json", return_sha=True, return_path=True)

    assert isinstance(result, ExtendedTuple)
    assert isinstance(result[0], ExtendedDict)
    assert isinstance(result[0]["service"]["name"], ExtendedString)
    assert result[0]["service"]["name"].upper_first() == "Api"
    assert result[1:] == ("abc123", "service.json")


def test_list_repositories_promotes_sdk_payloads() -> None:
    """Repository listing payloads should be extended containers, not raw dicts."""
    connector = _connector()
    repo = MagicMock()
    repo.id = 1
    repo.name = "api-service"
    repo.full_name = "test-org/api-service"
    repo.description = "API service"
    repo.private = False
    repo.archived = False
    repo.default_branch = "main"
    repo.html_url = "https://github.com/test-org/api-service"
    repo.clone_url = "https://github.com/test-org/api-service.git"
    repo.ssh_url = "git@github.com:test-org/api-service.git"
    repo.language = "Python"
    repo.topics = ["data", "vendor"]
    repo.created_at = None
    repo.updated_at = None
    repo.pushed_at = None
    connector.org.get_repos.return_value = [repo]

    result = connector.list_repositories()

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["api-service"], ExtendedDict)
    assert isinstance(result["api-service"]["topics"], ExtendedList)
    assert result["api-service"]["name"].to_snake_case() == "api_service"


def test_execute_graphql_promotes_response_payload() -> None:
    """GraphQL response dictionaries should expose nested extended containers."""
    connector = _connector()
    connector.graphql_client.execute.return_value = {
        "data": {"user": {"login": "octocat", "organizationVerifiedDomainEmails": ["octo@example.com"]}}
    }

    result = connector.execute_graphql("query($login: String!) { user(login: $login) { login } }", {"login": "octocat"})

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["data"]["user"], ExtendedDict)
    assert isinstance(result["data"]["user"]["organizationVerifiedDomainEmails"], ExtendedList)
    assert result["data"]["user"]["login"].upper_first() == "Octocat"


def test_verified_email_enrichment_returns_extended_payload() -> None:
    """Derived GitHub user payloads should remain in the extended container layer."""
    connector = _connector()
    connector.graphql_client.execute.return_value = {
        "data": {
            "user": {
                "login": "octocat",
                "email": "octocat@example.com",
                "organizationVerifiedDomainEmails": ["octocat@example.com"],
            }
        }
    }

    result = connector.get_users_with_verified_emails(
        members={"octocat": {"login": "octocat", "role": "member"}},
        domain_filter="example.com",
    )

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["octocat"], ExtendedDict)
    assert isinstance(result["octocat"]["verified_emails"], ExtendedList)
    assert result["octocat"]["primary_email"].upper_first() == "Octocat@example.com"


def test_workflow_builders_return_extended_data() -> None:
    """Local GitHub workflow builders should produce first-class extended data."""
    connector = _connector()

    step = connector.build_workflow_step(name="Run tests", run="pytest")
    job = connector.build_workflow_job(steps=[step])
    workflow = connector.build_workflow(name="CI", on={"pull_request": {}}, jobs={"test": job})

    assert isinstance(step, ExtendedDict)
    assert isinstance(job, ExtendedDict)
    assert isinstance(workflow, ExtendedDict)
    assert isinstance(workflow["jobs"]["test"]["steps"], ExtendedList)
    assert workflow["jobs"]["test"]["steps"][0]["run"].upper_first() == "Pytest"


def test_update_repository_file_redacts_diagnostics_but_preserves_payload() -> None:
    """GitHub file updates should not leak caller paths or messages in logs."""
    connector = _connector()
    raw_path = "private/path.txt"
    raw_message = "commit mentions private/path.txt token=raw-token"

    connector.update_repository_file(
        raw_path,
        "raw file data",
        file_sha="abc123",
        msg=raw_message,
        allow_encoding=False,
    )

    connector.repo.update_file.assert_called_once_with(
        path=raw_path,
        message=raw_message,
        content="raw file data",
        sha="abc123",
        branch="main",
    )
    logs = _logged_text(connector.logger)
    assert "[REDACTED]" in logs
    assert raw_path not in logs
    assert raw_message not in logs
    assert "raw-token" not in logs


def test_add_team_member_failure_redacts_diagnostics_without_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Team membership failures should redact user/team identifiers and avoid tracebacks."""
    monkeypatch.setattr(github_module, "GithubException", GitHubFallbackError)
    monkeypatch.setattr(github_module, "UnknownObjectException", GitHubFallbackError)

    connector = _connector()
    connector.org.get_team_by_slug.side_effect = GitHubFallbackError(
        "team private-team user secret-user token=raw-token"
    )

    assert connector.add_team_member("private-team", "secret-user") is False

    logs = _logged_text(connector.logger)
    assert "[REDACTED]" in logs
    assert "private-team" not in logs
    assert "secret-user" not in logs
    assert "raw-token" not in logs
    connector.logger.exception.assert_not_called()
    for call in connector.logger.error.call_args_list:
        assert call.kwargs.get("exc_info") is not True
