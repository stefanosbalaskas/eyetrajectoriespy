"""Transparent workflow infrastructure for the 1.2 development line.

This module defines shared orchestration contracts only. It deliberately does
not choose scientific estimators, preprocessing, diagnostics, or tuning values.
Concrete run_*_workflow functions are added only in separately qualified W2+ tranches.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ..portable_results import capture_environment, export_portable_result


WORKFLOW_SCHEMA_VERSION = 1
WORKFLOW_BUNDLE_SCHEMA_VERSION = 1
WORKFLOW_BUNDLE_FORMAT = "eyetrajectoriespy-workflow-bundle"

_ALLOWED_DECISION_SOURCES = {
    "analyst",
    "audited_selector",
    "workflow_contract",
    "derived",
}
_ALLOWED_STEP_STATUSES = {"completed", "failed", "skipped"}


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _jsonable(value: Any, *, path: str = "value") -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not np.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, np.generic):
        return _jsonable(value.item(), path=path)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{path} contains non-finite array values")
        return value.tolist()
    if isinstance(value, pd.Index):
        return [
            _jsonable(item, path=f"{path}[{index}]")
            for index, item in enumerate(value.tolist())
        ]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _jsonable(
                getattr(value, field.name),
                path=f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} contains a non-string mapping key")
            output[key] = _jsonable(item, path=f"{path}.{key}")
        return output
    if isinstance(value, (tuple, list)):
        return [
            _jsonable(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise TypeError(
        f"{path} contains unsupported workflow-JSON type "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


@dataclass(frozen=True)
class WorkflowDecisionRecord:
    """One scientifically relevant value and how it entered a workflow."""

    value: Any
    source: str
    criterion: str | None = None

    def __post_init__(self) -> None:
        if self.source not in _ALLOWED_DECISION_SOURCES:
            raise ValueError(
                "source must be one of "
                f"{sorted(_ALLOWED_DECISION_SOURCES)!r}"
            )
        if self.source == "audited_selector" and not self.criterion:
            raise ValueError(
                "audited_selector decisions require a non-empty criterion"
            )
        _jsonable(self.value, path="decision.value")


@dataclass(frozen=True)
class WorkflowStepRecord:
    """Auditable record of one ordered orchestration step."""

    name: str
    function: str
    status: str
    parameters: Mapping[str, Any]
    elapsed_seconds: float
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("workflow step name must be non-empty")
        if not self.function:
            raise ValueError("workflow step function must be non-empty")
        if self.status not in _ALLOWED_STEP_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_ALLOWED_STEP_STATUSES)!r}"
            )
        if not np.isfinite(self.elapsed_seconds) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative")
        frozen = _freeze_mapping(self.parameters)
        _jsonable(frozen, path=f"step[{self.name}].parameters")
        object.__setattr__(self, "parameters", frozen)
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class PreprocessingStepConfig:
    """One explicitly requested preprocessing operation."""

    function: str
    parameters: Mapping[str, Any]
    scientific_effect: str

    def __post_init__(self) -> None:
        if not self.function:
            raise ValueError("preprocessing function must be non-empty")
        if not self.scientific_effect:
            raise ValueError(
                "preprocessing scientific_effect must be explicitly described"
            )
        frozen = _freeze_mapping(self.parameters)
        _jsonable(frozen, path=f"preprocessing[{self.function}].parameters")
        object.__setattr__(self, "parameters", frozen)


@dataclass(frozen=True)
class PreprocessingPlan:
    """Ordered analyst-declared preprocessing plan.

    An empty plan means no preprocessing. No implicit default steps are added.
    """

    steps: tuple[PreprocessingStepConfig, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(self.steps))


def workflow_config_to_dict(config: Any) -> dict[str, Any]:
    """Return a strict JSON-compatible representation of a workflow config."""

    if not is_dataclass(config) or isinstance(config, type):
        raise TypeError("config must be a dataclass instance")
    value = _jsonable(config, path="config")
    if not isinstance(value, dict):
        raise TypeError("workflow config did not encode to a mapping")
    return value


def workflow_steps_frame(
    steps: Sequence[WorkflowStepRecord],
) -> pd.DataFrame:
    """Return one auditable row per ordered workflow step."""

    rows = []
    for order, step in enumerate(steps, start=1):
        rows.append(
            {
                "order": order,
                "name": step.name,
                "function": step.function,
                "status": step.status,
                "elapsed_seconds": float(step.elapsed_seconds),
                "parameters_json": json.dumps(
                    _jsonable(step.parameters),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "warning_count": len(step.warnings),
                "warnings": "\n".join(step.warnings),
            }
        )
    return pd.DataFrame(
        rows,
        columns=(
            "order",
            "name",
            "function",
            "status",
            "elapsed_seconds",
            "parameters_json",
            "warning_count",
            "warnings",
        ),
    )


def workflow_decisions_frame(
    decisions: Mapping[str, WorkflowDecisionRecord],
) -> pd.DataFrame:
    """Return one row per explicit or audited workflow decision."""

    rows = []
    for name, record in decisions.items():
        rows.append(
            {
                "name": name,
                "value_json": json.dumps(
                    _jsonable(record.value),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "source": record.source,
                "criterion": record.criterion,
            }
        )
    return pd.DataFrame(
        rows,
        columns=("name", "value_json", "source", "criterion"),
    )


def workflow_summary_frame(result: Any) -> pd.DataFrame:
    """Return a one-row generic workflow orchestration summary."""

    _validate_workflow_result(result)
    statuses = [step.status for step in result.steps]
    sources = [record.source for record in result.decisions.values()]
    return pd.DataFrame(
        [
            {
                "workflow_schema_version": int(result.workflow_schema_version),
                "workflow_contract": str(result.workflow_contract),
                "step_count": len(result.steps),
                "completed_steps": statuses.count("completed"),
                "failed_steps": statuses.count("failed"),
                "skipped_steps": statuses.count("skipped"),
                "warning_count": int(
                    sum(len(step.warnings) for step in result.steps)
                ),
                "decision_count": len(result.decisions),
                "analyst_decisions": sources.count("analyst"),
                "audited_selector_decisions": sources.count(
                    "audited_selector"
                ),
                "workflow_contract_decisions": sources.count(
                    "workflow_contract"
                ),
                "derived_decisions": sources.count("derived"),
            }
        ]
    )


def workflow_reporting_text(result: Any) -> str:
    """Return a compact generic audit description for a workflow result."""

    _validate_workflow_result(result)
    completed = sum(step.status == "completed" for step in result.steps)
    failed = sum(step.status == "failed" for step in result.steps)
    skipped = sum(step.status == "skipped" for step in result.steps)
    selected = sum(
        record.source == "audited_selector"
        for record in result.decisions.values()
    )
    analyst = sum(
        record.source == "analyst"
        for record in result.decisions.values()
    )
    return (
        f"Workflow {result.workflow_contract!r} used schema "
        f"{result.workflow_schema_version} and retained {len(result.steps)} "
        f"ordered steps ({completed} completed, {failed} failed, "
        f"{skipped} skipped). It retained {len(result.decisions)} "
        f"scientific decisions ({analyst} analyst-declared and {selected} "
        "from audited selectors). Workflow orchestration does not itself "
        "authorize hidden preprocessing, diagnostic expansion, or automatic "
        "scientific model selection."
    )


def _validate_workflow_result(result: Any) -> None:
    if not is_dataclass(result) or isinstance(result, type):
        raise TypeError("result must be a dataclass-based workflow result")
    for attribute in (
        "workflow_schema_version",
        "workflow_contract",
        "config",
        "steps",
        "decisions",
        "provenance",
    ):
        if not hasattr(result, attribute):
            raise TypeError(
                f"workflow result is missing required attribute {attribute!r}"
            )
    if int(result.workflow_schema_version) != WORKFLOW_SCHEMA_VERSION:
        raise ValueError(
            "workflow result uses an unsupported workflow schema version"
        )
    if not str(result.workflow_contract):
        raise ValueError("workflow_contract must be non-empty")
    if not all(isinstance(step, WorkflowStepRecord) for step in result.steps):
        raise TypeError("steps must contain WorkflowStepRecord objects")
    if not all(
        isinstance(name, str) and isinstance(record, WorkflowDecisionRecord)
        for name, record in result.decisions.items()
    ):
        raise TypeError(
            "decisions must map string names to WorkflowDecisionRecord objects"
        )
    workflow_config_to_dict(result.config)
    _jsonable(result.provenance, path="provenance")


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prepare_directory(
    directory: str | Path,
    *,
    overwrite: bool,
) -> Path:
    destination = Path(directory)
    if destination.exists() and any(destination.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"workflow bundle directory is not empty: {destination}"
            )
        for child in destination.iterdir():
            if child.is_dir():
                raise ValueError(
                    "overwrite does not recursively remove existing directories"
                )
            child.unlink()
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def export_workflow_bundle(
    result: Any,
    directory: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Export an auditable workflow bundle.

    The bundle contains the typed workflow result as a portable scientific
    result plus explicit config, decisions, steps, provenance, environment,
    reports, tabular outputs and SHA256 checksums. Figure export is
    intentionally deferred to the later workflow plotting/gallery tranche.
    """

    _validate_workflow_result(result)
    destination = _prepare_directory(directory, overwrite=overwrite)
    config = workflow_config_to_dict(result.config)
    steps = workflow_steps_frame(result.steps)
    decisions = workflow_decisions_frame(result.decisions)
    provenance = _jsonable(result.provenance, path="provenance")
    environment = capture_environment()

    (destination / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (destination / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (destination / "environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    steps.to_csv(destination / "steps.csv", index=False)
    decisions.to_csv(destination / "decisions.csv", index=False)

    portable_directory = destination / "result"
    export_portable_result(
        result,
        portable_directory,
        include_environment=False,
    )

    report_names: list[str] = []
    reports = getattr(result, "reports", None)
    if reports:
        report_directory = destination / "reports"
        report_directory.mkdir()
        for name, text in reports.items():
            if Path(name).name != name:
                raise ValueError("report names must be simple filenames")
            filename = name if Path(name).suffix else f"{name}.txt"
            (report_directory / filename).write_text(
                text.rstrip() + "\n",
                encoding="utf-8",
            )
            report_names.append(filename)

    table_names: list[str] = []
    tables = getattr(result, "tables", None)
    if tables:
        table_directory = destination / "tables"
        table_directory.mkdir()
        for name, table in tables.items():
            if Path(name).name != name:
                raise ValueError("table names must be simple filenames")
            filename = name if Path(name).suffix else f"{name}.csv"
            if Path(filename).suffix.lower() != ".csv":
                raise ValueError("workflow W1 tables must use CSV filenames")
            if not isinstance(table, pd.DataFrame):
                raise TypeError("workflow tables must be pandas DataFrames")
            table.to_csv(table_directory / filename, index=False)
            table_names.append(filename)

    manifest = {
        "schema_version": WORKFLOW_BUNDLE_SCHEMA_VERSION,
        "format": WORKFLOW_BUNDLE_FORMAT,
        "workflow_schema_version": int(result.workflow_schema_version),
        "workflow_contract": str(result.workflow_contract),
        "result_type": (
            f"{result.__class__.__module__}.{result.__class__.__qualname__}"
        ),
        "portable_result_directory": "result",
        "reports": sorted(report_names),
        "tables": sorted(table_names),
        "figure_export_included": False,
        "figure_export_status": (
            "deferred_to_later_workflow_plotting_tranche"
        ),
    }
    (destination / "workflow.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checksum_lines = []
    for path in sorted(
        item
        for item in destination.rglob("*")
        if item.is_file() and item.name != "SHA256SUMS"
    ):
        checksum_lines.append(
            f"{_sha256(path)}  {path.relative_to(destination).as_posix()}"
        )
    (destination / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    return destination
