"""Shared contracts for transparent, reproducible analysis workflows.

The workflow layer composes already-qualified scientific primitives.  It does
not infer scientific choices, silently preprocess data, or select a preferred
analysis architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from math import isfinite
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Literal, Mapping

import numpy as np
import pandas as pd


WORKFLOW_SCHEMA_VERSION = 1
_WORKFLOW_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_ALLOWED_STEP_STATUS = frozenset({"ok", "skipped", "failed"})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze_value(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})
    return _freeze_value(value)


def _require_nonempty_text(value: str, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class WorkflowContract:
    """Versioned semantic identity for one workflow definition."""

    name: str
    version: int = 1
    scientific_scope: str = ""
    prohibitions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = _require_nonempty_text(self.name, name="name")
        if _WORKFLOW_NAME_RE.fullmatch(name) is None:
            raise ValueError(
                "workflow contract name must match ^[a-z][a-z0-9_]*$"
            )
        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("workflow contract version must be an integer")
        if self.version < 1:
            raise ValueError("workflow contract version must be >= 1")
        if not isinstance(self.prohibitions, tuple):
            raise TypeError("prohibitions must be a tuple")
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "scientific_scope",
            str(self.scientific_scope).strip(),
        )
        object.__setattr__(
            self,
            "prohibitions",
            tuple(
                _require_nonempty_text(item, name="prohibition")
                for item in self.prohibitions
            ),
        )

    @property
    def identifier(self) -> str:
        """Return the stable workflow-contract identifier."""

        return f"{self.name}:v{self.version}"


@dataclass(frozen=True)
class WorkflowDecision:
    """Record how a scientifically consequential value entered a workflow."""

    value: Any
    source: str
    criterion: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source",
            _require_nonempty_text(self.source, name="source"),
        )
        if self.criterion is not None:
            object.__setattr__(
                self,
                "criterion",
                _require_nonempty_text(self.criterion, name="criterion"),
            )
        object.__setattr__(self, "details", _freeze_mapping(self.details))


@dataclass(frozen=True)
class WorkflowStepRecord:
    """Inspectably record one ordered primitive call in a workflow."""

    name: str
    function: str
    status: Literal["ok", "skipped", "failed"]
    parameters: Mapping[str, Any] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name",
            _require_nonempty_text(self.name, name="name"),
        )
        object.__setattr__(
            self,
            "function",
            _require_nonempty_text(self.function, name="function"),
        )
        if self.status not in _ALLOWED_STEP_STATUS:
            raise ValueError(
                "status must be one of 'ok', 'skipped', or 'failed'"
            )
        elapsed = float(self.elapsed_seconds)
        if not isfinite(elapsed) or elapsed < 0.0:
            raise ValueError("elapsed_seconds must be finite and >= 0")
        object.__setattr__(self, "elapsed_seconds", elapsed)
        object.__setattr__(
            self,
            "parameters",
            _freeze_mapping(self.parameters),
        )
        if not isinstance(self.warnings, tuple):
            raise TypeError("warnings must be a tuple")
        object.__setattr__(
            self,
            "warnings",
            tuple(
                _require_nonempty_text(item, name="warning")
                for item in self.warnings
            ),
        )


@dataclass(frozen=True)
class PreprocessingStepConfig:
    """One explicitly requested preprocessing operation."""

    operation: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operation",
            _require_nonempty_text(self.operation, name="operation"),
        )
        object.__setattr__(
            self,
            "parameters",
            _freeze_mapping(self.parameters),
        )


@dataclass(frozen=True)
class PreprocessingPlan:
    """Ordered, analyst-declared preprocessing plan.

    An empty plan means that the workflow applies no preprocessing.  Scientific
    compatibility of declared steps is validated by each concrete workflow.
    """

    steps: tuple[PreprocessingStepConfig, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.steps, tuple):
            raise TypeError("steps must be a tuple")
        if not all(
            isinstance(step, PreprocessingStepConfig)
            for step in self.steps
        ):
            raise TypeError(
                "every preprocessing step must be a PreprocessingStepConfig"
            )


@dataclass(frozen=True)
class WorkflowDiagnosticConfig:
    """One explicitly requested diagnostic operation."""

    name: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name",
            _require_nonempty_text(self.name, name="diagnostic name"),
        )
        object.__setattr__(
            self,
            "parameters",
            _freeze_mapping(self.parameters),
        )


@dataclass(frozen=True)
class WorkflowDiagnosticsPlan:
    """Ordered, explicit diagnostic plan; empty means no diagnostics."""

    diagnostics: tuple[WorkflowDiagnosticConfig, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("diagnostics must be a tuple")
        if not all(
            isinstance(item, WorkflowDiagnosticConfig)
            for item in self.diagnostics
        ):
            raise TypeError(
                "every diagnostic must be a WorkflowDiagnosticConfig"
            )


@dataclass(frozen=True)
class WorkflowResultBase:
    """Shared frozen result contract for concrete workflow results."""

    workflow_contract: str
    config: Any
    steps: tuple[WorkflowStepRecord, ...]
    provenance: Mapping[str, Any]
    workflow_schema_version: int = field(
        default=WORKFLOW_SCHEMA_VERSION,
        init=False,
    )

    def __post_init__(self) -> None:
        contract = _require_nonempty_text(
            self.workflow_contract,
            name="workflow_contract",
        )
        if re.fullmatch(r"^[a-z][a-z0-9_]*:v[1-9][0-9]*$", contract) is None:
            raise ValueError(
                "workflow_contract must use the form '<name>:v<positive integer>'"
            )
        if not is_dataclass(self.config) or isinstance(self.config, type):
            raise TypeError("config must be a dataclass instance")
        if not isinstance(self.steps, tuple) or not all(
            isinstance(step, WorkflowStepRecord)
            for step in self.steps
        ):
            raise TypeError(
                "steps must be a tuple of WorkflowStepRecord objects"
            )
        if not isinstance(self.provenance, Mapping):
            raise TypeError("provenance must be a mapping")
        object.__setattr__(self, "workflow_contract", contract)
        object.__setattr__(
            self,
            "provenance",
            _freeze_mapping(self.provenance),
        )


def _jsonable(value: Any, *, path: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, np.generic):
        return _jsonable(value.item(), path=path)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        if value.dtype == object:
            return _jsonable(value.tolist(), path=path)
        return _jsonable(value.tolist(), path=path)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _jsonable(
                getattr(value, item.name),
                path=f"{path}.{item.name}",
            )
            for item in fields(value)
        }
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise TypeError(
                    f"{path} mapping keys must be non-empty strings"
                )
            out[key] = _jsonable(item, path=f"{path}.{key}")
        return out
    if isinstance(value, (tuple, list)):
        return [
            _jsonable(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise TypeError(
        f"{path} contains unsupported workflow-serialization type "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def workflow_config_dict(config: Any) -> dict[str, Any]:
    """Return a JSON-safe dictionary for a dataclass workflow config."""

    if not is_dataclass(config) or isinstance(config, type):
        raise TypeError("workflow config must be a dataclass instance")
    encoded = _jsonable(config, path="config")
    if not isinstance(encoded, dict):
        raise TypeError("workflow config must encode to a dictionary")
    return encoded


def workflow_provenance_dict(
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a JSON-safe workflow provenance mapping."""

    if not isinstance(provenance, Mapping):
        raise TypeError("workflow provenance must be a mapping")
    encoded = _jsonable(provenance, path="provenance")
    if not isinstance(encoded, dict):
        raise TypeError("workflow provenance must encode to a dictionary")
    return encoded


def workflow_steps_frame(
    steps: tuple[WorkflowStepRecord, ...],
) -> pd.DataFrame:
    """Return one audit row per ordered workflow step."""

    if not isinstance(steps, tuple) or not all(
        isinstance(step, WorkflowStepRecord) for step in steps
    ):
        raise TypeError("steps must be a tuple of WorkflowStepRecord objects")
    return pd.DataFrame(
        [
            {
                "step_index": index,
                "name": step.name,
                "function": step.function,
                "status": step.status,
                "elapsed_seconds": step.elapsed_seconds,
                "n_warnings": len(step.warnings),
            }
            for index, step in enumerate(steps, start=1)
        ],
        columns=(
            "step_index",
            "name",
            "function",
            "status",
            "elapsed_seconds",
            "n_warnings",
        ),
    )
