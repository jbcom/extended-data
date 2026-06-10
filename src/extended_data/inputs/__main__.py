"""Module to handle directed inputs for the InputProvider library.

This module provides functionality for managing inputs from various sources
(environment, stdin) and allows for dynamic merging, freezing, and thawing
of inputs. It includes methods to decode inputs from JSON, YAML, and Base64
formats, as well as handling boolean and integer conversions.
"""

from __future__ import annotations

import binascii
import json
import os
import sys

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from deepmerge import Merger  # type: ignore[attr-defined]

from extended_data.containers.factory import extend_data, to_builtin
from extended_data.containers.mappings import ExtendedDict
from extended_data.io.base64 import base64_decode
from extended_data.primitives.formats.errors import DataDecodeError
from extended_data.primitives.formats.json import decode_json
from extended_data.primitives.formats.yaml import decode_yaml
from extended_data.primitives.state import is_nothing
from extended_data.primitives.types import strtobool, strtodatetime, strtofloat, strtoint, strtopath


if TYPE_CHECKING:
    from collections.abc import Mapping


class InputProvider:
    """A class to manage and process directed inputs from environment variables.

    stdin, or provided dictionaries.

    Attributes:
        inputs (ExtendedDict): Dictionary to store inputs.
        frozen_inputs (ExtendedDict): Dictionary to store frozen inputs.
        from_stdin (bool): Flag indicating if inputs were read from stdin.
        merger (Merger): Object to manage deep merging of dictionaries.
    """

    def __init__(
        self,
        inputs: Mapping[str, Any] | None = None,
        from_environment: bool = True,
        from_stdin: bool = False,
        env_prefix: str | None = None,
        strip_env_prefix: bool = False,
    ):
        """Initializes the InputProvider with the provided inputs.

        Optionally loading additional inputs from environment variables and stdin.

        Args:
            inputs (Mapping[str, Any] | None): Initial inputs to be processed.
            from_environment (bool): Whether to load inputs from environment variables.
            from_stdin (bool): Whether to load inputs from stdin.
            env_prefix (str | None): Optional prefix to filter environment variables.
            strip_env_prefix (bool): Whether to strip the prefix from environment keys.
        """
        self.merger = Merger(
            [(list, ["append"]), (dict, ["merge"]), (set, ["union"])],
            ["override"],
            ["override"],
        )

        current_inputs = self._normalize_inputs(inputs)

        if from_environment:
            env_inputs = self._filtered_environment(os.environ, env_prefix=env_prefix, strip_prefix=strip_env_prefix)
            current_inputs = self._merge_inputs(env_inputs, current_inputs)

        if from_stdin and not strtobool(os.getenv("OVERRIDE_STDIN", "False")):
            stdin_inputs = self._load_from_stdin()
            current_inputs = self._merge_inputs(stdin_inputs, current_inputs)

        self.from_stdin = from_stdin
        self.inputs: ExtendedDict = ExtendedDict(current_inputs)
        self.frozen_inputs: ExtendedDict = ExtendedDict()

    @staticmethod
    def _normalize_inputs(inputs: Mapping[str, Any] | None) -> dict[str, Any]:
        if inputs is None or is_nothing(inputs):
            return {}

        return to_builtin(dict(inputs))

    @staticmethod
    def _filtered_environment(
        env: Mapping[str, str],
        *,
        env_prefix: str | None,
        strip_prefix: bool,
    ) -> dict[str, str]:
        if env_prefix is None:
            return dict(env)

        return {
            key[len(env_prefix) :] if strip_prefix else key: value
            for key, value in env.items()
            if key.startswith(env_prefix)
        }

    def _merge_inputs(self, base: Mapping[str, Any], incoming: Mapping[str, Any]) -> dict[str, Any]:
        if is_nothing(incoming):
            return deepcopy(to_builtin(base))

        clean_base = deepcopy(to_builtin(base))
        clean_incoming = deepcopy(to_builtin(incoming))

        return self.merger.merge(clean_base, clean_incoming)

    @staticmethod
    def _load_from_stdin() -> dict[str, Any]:
        inputs_from_stdin = sys.stdin.read()

        if is_nothing(inputs_from_stdin):
            return {}

        try:
            decoded_stdin: dict[str, Any] = json.loads(inputs_from_stdin)
            return decoded_stdin
        except json.JSONDecodeError as exc:
            message = f"Failed to decode stdin as JSON ({len(inputs_from_stdin)} characters)."
            raise RuntimeError(message) from exc

    @staticmethod
    def _coerce_text(value: Any) -> Any:
        if isinstance(value, memoryview):
            return value.tobytes().decode("utf-8")

        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError as exc:
                message = f"Failed to decode {type(value).__name__} input as UTF-8 text."
                raise RuntimeError(message) from exc

        return value

    @staticmethod
    def _format_available_keys(inputs: Mapping[str, Any]) -> str:
        """Format available input keys without exposing their values."""
        if not inputs:
            return "none"

        keys = sorted(str(key) for key in inputs)
        return ", ".join(keys[:20]) + (f", ... ({len(keys)} total)" if len(keys) > 20 else "")

    def get_input(
        self,
        k: str,
        default: Any | None = None,
        required: bool = False,
        is_bool: bool = False,
        is_integer: bool = False,
        is_float: bool = False,
        is_path: bool = False,
        is_datetime: bool = False,
        as_extended: bool = False,
    ) -> Any:
        """Retrieves an input by key, with options for type conversion and default values.

        This method leverages Extended Data core utilities for robust type conversions,
        including support for Path objects, datetime parsing, and numeric conversions.

        Args:
            k (str): The key for the input.
            default (Any | None): The default value if the key is not found.
            required (bool): Whether the input is required.
                Raises an error if required and not found.
            is_bool (bool): Whether to convert the input to a boolean.
            is_integer (bool): Whether to convert the input to an integer.
            is_float (bool): Whether to convert the input to a float.
            is_path (bool): Whether to convert the input to a Path object.
            is_datetime (bool): Whether to convert the input to a datetime object.
            as_extended (bool): Whether to wrap the returned value in Tier 2 containers.

        Returns:
            Any: The retrieved input, potentially converted or defaulted.
        """
        inp = to_builtin(self.inputs.get(k, default))

        if is_nothing(inp):
            inp = default

        if is_bool and not isinstance(inp, bool):
            try:
                inp = strtobool(str(inp), raise_on_error=True)
            except (TypeError, ValueError) as exc:
                message = f"Input {k} cannot be converted to boolean."
                raise RuntimeError(message) from exc

        if is_integer and inp is not None and not isinstance(inp, int):
            try:
                inp = strtoint(str(inp), raise_on_error=True)
            except (TypeError, ValueError) as exc:
                message = f"Input {k} cannot be converted to integer."
                raise RuntimeError(message) from exc

        if is_float and inp is not None and not isinstance(inp, float):
            try:
                inp = strtofloat(str(inp), raise_on_error=True)
            except (TypeError, ValueError) as exc:
                message = f"Input {k} cannot be converted to float."
                raise RuntimeError(message) from exc

        if is_path and inp is not None:
            try:
                inp = strtopath(str(inp), raise_on_error=True)
            except (TypeError, ValueError) as exc:
                message = f"Input {k} cannot be converted to Path."
                raise RuntimeError(message) from exc

        if is_datetime and inp is not None:
            try:
                inp = strtodatetime(str(inp), raise_on_error=True)
            except (TypeError, ValueError) as exc:
                message = f"Input {k} cannot be converted to datetime."
                raise RuntimeError(message) from exc

        if is_nothing(inp) and required:
            available = self._format_available_keys(self.inputs)
            message = f"Required input {k} not passed. Available input keys: {available}."
            raise RuntimeError(message)

        if as_extended:
            return extend_data(inp)

        return inp

    def decode_input(
        self,
        k: str,
        default: Any | None = None,
        required: bool = False,
        decode_from_json: bool = False,
        decode_from_yaml: bool = False,
        decode_from_base64: bool = False,
        allow_none: bool = True,
        as_extended: bool = False,
    ) -> Any:
        """Decodes an input value, optionally from Base64, JSON, or YAML.

        Args:
            k (str): The key for the input.
            default (Any | None): The default value if the key is not found.
            required (bool): Whether the input is required.
                Raises an error if required and not found.
            decode_from_json (bool): Whether to decode the input from JSON format.
            decode_from_yaml (bool): Whether to decode the input from YAML format.
            decode_from_base64 (bool): Whether to decode the input from Base64.
            allow_none (bool): Whether to allow None as a valid return value.
            as_extended (bool): Wrap decoded container values in Tier 2 Extended Data containers.

        Returns:
            Any: The decoded input, potentially converted or defaulted.
        """
        conf = self.get_input(k, default=default, required=required)

        if conf is None or conf == default:
            return conf

        conf = self._coerce_text(conf)

        if not isinstance(conf, str):
            return extend_data(conf) if as_extended else conf

        if decode_from_base64:
            try:
                conf = base64_decode(
                    conf,
                    unwrap_raw_data=decode_from_json or decode_from_yaml,
                    encoding="json" if decode_from_json else "yaml",
                    as_extended=False,
                )
            except (binascii.Error, DataDecodeError) as exc:
                message = f"Failed to decode input {k} from Base64."
                raise RuntimeError(message) from exc

            if not isinstance(conf, str):
                if conf is None and not allow_none:
                    return default
                return extend_data(conf) if as_extended else conf

        if decode_from_yaml:
            try:
                conf = decode_yaml(conf)
            except DataDecodeError as exc:
                message = f"Failed to decode input {k} from YAML."
                raise RuntimeError(message) from exc
        elif decode_from_json:
            try:
                conf = decode_json(conf)
            except DataDecodeError as exc:
                message = f"Failed to decode input {k} from JSON."
                raise RuntimeError(message) from exc

        if conf is None and not allow_none:
            return default

        if as_extended:
            return extend_data(conf)

        return conf

    def freeze_inputs(self) -> ExtendedDict:
        """Freezes the current inputs, preventing further modifications until thawed.

        Returns:
            ExtendedDict: The frozen inputs.
        """
        if is_nothing(self.frozen_inputs):
            self.frozen_inputs = ExtendedDict(deepcopy(to_builtin(self.inputs)))
            self.inputs = ExtendedDict()

        return self.frozen_inputs

    def thaw_inputs(self) -> ExtendedDict:
        """Thaws the inputs, merging the frozen inputs back into the current inputs.

        Returns:
            ExtendedDict: The thawed inputs.
        """
        if is_nothing(self.inputs):
            self.inputs = ExtendedDict(deepcopy(to_builtin(self.frozen_inputs)))
            self.frozen_inputs = ExtendedDict()
            return self.inputs

        merged = self._merge_inputs(self.inputs, self.frozen_inputs)
        self.inputs = ExtendedDict(merged)
        self.frozen_inputs = ExtendedDict()
        return self.inputs

    def snapshot_inputs(self, *, frozen: bool = False) -> ExtendedDict:
        """Return a detached Tier 2 snapshot of active or frozen inputs.

        Args:
            frozen (bool): Return frozen inputs instead of active inputs.

        Returns:
            ExtendedDict: A promoted copy of the requested input state.
        """
        source = self.frozen_inputs if frozen else self.inputs
        return ExtendedDict(deepcopy(to_builtin(source)))

    def replace_inputs(self, new_inputs: Mapping[str, Any] | None, *, clear_frozen: bool = True) -> ExtendedDict:
        """Replace active inputs with a normalized Tier 2 snapshot.

        Args:
            new_inputs (Mapping[str, Any] | None): New active input values.
            clear_frozen (bool): Whether to clear frozen inputs after replacement.

        Returns:
            ExtendedDict: The updated active input mapping.
        """
        self.inputs = ExtendedDict(deepcopy(self._normalize_inputs(new_inputs)))
        if clear_frozen:
            self.frozen_inputs = ExtendedDict()
        return self.inputs

    def merge_inputs(self, new_inputs: Mapping[str, Any] | None) -> ExtendedDict:
        """Merge new inputs into the current inputs using deep merge semantics.

        Args:
            new_inputs (Mapping[str, Any] | None): Incoming values to merge.

        Returns:
            ExtendedDict: The updated input mapping.
        """
        merged = self._merge_inputs(self.inputs, self._normalize_inputs(new_inputs))
        self.inputs = ExtendedDict(merged)
        return self.inputs

    def shift_inputs(self) -> ExtendedDict:
        """Shifts between frozen and thawed inputs.

        Returns:
            ExtendedDict: The resulting inputs after the shift.
        """
        if is_nothing(self.frozen_inputs):
            return self.freeze_inputs()

        return self.thaw_inputs()
