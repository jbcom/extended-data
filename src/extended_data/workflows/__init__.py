"""Tier 3 workflow composition over Extended Data primitives and containers."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

from extended_data.containers import ExtendedDict, extend_data, to_builtin
from extended_data.io.exporters import make_raw_data_export_safe, wrap_raw_data_for_export
from extended_data.io.files import DataFile, FilePath, write_file


WorkflowAction: TypeAlias = Callable[[Any], Any]
StepLike: TypeAlias = "WorkflowStep | tuple[str, WorkflowAction] | WorkflowAction"


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """A named transformation in a data workflow."""

    name: str
    action: WorkflowAction

    def __call__(self, value: Any) -> Any:
        """Apply the step to a workflow value."""
        return self.action(value)


@dataclass(frozen=True, slots=True, init=False)
class WorkflowResult:
    """The completed value and audit trail for a data workflow."""

    value: Any
    steps: tuple[str, ...]
    output_path: Path | None
    _metadata: ExtendedDict = field(repr=False)

    def __init__(
        self,
        value: Any,
        steps: Iterable[str] = (),
        output_path: Path | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Store workflow metadata as promoted detached data."""
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "steps", tuple(steps))
        object.__setattr__(self, "output_path", output_path)
        object.__setattr__(self, "_metadata", ExtendedDict(metadata or {}))

    @property
    def metadata(self) -> ExtendedDict:
        """Return a detached promoted copy of workflow metadata."""
        return ExtendedDict(to_builtin(self._metadata))

    def as_builtin(self) -> Any:
        """Return the workflow value lowered to built-in Python containers."""
        return to_builtin(self.value)

    def as_extended(self) -> Any:
        """Return a detached workflow value promoted to Extended Data containers."""
        return extend_data(deepcopy(to_builtin(self.value)))

    def to_export_safe(self, *, export_to_yaml: bool = False) -> Any:
        """Return the workflow value converted to export-safe primitive data."""
        return make_raw_data_export_safe(self.value, export_to_yaml=export_to_yaml)

    def wrap_for_export(self, allow_encoding: bool | str = True, **format_opts: Any) -> str:
        """Return the workflow value wrapped as an encoded export string."""
        return wrap_raw_data_for_export(self.value, allow_encoding=allow_encoding, **format_opts)


class DataWorkflow:
    """Compose file decoding, transformations, and exports as a Tier 3 primitive."""

    def __init__(
        self,
        value: Any,
        *,
        steps: Iterable[str] = (),
        as_extended: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Create a workflow from an existing value."""
        self._value = extend_data(value) if as_extended else value
        self._steps = tuple(steps)
        self._as_extended = as_extended
        self._metadata = ExtendedDict(metadata or {})

    @property
    def value(self) -> Any:
        """Return the current workflow value."""
        return self._value

    @property
    def steps(self) -> tuple[str, ...]:
        """Return the names of executed workflow steps."""
        return self._steps

    @property
    def metadata(self) -> ExtendedDict:
        """Return a detached promoted copy of workflow metadata."""
        return ExtendedDict(to_builtin(self._metadata))

    @classmethod
    def from_value(
        cls,
        value: Any,
        *,
        as_extended: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> DataWorkflow:
        """Start a workflow from an in-memory value."""
        return cls(value, steps=("value",), as_extended=as_extended, metadata=metadata)

    @classmethod
    def from_data_file(cls, artifact: DataFile, *, as_extended: bool = True) -> DataWorkflow:
        """Start a workflow from a decoded DataFile artifact."""
        value = artifact.as_extended() if as_extended else artifact.as_builtin()
        return cls(
            value,
            steps=(f"data_file:{artifact.source}",),
            as_extended=as_extended,
            metadata=artifact.metadata,
        )

    @classmethod
    def decode(
        cls,
        file_data: str | memoryview | bytes | bytearray,
        *,
        file_path: FilePath | None = None,
        suffix: str | None = None,
        as_extended: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> DataWorkflow:
        """Start a workflow by decoding structured text or bytes."""
        artifact = DataFile.decode(
            file_data,
            file_path=file_path,
            suffix=suffix,
            as_extended=as_extended,
            metadata=metadata,
        )
        return cls(
            artifact.data,
            steps=(_decode_step_name(file_path=file_path, suffix=suffix),),
            as_extended=as_extended,
            metadata=artifact.metadata,
        )

    @classmethod
    def from_file(
        cls,
        file_path: FilePath,
        *,
        suffix: str | None = None,
        as_extended: bool = True,
        charset: str = "utf-8",
        errors: str = "strict",
        tld: Path | None = None,
    ) -> DataWorkflow:
        """Read and decode a local file or URL into a workflow."""
        artifact = DataFile.read(
            file_path,
            suffix=suffix,
            as_extended=as_extended,
            charset=charset,
            errors=errors,
            tld=tld,
        )
        return cls(
            artifact.data,
            steps=(f"read:{file_path}",),
            as_extended=as_extended,
            metadata=artifact.metadata,
        )

    def then(
        self,
        step: StepLike,
        *,
        name: str | None = None,
        as_extended: bool | None = None,
    ) -> DataWorkflow:
        """Apply one transformation and return the next workflow state."""
        workflow_step = _coerce_step(step, name=name)
        next_value = workflow_step(self._value)
        should_extend = self._as_extended if as_extended is None else as_extended
        if should_extend:
            next_value = extend_data(next_value)
        return DataWorkflow(
            next_value,
            steps=(*self._steps, workflow_step.name),
            as_extended=should_extend,
            metadata=self._metadata,
        )

    def run(self, *steps: StepLike, as_extended: bool | None = None) -> DataWorkflow:
        """Apply multiple transformations in order."""
        workflow = self
        for step in steps:
            workflow = workflow.then(step, as_extended=as_extended)
        return workflow

    def as_builtin(self) -> DataWorkflow:
        """Return the next workflow state with built-in Python containers."""
        return DataWorkflow(
            to_builtin(self._value),
            steps=(*self._steps, "to_builtin"),
            as_extended=False,
            metadata=self._metadata,
        )

    def as_extended(self) -> DataWorkflow:
        """Return the next workflow state with Extended Data containers."""
        return DataWorkflow(
            extend_data(self._value),
            steps=(*self._steps, "as_extended"),
            as_extended=True,
            metadata=self._metadata,
        )

    def result(self) -> WorkflowResult:
        """Return a completed workflow result without writing an output artifact."""
        return WorkflowResult(value=self._value, steps=self._steps, metadata=self.metadata)

    def write(
        self,
        file_path: FilePath,
        *,
        encoding: str | None = None,
        charset: str = "utf-8",
        allow_empty: bool = False,
        tld: Path | None = None,
        as_builtin: bool = True,
    ) -> WorkflowResult:
        """Write the current workflow value and return the completed result."""
        output_value = to_builtin(self._value) if as_builtin else self._value
        output_path = write_file(
            file_path,
            output_value,
            encoding=encoding,
            charset=charset,
            allow_empty=allow_empty,
            tld=tld,
        )
        if output_path is None:
            raise ValueError("Workflow output was empty; pass allow_empty=True to write it")

        return WorkflowResult(
            value=self._value,
            steps=(*self._steps, f"write:{file_path}"),
            output_path=output_path,
            metadata=self.metadata,
        )


def _coerce_step(step: StepLike, *, name: str | None = None) -> WorkflowStep:
    """Normalize supported step declarations to WorkflowStep."""
    if isinstance(step, WorkflowStep):
        if name is None:
            return step
        return WorkflowStep(name=name, action=step.action)

    if isinstance(step, tuple):
        step_name, action = step
        return WorkflowStep(name=name or step_name, action=action)

    inferred_name = name
    if inferred_name is None:
        raw_name = getattr(step, "__name__", None)
        inferred_name = raw_name if isinstance(raw_name, str) else step.__class__.__name__
    return WorkflowStep(name=inferred_name, action=step)


def _decode_step_name(*, file_path: FilePath | None, suffix: str | None) -> str:
    """Return a stable step name for decode-only workflows."""
    if file_path is not None:
        return f"decode:{file_path}"
    if suffix is not None:
        return f"decode:{suffix}"
    return "decode"


__all__ = [
    "DataWorkflow",
    "StepLike",
    "WorkflowAction",
    "WorkflowResult",
    "WorkflowStep",
]
