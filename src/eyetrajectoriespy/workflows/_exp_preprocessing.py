"""E1: conservative opt-in execution of explicitly declared preprocessing plans.

Experimental candidate API. This module composes established operations and
never silently converts sparse observations to a common grid.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from time import perf_counter
from typing import Any, Callable
import warnings

import numpy as np
import pandas as pd

from ..preprocessing import (
    center_on_landmark,
    interpolate_short_gaps,
    normalize_coordinates,
    normalize_time,
    resample_to_grid,
    smooth_trajectories,
)
from ..registration import register_to_landmarks
from ..types import IrregularTrajectorySet, RegistrationResult, TrajectorySet
from ._core import (
    PreprocessingPlan,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
    workflow_config_to_dict,
)

_OPERATIONS: dict[str, Callable[..., TrajectorySet]] = {
    "center_on_landmark": center_on_landmark,
    "interpolate_short_gaps": interpolate_short_gaps,
    "normalize_coordinates": normalize_coordinates,
    "normalize_time": normalize_time,
    "resample_to_grid": resample_to_grid,
    "smooth_trajectories": smooth_trajectories,
    "register_to_landmarks": register_to_landmarks,
}


@dataclass(frozen=True)
class PreprocessingExecutionResult:
    """Transformed data and a complete ordered, auditable preprocessing trail."""

    data: TrajectorySet | IrregularTrajectorySet
    steps: tuple[WorkflowStepRecord, ...]
    audit: pd.DataFrame
    phase_results: tuple[RegistrationResult, ...]
    provenance: dict[str, Any]


def _data_summary(data: TrajectorySet | IrregularTrajectorySet) -> dict[str, Any]:
    if isinstance(data, TrajectorySet):
        observed = np.isfinite(data.values)
        support = np.count_nonzero(observed, axis=1)
        samples = int(data.values.size)
        finite = int(observed.sum())
        return {
            "layout": "common_grid",
            "n_curves": data.n_curves,
            "n_dimensions": data.n_dimensions,
            "grid_size": data.n_time,
            "samples": samples,
            "finite_samples": finite,
            "missing_samples": samples - finite,
            "min_dimension_support": int(support.min()) if support.size else 0,
            "time_start": float(data.time[0]),
            "time_end": float(data.time[-1]),
            "time_unit": data.time_unit,
            "coordinate_system": data.coordinate_system,
        }
    observed = [np.isfinite(a) for a in data.values]
    support = [int(x.sum()) for x in observed]
    samples = sum(x.size for x in observed)
    finite = sum(support)
    return {
        "layout": "irregular",
        "n_curves": data.n_curves,
        "n_dimensions": data.n_dimensions,
        "grid_size": None,
        "samples": samples,
        "finite_samples": finite,
        "missing_samples": samples - finite,
        "min_dimension_support": min(
            (int(np.isfinite(a).sum(axis=0).min()) for a in data.values), default=0
        ),
        "time_start": float(min(t[0] for t in data.time)),
        "time_end": float(max(t[-1] for t in data.time)),
        "time_unit": data.time_unit,
        "coordinate_system": data.coordinate_system,
    }


def run_preprocessing_plan(
    data: TrajectorySet | IrregularTrajectorySet,
    *,
    plan: PreprocessingPlan,
) -> PreprocessingExecutionResult:
    """Run analyst-declared steps in order; never impute/drop data implicitly.

    Only existing qualified common-grid operations are allowed. A nonempty plan
    on irregular data fails before the first operation: dense conversion must be
    a separately reviewed scientific decision. Registration retains the full
    warping arrays via `phase_results`. Each step records support and unit changes.
    """

    if not isinstance(data, (TrajectorySet, IrregularTrajectorySet)):
        raise TypeError("data must be TrajectorySet or IrregularTrajectorySet")
    if not isinstance(plan, PreprocessingPlan):
        raise TypeError("plan must be a PreprocessingPlan")
    if plan.steps and isinstance(data, IrregularTrajectorySet):
        raise ValueError("Nonempty preprocessing of irregular data is not qualified; no implicit densification")
    for step in plan.steps:
        if step.function not in _OPERATIONS:
            raise ValueError(f"Unsupported preprocessing function: {step.function!r}")
    current = data
    original_summary = _data_summary(data)
    step_records: list[WorkflowStepRecord] = []
    rows: list[dict[str, Any]] = []
    phase_results: list[RegistrationResult] = []
    for order, step in enumerate(plan.steps, start=1):
        assert isinstance(current, TrajectorySet)
        params = dict(step.parameters)
        if step.function == "resample_to_grid":
            if "grid" not in params:
                raise ValueError("resample_to_grid requires an explicit grid")
            params["grid"] = np.asarray(params["grid"], dtype=float)
        if step.function == "normalize_coordinates" and current.coordinate_system != "pixels":
            raise ValueError("normalize_coordinates requires explicitly pixel-valued coordinates")
        if step.function == "register_to_landmarks" and "observed_landmarks" not in params:
            raise ValueError("register_to_landmarks requires observed_landmarks")
        before = _data_summary(current)
        start = perf_counter()
        with warnings.catch_warnings(record=True) as detected:
            warnings.simplefilter("always")
            if step.function == "register_to_landmarks":
                registration = register_to_landmarks(current, **params)
                phase_results.append(registration)
                transformed = registration.registered
            else:
                transformed = _OPERATIONS[step.function](current, **params)
        after = _data_summary(transformed)
        if transformed.n_curves != current.n_curves or transformed.curve_ids != current.curve_ids:
            raise RuntimeError("Preprocessing must never silently delete or reorder trajectories")
        elapsed = perf_counter() - start
        warns = tuple(str(item.message) for item in detected)
        if step.function == "register_to_landmarks":
            warns += ("Registration modifies phase; retain the warping functions and compare unregistered sensitivity.",)
        records = WorkflowStepRecord(
            name=f"preprocessing_{order:02d}",
            function=step.function,
            status="completed",
            parameters={**dict(step.parameters), "scientific_effect": step.scientific_effect},
            elapsed_seconds=elapsed,
            warnings=warns,
        )
        step_records.append(records)
        rows.append({
            "order": order, "function": step.function, "scientific_effect": step.scientific_effect,
            "n_curves_before": before["n_curves"], "n_curves_after": after["n_curves"],
            "finite_samples_before": before["finite_samples"],
            "finite_samples_after": after["finite_samples"],
            "missing_samples_before": before["missing_samples"],
            "missing_samples_after": after["missing_samples"],
            "time_unit_before": before["time_unit"], "time_unit_after": after["time_unit"],
            "coordinate_system_before": before["coordinate_system"],
            "coordinate_system_after": after["coordinate_system"],
            "warning_count": len(warns),
        })
        current = transformed
    return PreprocessingExecutionResult(
        data=current,
        steps=tuple(step_records),
        audit=pd.DataFrame(rows, columns=[
            "order", "function", "scientific_effect", "n_curves_before", "n_curves_after",
            "finite_samples_before", "finite_samples_after",
            "missing_samples_before", "missing_samples_after",
            "time_unit_before", "time_unit_after",
            "coordinate_system_before", "coordinate_system_after", "warning_count",
        ]),
        phase_results=tuple(phase_results),
        provenance={
            "preprocessing_executed": bool(step_records),
            "no_automatic_interpolation_or_exclusion": True,
            "plan": workflow_config_to_dict(plan),
            "before": original_summary,
            "after": _data_summary(current),
            "phase_warping_retained": bool(phase_results),
        },
    )


def run_workflow_preprocessed(
    data: TrajectorySet,
    *,
    config: Any,
    runner: Callable[..., Any],
    **runner_kwargs: Any,
) -> Any:
    """Execute E1 before an existing dense scientific workflow.

    The underlying v1 runner retains its empty-plan contract. The returned
    result embeds original declared config and added audit records; it does not
    claim that the v1 entry point itself supports preprocessing.
    """

    if not hasattr(config, "preprocessing") or not isinstance(config.preprocessing, PreprocessingPlan):
        raise TypeError("config must declare a PreprocessingPlan")
    transformed = run_preprocessing_plan(data, plan=config.preprocessing)
    empty_config = replace(config, preprocessing=PreprocessingPlan())
    fitted = runner(transformed.data, config=empty_config, **runner_kwargs)
    if not hasattr(fitted, "workflow_contract") or not hasattr(fitted, "steps"):
        raise TypeError("runner must return a typed workflow result")
    decisions = dict(fitted.decisions)
    if transformed.steps:
        decisions["preprocessing_plan"] = WorkflowDecisionRecord(
            workflow_config_to_dict(config.preprocessing), "analyst"
        )
    tables = dict(getattr(fitted, "tables", {}))
    if transformed.steps:
        tables["preprocessing_audit"] = transformed.audit.copy()
    for order, phase in enumerate(transformed.phase_results, start=1):
        # Preserve the complete phase map in the scientific result and its
        # portable tabular bundle, not just a Boolean provenance flag.
        n_curves, n_times = phase.warping_functions.shape
        reference_time = np.tile(phase.original.time, n_curves)
        source_time = phase.warping_functions.reshape(-1)
        tables[f"registration_{order:02d}_warping"] = pd.DataFrame({
            "curve_id": np.repeat(phase.original.curve_ids, n_times),
            "reference_time": reference_time,
            "source_time": source_time,
            "displacement": source_time - reference_time,
            "time_unit": phase.original.time_unit,
        })
    return replace(
        fitted,
        config=config,
        steps=(*transformed.steps, *fitted.steps),
        decisions=decisions,
        tables=tables,
        provenance={**dict(fitted.provenance), **transformed.provenance},
    )
