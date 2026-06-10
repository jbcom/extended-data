"""Test suite for the InputProvider.

This module contains unit tests for the InputProvider, which manages
and processes directed inputs from various sources like environment variables,
stdin, and predefined dictionaries.

The tests cover initialization, input retrieval, decoding, and input management
functions such as freezing, thawing, and shifting inputs.

Fixtures:
    _env_setup: A pytest fixture to set up environment variables for tests.
    _stdin_setup: A pytest fixture to set up stdin for tests.

Tests:
    test_init_with_env_vars: Tests initialization with environment variables.
    test_init_with_stdin: Tests initialization with stdin input.
    test_get_input_with_default: Tests retrieving an input with a default value.
    test_get_input_required: Tests retrieving a required input.
    test_get_input_boolean: Tests retrieving and converting a boolean input.
    test_get_input_integer: Tests retrieving and converting an integer input.
    test_decode_input_json: Tests decoding an input from JSON format.
    test_decode_input_yaml: Tests decoding an input from YAML format.
    test_decode_input_base64: Tests decoding an input from Base64 format.
    test_freeze_inputs: Tests freezing inputs.
    test_thaw_inputs: Tests thawing inputs.
    test_shift_inputs: Tests shifting between frozen and thawed inputs.
"""

from __future__ import annotations

import base64
import json
import os

from pathlib import Path

import pytest

from extended_data import base64_encode
from extended_data.containers import ExtendedDict, ExtendedString
from extended_data.inputs.__main__ import InputProvider


@pytest.fixture
def _env_setup(monkeypatch):
    """Fixture to set up environment variables.

    This fixture sets an environment variable `TEST_ENV_VAR` with the value
    `test_value` to simulate environment variable inputs during tests.

    Args:
        monkeypatch: A pytest fixture for safely patching and modifying the environment.
    """
    monkeypatch.setenv("TEST_ENV_VAR", "test_value")


@pytest.fixture
def _stdin_setup(monkeypatch):
    """Fixture to set up stdin.

    This fixture redirects stdin to a dummy file to simulate stdin inputs
    during tests.

    Args:
        monkeypatch: A pytest fixture for safely patching and modifying stdin.
    """
    with Path(os.devnull).open("w") as f:
        monkeypatch.setattr("sys.stdin", f)


@pytest.mark.usefixtures("_env_setup")
def test_init_with_env_vars():
    """Test initialization with environment variables.

    This test verifies that the InputProvider correctly initializes with
    inputs from environment variables.
    """
    dic = InputProvider()
    assert dic.inputs["TEST_ENV_VAR"] == "test_value"


@pytest.mark.usefixtures("_env_setup")
def test_init_with_stdin(monkeypatch):
    """Test initialization with stdin input.

    This test verifies that the InputProvider correctly initializes with
    inputs from stdin when `from_stdin` is set to True.

    Args:
        monkeypatch: A pytest fixture for safely patching stdin.
    """
    input_data = json.dumps({"stdin_key": "stdin_value"})
    monkeypatch.setattr("sys.stdin.read", lambda: input_data)

    dic = InputProvider(from_stdin=True)
    assert dic.inputs["stdin_key"] == "stdin_value"


def test_get_input_with_default():
    """Test retrieving an input with a default value.

    This test verifies that the InputProvider retrieves an input correctly,
    returning a default value if the key is not found.
    """
    dic = InputProvider(inputs={"key1": "value1"})
    assert isinstance(dic.inputs, ExtendedDict)
    assert isinstance(dic.inputs["key1"], ExtendedString)
    assert dic.get_input("key1", default="default_value") == "value1"
    assert isinstance(dic.get_input("key1"), str)
    assert dic.get_input("key2", default="default_value") == "default_value"


def test_get_input_uses_exact_keys():
    """InputProvider now uses the package's exact-key ExtendedDict surface."""
    dic = InputProvider(inputs={"API_KEY": "secret"}, from_environment=False)

    assert dic.get_input("api_key", default="fallback") == "fallback"
    assert dic.get_input("API_KEY") == "secret"


def test_get_input_can_return_extended_containers():
    """Plain input retrieval can opt into the Tier 2 container layer."""
    dic = InputProvider(inputs={"config": {"service": "api"}, "name": "gateway"}, from_environment=False)

    config = dic.get_input("config", as_extended=True)
    name = dic.get_input("name", as_extended=True)

    assert isinstance(config, ExtendedDict)
    assert isinstance(config["service"], ExtendedString)
    assert isinstance(name, ExtendedString)
    assert name.upper_first() == "Gateway"


def test_get_input_required():
    """Test retrieving a required input.

    This test verifies that the InputProvider raises an error if a required
    input is not provided.
    """
    dic = InputProvider(inputs={"key1": "value1", "API_TOKEN": "super-secret"}, from_environment=False)
    with pytest.raises(RuntimeError, match="Required input key2 not passed") as exc_info:
        dic.get_input("key2", required=True)

    message = str(exc_info.value)
    assert "key1" in message
    assert "API_TOKEN" in message
    assert "value1" not in message
    assert "super-secret" not in message


def test_init_with_invalid_stdin_does_not_echo_payload(monkeypatch):
    """Invalid stdin diagnostics do not expose raw stdin content."""
    monkeypatch.setattr("sys.stdin.read", lambda: '{"API_TOKEN": "super-secret"')

    with pytest.raises(RuntimeError, match="Failed to decode stdin as JSON") as exc_info:
        InputProvider(from_stdin=True)

    assert "super-secret" not in str(exc_info.value)


def test_get_input_boolean():
    """Test retrieving and converting a boolean input.

    This test verifies that the InputProvider correctly retrieves an input
    and converts it to a boolean value.
    """
    dic = InputProvider(inputs={"bool_key": "true"})
    assert dic.get_input("bool_key", is_bool=True) is True


def test_get_input_boolean_existing_bool():
    """Boolean inputs that are already bool are returned unchanged."""
    dic = InputProvider(inputs={"bool_key": False})
    assert dic.get_input("bool_key", is_bool=True) is False


def test_get_input_boolean_conversion_errors_do_not_echo_values():
    """Boolean conversion diagnostics identify the key without exposing the value."""
    dic = InputProvider(inputs={"bool_key": "super-secret"})

    with pytest.raises(RuntimeError, match="Input bool_key cannot be converted to boolean") as exc_info:
        dic.get_input("bool_key", is_bool=True)

    assert "super-secret" not in str(exc_info.value)


def test_get_input_integer():
    """Test retrieving and converting an integer input.

    This test verifies that the InputProvider correctly retrieves an input
    and converts it to an integer value.
    """
    dic = InputProvider(inputs={"int_key": "10"})
    integer_test_value = 10
    assert dic.get_input("int_key", is_integer=True) == integer_test_value


def test_get_input_conversion_errors_do_not_echo_values():
    """Type conversion diagnostics identify the key without exposing the value."""
    dic = InputProvider(inputs={"int_key": "super-secret"})

    with pytest.raises(RuntimeError, match="Input int_key cannot be converted to integer") as exc_info:
        dic.get_input("int_key", is_integer=True)

    assert "super-secret" not in str(exc_info.value)


def test_decode_input_json():
    """Test decoding an input from JSON format.

    This test verifies that the InputProvider correctly decodes an input
    from JSON format.
    """
    dic = InputProvider(inputs={"json_key": '{"name": "test"}'})
    decoded = dic.decode_input("json_key", decode_from_json=True)
    assert decoded == {"name": "test"}


def test_decode_input_yaml():
    """Test decoding an input from YAML format.

    This test verifies that the InputProvider correctly decodes an input
    from YAML format.
    """
    dic = InputProvider(inputs={"yaml_key": "name: test"})
    decoded = dic.decode_input("yaml_key", decode_from_yaml=True)
    assert decoded == {"name": "test"}


def test_decode_input_base64():
    """Test decoding an input from Base64 format.

    This test verifies that the InputProvider correctly decodes an input
    from Base64 format, optionally also decoding it from JSON.
    """
    encoded_value = base64_encode(json.dumps({"name": "test"}).encode())
    dic = InputProvider(inputs={"base64_key": encoded_value})
    decoded = dic.decode_input("base64_key", decode_from_base64=True, decode_from_json=True)
    assert decoded == {"name": "test"}


def test_decode_input_base64_from_bytes():
    """Base64 encoded bytes can be decoded and parsed."""
    encoded_value = base64_encode(json.dumps({"name": "test"}).encode())
    dic = InputProvider(inputs={"base64_key": encoded_value.encode()})
    decoded = dic.decode_input("base64_key", decode_from_base64=True, decode_from_json=True)

    assert decoded == {"name": "test"}


def test_decode_input_json_can_return_extended_containers():
    """Decoded input payloads can opt into the Tier 2 container layer."""
    dic = InputProvider(inputs={"json_key": '{"name": "test"}'})
    decoded = dic.decode_input("json_key", decode_from_json=True, as_extended=True)

    assert isinstance(decoded, ExtendedDict)
    assert isinstance(decoded["name"], ExtendedString)
    assert decoded["name"].upper_first() == "Test"


def test_decode_input_decodes_present_value_that_equals_default():
    """Defaults should not mask present input values that happen to be equal."""
    raw_config = '{"name": "test"}'
    dic = InputProvider(inputs={"json_key": raw_config}, from_environment=False)
    missing = InputProvider(from_environment=False)

    decoded = dic.decode_input("json_key", default=raw_config, decode_from_json=True, as_extended=True)

    assert isinstance(decoded, ExtendedDict)
    assert isinstance(decoded["name"], ExtendedString)
    assert decoded["name"].upper_first() == "Test"
    assert missing.decode_input("json_key", default=raw_config, decode_from_json=True) == raw_config


def test_decode_input_honors_explicit_none_values():
    """Present None inputs should obey allow_none instead of looking missing."""
    dic = InputProvider(inputs={"json_key": None}, from_environment=False)
    missing = InputProvider(from_environment=False)

    assert dic.decode_input("json_key", default="fallback", decode_from_json=True, allow_none=True) is None
    assert dic.decode_input("json_key", default="fallback", decode_from_json=True, allow_none=False) == "fallback"
    assert missing.decode_input("json_key", default="fallback", decode_from_json=True, allow_none=True) == "fallback"


def test_decode_input_required_empty_value_raises():
    """Required decode inputs still reject empty provided values."""
    dic = InputProvider(inputs={"json_key": ""}, from_environment=False)

    with pytest.raises(RuntimeError, match="Required input json_key not passed"):
        dic.decode_input("json_key", decode_from_json=True, required=True)


def test_decode_input_errors_do_not_echo_values():
    """Decode diagnostics identify the input key without exposing raw values."""
    dic = InputProvider(
        inputs={
            "json_key": '{"token": "super-secret"',
            "yaml_key": "token: [super-secret",
            "base64_key": "not valid base64!",
        }
    )

    with pytest.raises(RuntimeError, match="Failed to decode input json_key from JSON") as json_exc:
        dic.decode_input("json_key", decode_from_json=True)
    with pytest.raises(RuntimeError, match="Failed to decode input yaml_key from YAML") as yaml_exc:
        dic.decode_input("yaml_key", decode_from_yaml=True)
    with pytest.raises(RuntimeError, match="Failed to decode input base64_key from Base64") as base64_exc:
        dic.decode_input("base64_key", decode_from_base64=True)

    for exc_info in (json_exc, yaml_exc, base64_exc):
        message = str(exc_info.value)
        assert "super-secret" not in message
        assert "not valid base64" not in message


def test_decode_input_base64_external_json_can_return_extended_containers():
    """Externally produced Base64 JSON should decode once and then be extended."""
    encoded_value = base64.b64encode(b'{"name": "test"}').decode("utf-8")
    dic = InputProvider(inputs={"base64_key": encoded_value})
    decoded = dic.decode_input("base64_key", decode_from_base64=True, decode_from_json=True, as_extended=True)

    assert isinstance(decoded, ExtendedDict)
    assert isinstance(decoded["name"], ExtendedString)
    assert decoded["name"].upper_first() == "Test"


def test_freeze_inputs():
    """Test freezing inputs.

    This test verifies that the InputProvider correctly freezes its inputs,
    preventing further modifications.
    """
    dic = InputProvider(inputs={"key1": "value1"})
    frozen_inputs = dic.freeze_inputs()
    assert isinstance(frozen_inputs, ExtendedDict)
    assert frozen_inputs["key1"] == "value1"
    assert isinstance(frozen_inputs["key1"], ExtendedString)
    assert isinstance(dic.inputs, ExtendedDict)
    assert dic.inputs == {}


def test_thaw_inputs():
    """Test thawing inputs.

    This test verifies that the InputProvider correctly thaws its inputs,
    merging the frozen inputs back into the current inputs.
    """
    dic = InputProvider(inputs={"key1": "value1"})
    dic.freeze_inputs()
    dic.thaw_inputs()
    assert isinstance(dic.inputs, ExtendedDict)
    assert dic.inputs["key1"] == "value1"
    assert isinstance(dic.inputs["key1"], ExtendedString)
    assert isinstance(dic.frozen_inputs, ExtendedDict)
    assert dic.frozen_inputs == {}


def test_snapshot_inputs_returns_detached_extended_copy():
    """Input snapshots are promoted copies, not mutable internal state."""
    dic = InputProvider(inputs={"service": {"name": "api"}})

    snapshot = dic.snapshot_inputs()
    snapshot["service"]["name"] = "worker"

    assert isinstance(snapshot, ExtendedDict)
    assert isinstance(snapshot["service"], ExtendedDict)
    assert isinstance(snapshot["service"]["name"], ExtendedString)
    assert dic.inputs["service"]["name"] == "api"
    assert dic.snapshot_inputs()["service"]["name"].upper_first() == "Api"


def test_snapshot_inputs_can_select_frozen_state():
    """Frozen input snapshots can be inspected without thawing state."""
    dic = InputProvider(inputs={"service": {"name": "api"}}, from_environment=False)
    dic.freeze_inputs()

    frozen = dic.snapshot_inputs(frozen=True)

    assert isinstance(frozen, ExtendedDict)
    assert isinstance(frozen["service"], ExtendedDict)
    assert frozen["service"]["name"].upper_first() == "Api"
    assert dic.inputs == {}
    assert dic.frozen_inputs["service"]["name"] == "api"


def test_replace_inputs_promotes_values_and_clears_frozen_state_by_default():
    """Replacing inputs should be explicit and should not keep stale frozen state."""
    dic = InputProvider(inputs={"service": {"name": "api"}}, from_environment=False)
    dic.freeze_inputs()

    replaced = dic.replace_inputs({"service": {"name": "worker"}})

    assert isinstance(replaced, ExtendedDict)
    assert isinstance(replaced["service"], ExtendedDict)
    assert replaced["service"]["name"].upper_first() == "Worker"
    assert dic.inputs["service"]["name"] == "worker"
    assert dic.frozen_inputs == {}


def test_replace_inputs_can_preserve_frozen_state_when_requested():
    """Replacement can keep frozen inputs for explicit staged-state workflows."""
    dic = InputProvider(inputs={"service": {"name": "api"}}, from_environment=False)
    dic.freeze_inputs()

    dic.replace_inputs({"region": "us-east-1"}, clear_frozen=False)

    assert dic.inputs["region"].upper_first() == "Us-east-1"
    assert dic.snapshot_inputs(frozen=True)["service"]["name"].upper_first() == "Api"


def test_shift_inputs():
    """Test shifting between frozen and thawed inputs.

    This test verifies that the InputProvider correctly shifts between
    frozen and thawed inputs, allowing for flexible input management.
    """
    dic = InputProvider(inputs={"key1": "value1"})
    dic.shift_inputs()
    assert isinstance(dic.inputs, ExtendedDict)
    assert isinstance(dic.frozen_inputs, ExtendedDict)
    assert dic.inputs == {}
    assert dic.frozen_inputs["key1"] == "value1"

    dic.shift_inputs()
    assert dic.inputs["key1"] == "value1"
    assert dic.frozen_inputs == {}


def test_merge_inputs_deep_merge():
    """Merging inputs should deep merge nested structures rather than replace."""
    dic = InputProvider(inputs={"nested": {"left": 1}})
    merged = dic.merge_inputs({"nested": {"right": 2}})

    assert isinstance(merged, ExtendedDict)
    assert isinstance(merged["nested"], ExtendedDict)
    assert merged["nested"] == {"left": 1, "right": 2}


def test_environment_prefix_filter(monkeypatch):
    """Only environment variables matching the prefix should be loaded."""
    monkeypatch.setenv("APP_ALPHA", "alpha")
    monkeypatch.setenv("APP_BETA", "beta")
    monkeypatch.setenv("UNSCOPED", "nope")

    dic = InputProvider(from_environment=True, env_prefix="APP_", strip_env_prefix=True)

    assert dic.inputs["ALPHA"] == "alpha"
    assert dic.inputs["ALPHA"].upper_first() == "Alpha"
    assert dic.inputs["BETA"] == "beta"
    assert "UNSCOPED" not in dic.inputs
