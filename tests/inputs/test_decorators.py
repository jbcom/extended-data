"""Tests for decorator-based InputProvider integrations."""

from __future__ import annotations

import pytest

from extended_data.containers import ExtendedDict, ExtendedString
from extended_data.inputs import directed_inputs, input_config


@directed_inputs(inputs={"domain": "example.com"})
class ExampleService:
    """Simple service used for decorator tests."""

    def list_users(self, domain: str) -> str:
        return domain

    @input_config("api_key", source_name="API_KEY", required=True)
    def secure_call(self, api_key: str) -> str:
        return api_key

    @input_config("config", decode_from_json=True)
    def parse_config(self, config: dict[str, str]) -> dict[str, str]:
        return config

    @input_config("extended_config", decode_from_json=True, as_extended=True)
    def parse_extended_config(self, extended_config: ExtendedDict) -> ExtendedDict:
        return extended_config

    @input_config("raw_config", as_extended=True)
    def parse_raw_extended_config(self, raw_config: ExtendedDict) -> ExtendedDict:
        return raw_config

    @input_config("optional_value", allow_none=True)
    def optional_plain_value(self, optional_value: str | None = "method-default") -> str | None:
        return optional_value

    @input_config("required_value", required=True, allow_none=True)
    def required_plain_value(self, required_value: str | None = "method-default") -> str | None:
        return required_value

    def greet(self, prefix: str = "hello") -> str:
        return prefix


def test_decorator_populates_missing_argument() -> None:
    service = ExampleService()
    assert service.list_users() == "example.com"


def test_provided_argument_is_not_overwritten() -> None:
    service = ExampleService()
    assert service.list_users(domain="override") == "override"


def test_required_input_uses_custom_source() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"API_KEY": "super-secret"}})
    assert service.secure_call() == "super-secret"


def test_missing_required_input_raises_error() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"domain": "acme.io"}})
    with pytest.raises(RuntimeError):
        service.secure_call()


def test_decode_from_json_input_config() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"config": '{"enabled": true}'}})
    assert service.parse_config() == {"enabled": True}


def test_decode_from_json_input_config_can_return_extended_containers() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"extended_config": '{"name": "api"}'}})
    parsed = service.parse_extended_config()

    assert isinstance(parsed, ExtendedDict)
    assert isinstance(parsed["name"], ExtendedString)


def test_plain_input_config_can_return_extended_containers() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"raw_config": {"name": "api"}}})
    parsed = service.parse_raw_extended_config()

    assert isinstance(parsed, ExtendedDict)
    assert isinstance(parsed["name"], ExtendedString)


def test_plain_input_config_honors_explicit_none() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"optional_value": None}})

    assert service.optional_plain_value() is None


def test_plain_input_config_required_none_still_raises() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"required_value": None}})

    with pytest.raises(RuntimeError, match="Required input required_value not passed"):
        service.required_plain_value()


def test_method_default_used_when_input_missing() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"domain": "acme.io"}})
    assert service.greet() == "hello"


def test_refresh_inputs_updates_context() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"domain": "override.io"}})
    assert service.list_users() == "override.io"
    service.refresh_inputs(inputs={"domain": "beta.example"})
    assert service.list_users() == "beta.example"


def test_decorator_exposes_input_provider_property() -> None:
    service = ExampleService(_input_provider_config={"inputs": {"domain": "override.io"}})

    assert service.input_provider.get_input("domain") == "override.io"
    assert not hasattr(service, "directed_inputs")


def test_decorator_metadata_uses_extended_options() -> None:
    metadata = ExampleService.__input_provider_metadata__

    assert isinstance(metadata.options, ExtendedDict)
    assert isinstance(metadata.options["inputs"], ExtendedDict)
    assert isinstance(metadata.options["inputs"]["domain"], ExtendedString)
