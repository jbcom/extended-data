"""Dependency-free GitHub connector payload contract tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from extended_data.connectors.github import GitHubConnector
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
