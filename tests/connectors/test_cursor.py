"""Tests for Cursor connector."""

from __future__ import annotations

import os

from unittest.mock import MagicMock, patch

import pytest

from extended_data.connectors.cursor import (
    Agent,
    AgentState,
    Conversation,
    ConversationMessage,
    CursorConnector,
    CursorError,
    CursorValidationError,
    Repository,
    validate_agent_id,
    validate_prompt_text,
    validate_repository,
    validate_webhook_url,
)
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString, extend_data


class TestValidators:
    """Tests for input validators."""

    def test_validate_agent_id_valid(self):
        """Valid agent IDs should pass."""
        validate_agent_id("abc-123")
        validate_agent_id("agent-id-with-numbers-123")
        validate_agent_id("simple")

    def test_validate_agent_id_empty(self):
        """Empty agent ID should fail."""
        with pytest.raises(CursorValidationError, match="required"):
            validate_agent_id("")

    def test_validate_agent_id_too_long(self):
        """Agent ID over 100 chars should fail."""
        with pytest.raises(CursorValidationError, match="maximum length"):
            validate_agent_id("a" * 101)

    def test_validate_agent_id_invalid_chars(self):
        """Agent ID with invalid chars should fail."""
        with pytest.raises(CursorValidationError, match="invalid characters"):
            validate_agent_id("agent@id")
        with pytest.raises(CursorValidationError, match="invalid characters"):
            validate_agent_id("agent id")

    def test_validate_prompt_text_valid(self):
        """Valid prompt text should pass."""
        validate_prompt_text("Hello, world!")
        validate_prompt_text("Implement feature X with multiple lines\nand more text")

    def test_validate_prompt_text_empty(self):
        """Empty prompt should fail."""
        with pytest.raises(CursorValidationError, match="required"):
            validate_prompt_text("")
        with pytest.raises(CursorValidationError, match="cannot be empty"):
            validate_prompt_text("   ")

    def test_validate_prompt_text_too_long(self):
        """Prompt over 100k chars should fail."""
        with pytest.raises(CursorValidationError, match="maximum length"):
            validate_prompt_text("a" * 100001)

    def test_validate_repository_valid(self):
        """Valid repository names should pass."""
        validate_repository("owner/repo")
        validate_repository("https://github.com/owner/repo")

    def test_validate_repository_invalid(self):
        """Invalid repository names should fail."""
        with pytest.raises(CursorValidationError, match="format"):
            validate_repository("invalid-no-slash")

    def test_validate_webhook_url_valid(self):
        """Valid HTTPS webhook URLs should pass."""
        validate_webhook_url("https://example.com/webhook")
        validate_webhook_url("https://api.myservice.io/hooks/123")

    def test_validate_webhook_url_http(self):
        """HTTP (non-HTTPS) URLs should fail."""
        with pytest.raises(CursorValidationError, match="HTTPS"):
            validate_webhook_url("http://example.com/webhook")

    def test_validate_webhook_url_internal(self):
        """Internal/private URLs should fail (SSRF protection)."""
        # IPv4 localhost and private ranges
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://localhost/webhook")
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://127.0.0.1/webhook")
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://192.168.1.1/webhook")
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://10.0.0.1/webhook")

    def test_validate_webhook_url_ipv6_internal(self):
        """IPv6 internal addresses should fail (SSRF protection)."""
        # IPv6 localhost
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://[::1]/webhook")
        # IPv6 unique local addresses (fc00::/7, fd00::/8)
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://[fc00::1]/webhook")
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://[fd12:3456::1]/webhook")
        # IPv6 link-local (fe80::/10)
        with pytest.raises(CursorValidationError, match="internal"):
            validate_webhook_url("https://[fe80::1]/webhook")


class TestModels:
    """Tests for Pydantic models."""

    def test_agent_model(self):
        """Agent model should parse correctly."""
        agent = Agent(
            id="test-agent-123",
            state=AgentState.RUNNING,
            task="Implement feature X",
            repository="owner/repo",
        )
        assert agent.id == "test-agent-123"
        assert agent.state == AgentState.RUNNING
        assert agent.task == "Implement feature X"

    def test_agent_model_extra_fields(self):
        """Agent model should allow extra fields from API."""
        agent = Agent.model_validate(
            {
                "id": "test",
                "state": "running",
                "custom_field": "value",
            }
        )
        assert agent.id == "test"
        assert hasattr(agent, "custom_field")

    def test_repository_model(self):
        """Repository model should parse correctly."""
        repo = Repository(name="owner/repo", url="https://github.com/owner/repo")
        assert repo.name == "owner/repo"

    def test_conversation_model(self):
        """Conversation model should parse correctly."""
        conv = Conversation(
            agent_id="test",
            messages=[
                ConversationMessage(role="user", content="Hello"),
                ConversationMessage(role="assistant", content="Hi there!"),
            ],
        )
        assert conv.agent_id == "test"
        assert len(conv.messages) == 2


class TestCursorConnector:
    """Tests for CursorConnector."""

    def test_init_without_api_key(self):
        """Initialization without API key should fail."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CursorError, match="CURSOR_API_KEY is required"):
                CursorConnector()

    def test_init_with_api_key(self):
        """Initialization with API key should succeed."""
        with patch("extended_data.connectors.cursor.httpx.Client"):
            connector = CursorConnector(api_key="test-key")
            assert connector.api_key == "test-key"

    def test_is_available_true(self):
        """is_available should return True when env var is set."""
        with patch.dict(os.environ, {"CURSOR_API_KEY": "test"}):
            assert CursorConnector.is_available() is True

    def test_is_available_false(self):
        """is_available should return False when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert CursorConnector.is_available() is False

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_list_agents(self, mock_client_class):
        """list_agents should return parsed agents."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"agents": [{"id": "agent-1", "state": "running"}]}'
        mock_response.json.return_value = {"agents": [{"id": "agent-1", "state": "running"}]}
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        agents = connector.list_agents()

        assert isinstance(agents, ExtendedList)
        assert isinstance(agents[0], ExtendedDict)
        assert isinstance(agents[0]["id"], ExtendedString)
        assert len(agents) == 1
        assert agents[0]["id"] == "agent-1"
        assert agents[0]["state"] == "running"

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_get_agent_status_returns_extended_dict(self, mock_client_class):
        """get_agent_status should return an extended agent payload."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"id": "agent-1", "state": "finished", "pr_url": "https://github.com/org/repo/pull/1"}'
        mock_response.json.return_value = {
            "id": "agent-1",
            "state": "finished",
            "pr_url": "https://github.com/org/repo/pull/1",
        }
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        agent = connector.get_agent_status("agent-1")

        assert isinstance(agent, ExtendedDict)
        assert isinstance(agent["state"], ExtendedString)
        assert agent["pr_url"] == "https://github.com/org/repo/pull/1"

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_get_agent_conversation_returns_extended_dict(self, mock_client_class):
        """get_agent_conversation should return an extended conversation payload."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"messages": [{"role": "user", "content": "hello"}]}'
        mock_response.json.return_value = {"messages": [{"role": "user", "content": "hello"}]}
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        conversation = connector.get_agent_conversation("agent-1")

        assert isinstance(conversation, ExtendedDict)
        assert isinstance(conversation["messages"], ExtendedList)
        assert isinstance(conversation["messages"][0], ExtendedDict)
        assert conversation["messages"][0]["content"] == "hello"

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_launch_agent(self, mock_client_class):
        """launch_agent should send correct request and return agent."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"id": "new-agent", "state": "pending"}
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        agent = connector.launch_agent(
            prompt_text="Implement feature X",
            repository="owner/repo",
            images=extend_data([{"data": "base64", "dimensions": {"width": 16, "height": 16}}]),
        )

        assert isinstance(agent, ExtendedDict)
        assert isinstance(agent["id"], ExtendedString)
        assert agent["id"] == "new-agent"
        assert agent["state"] == "pending"

        # Verify request was made correctly
        call_args = mock_client.request.call_args
        assert call_args.args[0] == "POST"
        assert "/agents" in call_args.args[1]
        assert "prompt" in call_args.kwargs["json"]
        assert "source" in call_args.kwargs["json"]
        assert isinstance(call_args.kwargs["json"]["prompt"]["images"], list)
        assert isinstance(call_args.kwargs["json"]["prompt"]["images"][0], dict)

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_launch_agent_validation(self, mock_client_class):
        """launch_agent should validate inputs."""
        mock_client_class.return_value = MagicMock()

        connector = CursorConnector(api_key="test-key")

        with pytest.raises(CursorValidationError, match="required"):
            connector.launch_agent(prompt_text="", repository="owner/repo")

        with pytest.raises(CursorValidationError, match="format"):
            connector.launch_agent(prompt_text="Hello", repository="invalid")

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_list_repositories_returns_extended_list(self, mock_client_class):
        """list_repositories should return extended repository payloads."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"repositories": [{"name": "org/repo", "default_branch": "main"}]}'
        mock_response.json.return_value = {"repositories": [{"name": "org/repo", "default_branch": "main"}]}
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        repositories = connector.list_repositories()

        assert isinstance(repositories, ExtendedList)
        assert isinstance(repositories[0], ExtendedDict)
        assert repositories[0]["name"] == "org/repo"

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_list_models_returns_extended_list(self, mock_client_class):
        """list_models should expose model names as an extended container."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"models": ["cursor-small", "cursor-large"]}'
        mock_response.json.return_value = {"models": ["cursor-small", "cursor-large"]}
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        models = connector.list_models()

        assert isinstance(models, ExtendedList)
        assert isinstance(models[0], ExtendedString)
        assert models[0].to_snake_case() == "cursor_small"

    @patch("extended_data.connectors.cursor.httpx.Client")
    def test_list_models_empty_response_returns_extended_list(self, mock_client_class):
        """list_models should extend the empty response path too."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = "{}"
        mock_response.json.return_value = {}
        mock_client.request.return_value = mock_response

        connector = CursorConnector(api_key="test-key")
        models = connector.list_models()

        assert isinstance(models, ExtendedList)
        assert models == []
