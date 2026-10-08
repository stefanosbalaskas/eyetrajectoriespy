"""Shared contracts for transparent sparse workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable
import warnings

import numpy as np

from ..observation_process import (
    ObservationProcessData,
    ObservationProcessDiagnosticResult,
    diagnose_observation_process,
)
from ._core import PreprocessingPlan, WorkflowStepRecord


@dataclass(frozen=True)
class ScoreUncertaintyConfig:
    """Explicit conditional-score uncertainty request."""

    condition_limit: float | None = None
    failure_action: str = "error"

    def __post_init__(self) -> None:
        if self.condition_limit is not None:
            value = float(self.condition_limit)
            if not np.isfinite(value) or value <= 1:
                raise ValueError(
                    "condition_limit must be finite and greater than 1"
                )
            object.__setattr__(self, "condition_limit", value)
        if self.failure_action not in {"error", "retain_nan"}:
            raise ValueError("failure_action must be 'error' or 'retain_nan'")


@dataclass(frozen=True)
class ObservationDiagnosticConfig:
    """Explicit settings for candidate-sample observation diagnostics."""

    predictors: tuple[str, ...] | None = None
    history_predictors: tuple[str, ...] = ()
    eccentricity_reference: tuple[float, float] | None = None
    risk_set: str = "all_candidates"
    time_basis: str | None = "linear"
    time_bins: int | tuple[float, ...] | None = None
    association_bins: int | tuple[float, ...] | None = 4
    low_support_threshold: float = 0.10

    def __post_init__(self) -> None:
        if self.predictors is not None:
            object.__setattr__(
                self,
                "predictors",
                tuple(map(str, self.predictors)),
            )
        object.__setattr__(
            self,
            "history_predictors",
            tuple(map(str, self.history_predictors)),
        )
        if self.eccentricity_reference is not None:
            reference = tuple(map(float, self.eccentricity_reference))
            if len(reference) != 2 or not np.all(np.isfinite(reference)):
                raise ValueError(
                    "eccentricity_reference must contain two finite values"
                )
            object.__setattr__(self, "eccentricity_reference", reference)
        threshold = float(self.low_support_threshold)
        if not np.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "low_support_threshold must be finite and within [0, 1]"
            )
        object.__setattr__(self, "low_support_threshold", threshold)


def normalized_grid(
    values: tuple[float, ...] | list[float] | np.ndarray,
    *,
    name: str,
) -> tuple[float, ...]:
    """Return a finite, strictly increasing immutable grid."""

    grid = np.asarray(values, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError(
            f"{name} must be a finite strictly increasing one-dimensional grid"
        )
    return tuple(map(float, grid))


def positive_candidates(
    values: tuple[float, ...] | list[float],
    *,
    name: str,
) -> tuple[float, ...]:
    """Return unique positive immutable candidate values."""

    converted = tuple(float(value) for value in values)
    if not converted:
        raise ValueError(f"{name} must contain at least one candidate")
    if not np.all(np.isfinite(converted)) or any(value <= 0 for value in converted):
        raise ValueError(f"{name} must contain finite positive values")
    return tuple(sorted(set(converted)))


def require_empty_sparse_preprocessing(
    preprocessing: PreprocessingPlan,
    *,
    workflow_contract: str,
) -> None:
    """Fail closed until sparse-route preprocessing execution is qualified."""

    if not isinstance(preprocessing, PreprocessingPlan):
        raise TypeError("preprocessing must be a PreprocessingPlan")
    if preprocessing.steps:
        raise ValueError(
            f"{workflow_contract} currently requires an empty preprocessing "
            "plan; sparse raw observations are passed to qualified primitive "
            "APIs on their native grids and no in-workflow transformation has "
            "yet been qualified"
        )


def timed_step(
    *,
    name: str,
    function: str,
    parameters: dict[str, Any],
    call: Callable[[], Any],
) -> tuple[Any, WorkflowStepRecord]:
    """Execute one qualified primitive and retain timing/warnings."""

    started = perf_counter()
    caught: list[str] = []
    try:
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            result = call()
            caught = [str(record.message) for record in records]
    except Exception:
        elapsed = perf_counter() - started
        # Failed primitive calls are deliberately not converted into a
        # successful workflow result. The raised exception remains authoritative.
        _ = WorkflowStepRecord(
            name=name,
            function=function,
            status="failed",
            parameters=parameters,
            elapsed_seconds=elapsed,
            warnings=tuple(caught),
        )
        raise
    elapsed = perf_counter() - started
    return result, WorkflowStepRecord(
        name=name,
        function=function,
        status="completed",
        parameters=parameters,
        elapsed_seconds=elapsed,
        warnings=tuple(caught),
    )


def run_observation_diagnostics(
    *,
    process: ObservationProcessData | None,
    config: ObservationDiagnosticConfig | None,
) -> tuple[ObservationProcessDiagnosticResult | None, WorkflowStepRecord | None]:
    """Run diagnostics only when both process and explicit config are supplied."""

    if config is None and process is None:
        return None, None
    if config is None and process is not None:
        raise ValueError(
            "observation_process was supplied without an explicit "
            "ObservationDiagnosticConfig"
        )
    if config is not None and process is None:
        raise ValueError(
            "ObservationDiagnosticConfig requires a separately supplied "
            "ObservationProcessData candidate-sample denominator"
        )
    assert config is not None
    assert process is not None
    parameters = {
        "predictors": config.predictors,
        "history_predictors": config.history_predictors,
        "eccentricity_reference": config.eccentricity_reference,
        "risk_set": config.risk_set,
        "time_basis": config.time_basis,
        "time_bins": config.time_bins,
        "association_bins": config.association_bins,
        "low_support_threshold": config.low_support_threshold,
    }
    return timed_step(
        name="observation_process_diagnostics",
        function="diagnose_observation_process",
        parameters=parameters,
        call=lambda: diagnose_observation_process(process, **parameters),
    )
