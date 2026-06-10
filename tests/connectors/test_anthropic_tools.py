"""Tests for Anthropic AI tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_anthropic_list_models():
    """Test list_models tool."""
    from extended_data.connectors.anthropic.tools import anthropic_list_models

    with patch("extended_data.connectors.anthropic.AnthropicConnector") as mock_connector_class:
        mock_connector = MagicMock()
        mock_model = MagicMock()
        mock_model.id = "claude-3-opus"
        mock_model.display_name = "Claude 3 Opus"
        mock_connector.list_models.return_value = [mock_model]
        mock_connector_class.return_value = mock_connector

        result = anthropic_list_models()
        assert len(result) == 1
        assert result[0]["id"] == "claude-3-opus"


def test_anthropic_create_message():
    """Test create_message tool."""
    from extended_data.connectors.anthropic.tools import anthropic_create_message

    with patch("extended_data.connectors.anthropic.AnthropicConnector") as mock_connector_class:
        mock_connector = MagicMock()
        mock_response = MagicMock()
        mock_response.id = "msg_123"
        mock_response.text = "Hello!"
        mock_response.model = "claude-3-opus"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_connector.create_message.return_value = mock_response
        mock_connector_class.return_value = mock_connector

        result = anthropic_create_message(model="claude-3-opus", prompt="Hi")
        assert result["id"] == "msg_123"
        assert result["text"] == "Hello!"
