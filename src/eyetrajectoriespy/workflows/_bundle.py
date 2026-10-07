"""Integrity-checked reproducibility bundles for workflow results."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
from typing import Any, Mapping

import pandas as pd

from ..portable_results import (
    PortableScientificResultSnapshot,
    capture_environment,
    export_portable_result,
    load_portable_result,
)
from ._core import (
    WORKFLOW_SCHEMA_VERSION,
    WorkflowStepRecord,
    _jsonable,
    workflow_config_dict,
    workflow_provenance_dict,
)


WORKFLOW_BUNDLE_SCHEMA_VERSION = 1
WORKFLOW_BUNDLE_FORMAT = "eyetrajectoriespy-workflow-bundle"
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class WorkflowBundleSnapshot:
    """Loaded and checksum-verified workflow reproducibility bundle."""

    workflow_schema_version: int
    workflow_contract: str
    manifest: Mapping[str, Any]
    config: Mapping[str, Any]
    provenance: Mapping[str, Any]
    steps: tuple[Mapping[str, Any], ...]
    environment: Mapping[str, Any] | None
    result: PortableScientificResultSnapshot
    tables: tuple[str, ...]
    reports: tuple[str, ...]
    figures: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(name: str, *, kind: str) -> str:
    if not isinstance(name, str) or _SAFE_NAME_RE.fullmatch(name) is None:
        raise ValueError(
            f"{kind} names must match ^[A-Za-z0-9][A-Za-z0-9._-]*$"
        )
    return name


def _prepare_destination(
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
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def _contract_identifier(result: Any) -> str:
    value = getattr(result, "workflow_contract", None)
    if not isinstance(value, str) or not value.strip():
        raise TypeError(
            "workflow result must expose a non-empty workflow_contract string"
        )
    return value.strip()


def _workflow_result_contract(result: Any) -> tuple[int, str]:
    if not is_dataclass(result) or isinstance(result, type):
        raise TypeError("workflow result must be a dataclass instance")
    schema_version = getattr(result, "workflow_schema_version", None)
    if schema_version != WORKFLOW_SCHEMA_VERSION:
        raise ValueError(
            "workflow result schema version mismatch: "
            f"{schema_version!r} != {WORKFLOW_SCHEMA_VERSION}"
        )
    contract = _contract_identifier(result)
    config = getattr(result, "config", None)
    workflow_config_dict(config)
    steps = getattr(result, "steps", None)
    if not isinstance(steps, tuple) or not all(
        isinstance(step, WorkflowStepRecord) for step in steps
    ):
        raise TypeError(
            "workflow result steps must be a tuple of WorkflowStepRecord objects"
        )
    provenance = getattr(result, "provenance", None)
    workflow_provenance_dict(provenance)
    return schema_version, contract


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_optional_tables(
    destination: Path,
    tables: Mapping[str, pd.DataFrame] | None,
) -> tuple[str, ...]:
    if tables is None:
        return ()
    if not isinstance(tables, Mapping):
        raise TypeError("tables must be a mapping of names to DataFrames")
    validated = [
        (_safe_name(name, kind="table"), frame)
        for name, frame in tables.items()
    ]
    target = destination / "tables"
    names: list[str] = []
    for safe, frame in sorted(validated, key=lambda item: item[0]):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"table {safe!r} must be a pandas DataFrame")
        target.mkdir(parents=True, exist_ok=True)
        filename = f"{safe}.csv"
        frame.to_csv(target / filename, index=False)
        names.append(filename)
    return tuple(names)


def _write_optional_reports(
    destination: Path,
    reports: Mapping[str, str] | None,
) -> tuple[str, ...]:
    if reports is None:
        return ()
    if not isinstance(reports, Mapping):
        raise TypeError("reports must be a mapping of names to strings")
    validated = [
        (_safe_name(name, kind="report"), report)
        for name, report in reports.items()
    ]
    target = destination / "reports"
    names: list[str] = []
    for safe, report in sorted(validated, key=lambda item: item[0]):
        if not isinstance(report, str):
            raise TypeError(f"report {safe!r} must be a string")
        target.mkdir(parents=True, exist_ok=True)
        filename = f"{safe}.txt"
        (target / filename).write_text(report, encoding="utf-8")
        names.append(filename)
    return tuple(names)


def _figure_object(value: Any) -> Any:
    if hasattr(value, "savefig") and callable(value.savefig):
        return value
    figure = getattr(value, "figure", None)
    if figure is not None and hasattr(figure, "savefig") and callable(figure.savefig):
        return figure
    raise TypeError(
        "workflow figures must be matplotlib-like Figure or Axes objects"
    )


def _write_optional_figures(
    destination: Path,
    figures: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if figures is None:
        return ()
    if not isinstance(figures, Mapping):
        raise TypeError("figures must be a mapping of names to figure objects")
    validated = [
        (_safe_name(name, kind="figure"), value)
        for name, value in figures.items()
    ]
    target = destination / "figures"
    names: list[str] = []
    for safe, value in sorted(validated, key=lambda item: item[0]):
        figure = _figure_object(value)
        target.mkdir(parents=True, exist_ok=True)
        filename = f"{safe}.png"
        figure.savefig(target / filename)
        names.append(filename)
    return tuple(names)


def _write_checksums(destination: Path) -> None:
    paths = sorted(
        path
        for path in destination.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    lines = [
        f"{_sha256(path)}  {path.relative_to(destination).as_posix()}"
        for path in paths
    ]
    (destination / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def export_workflow_bundle(
    result: Any,
    directory: str | Path,
    *,
    tables: Mapping[str, pd.DataFrame] | None = None,
    reports: Mapping[str, str] | None = None,
    figures: Mapping[str, Any] | None = None,
    include_environment: bool = True,
    overwrite: bool = False,
) -> Path:
    """Export a complete, inspectable workflow reproducibility bundle.

    The workflow result remains a typed dataclass.  Optional tables, reports,
    and figures are exports of already-computed objects; the exporter does not
    trigger diagnostics, inference, plotting, or model selection.
    """

    schema_version, contract = _workflow_result_contract(result)
    destination = _prepare_destination(directory, overwrite=overwrite)

    config = workflow_config_dict(result.config)
    provenance = workflow_provenance_dict(result.provenance)
    steps = _jsonable(result.steps, path="steps")
    environment = capture_environment() if include_environment else None

    _write_json(destination / "config.json", config)
    _write_json(destination / "provenance.json", provenance)
    _write_json(destination / "steps.json", steps)
    if environment is not None:
        _write_json(destination / "environment.json", environment)

    result_directory = destination / "results" / "workflow-result"
    export_portable_result(
        result,
        result_directory,
        include_environment=False,
    )

    table_names = _write_optional_tables(destination, tables)
    report_names = _write_optional_reports(destination, reports)
    figure_names = _write_optional_figures(destination, figures)

    manifest = {
        "schema_version": WORKFLOW_BUNDLE_SCHEMA_VERSION,
        "format": WORKFLOW_BUNDLE_FORMAT,
        "workflow_schema_version": schema_version,
        "workflow_contract": contract,
        "result_type": (
            f"{result.__class__.__module__}.{result.__class__.__qualname__}"
        ),
        "environment_file": (
            "environment.json" if environment is not None else None
        ),
        "config_file": "config.json",
        "provenance_file": "provenance.json",
        "steps_file": "steps.json",
        "portable_result_directory": "results/workflow-result",
        "tables": list(table_names),
        "reports": list(report_names),
        "figures": list(figure_names),
        "scope": (
            "Configured workflow decisions, ordered step audit, workflow "
            "provenance, portable scientific result state, optional precomputed "
            "tables/reports/figures, environment provenance, and file checksums."
        ),
    }
    _write_json(destination / "workflow.json", manifest)
    _write_checksums(destination)
    return destination


def _verify_checksums(source: Path) -> None:
    checksum_path = source / "SHA256SUMS"
    if not checksum_path.is_file():
        raise FileNotFoundError(
            f"workflow bundle checksum file not found: {checksum_path}"
        )
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if separator != "  " or not digest or not relative:
            raise ValueError("invalid workflow bundle checksum line")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(
                f"unsafe workflow bundle checksum path: {relative!r}"
            )
        path = source / relative_path
        try:
            resolved = path.resolve()
            resolved.relative_to(source.resolve())
        except (OSError, ValueError) as error:
            raise ValueError(
                f"unsafe workflow bundle checksum path: {relative!r}"
            ) from error
        if not resolved.is_file():
            raise FileNotFoundError(
                f"workflow bundle payload not found: {resolved}"
            )
        if _sha256(resolved) != digest:
            raise ValueError(
                f"workflow bundle checksum mismatch: {relative}"
            )


def load_workflow_bundle(
    directory: str | Path,
) -> WorkflowBundleSnapshot:
    """Load and integrity-check a workflow reproducibility bundle."""

    source = Path(directory)
    manifest_path = source / "workflow.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"workflow bundle manifest not found: {manifest_path}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != WORKFLOW_BUNDLE_FORMAT:
        raise ValueError("not an eyetrajectoriespy workflow bundle")
    if manifest.get("schema_version") != WORKFLOW_BUNDLE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported workflow bundle schema version "
            f"{manifest.get('schema_version')!r}"
        )
    if manifest.get("workflow_schema_version") != WORKFLOW_SCHEMA_VERSION:
        raise ValueError(
            "unsupported workflow result schema version "
            f"{manifest.get('workflow_schema_version')!r}"
        )

    _verify_checksums(source)

    config = json.loads(
        (source / manifest["config_file"]).read_text(encoding="utf-8")
    )
    provenance = json.loads(
        (source / manifest["provenance_file"]).read_text(encoding="utf-8")
    )
    steps_value = json.loads(
        (source / manifest["steps_file"]).read_text(encoding="utf-8")
    )
    if not isinstance(steps_value, list):
        raise ValueError("workflow steps payload must be a list")

    environment_file = manifest.get("environment_file")
    environment = (
        json.loads((source / environment_file).read_text(encoding="utf-8"))
        if environment_file is not None
        else None
    )
    result = load_portable_result(
        source / manifest["portable_result_directory"]
    )

    return WorkflowBundleSnapshot(
        workflow_schema_version=int(manifest["workflow_schema_version"]),
        workflow_contract=str(manifest["workflow_contract"]),
        manifest=manifest,
        config=config,
        provenance=provenance,
        steps=tuple(steps_value),
        environment=environment,
        result=result,
        tables=tuple(str(value) for value in manifest.get("tables", ())),
        reports=tuple(str(value) for value in manifest.get("reports", ())),
        figures=tuple(str(value) for value in manifest.get("figures", ())),
    )
