"""Private known-truth simulation support for observation-process diagnostics.

The A3 public surface is diagnostic only. This module exists to qualify that
surface against explicit candidate schedules and known retention mechanisms.
It deliberately does not expose an observation-process correction estimator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ._functional_simulation import FunctionalSimulationResult
from .observation_process import ObservationProcessData, observation_process_data


@dataclass(frozen=True)
class ObservationProcessSimulationTruth:
    """Exact truth for a simulated candidate-sample retention process."""

    process: ObservationProcessData
    missingness_mask: tuple[np.ndarray, ...]
    retention_probability: tuple[np.ndarray, ...] | None
    mechanism: str
    specification: dict[str, Any]
    random_state: int | None
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def n_candidates(self) -> int:
        return int(sum(mask.size for mask in self.missingness_mask))

    @property
    def n_missing(self) -> int:
        return int(sum(np.count_nonzero(mask) for mask in self.missingness_mask))


def _validate_functional_simulation(
    simulation: FunctionalSimulationResult,
) -> FunctionalSimulationResult:
    if not isinstance(simulation, FunctionalSimulationResult):
        raise TypeError("simulation must be a FunctionalSimulationResult")
    truth = simulation.truth
    n_curves = len(truth.pre_missing_observation_times)
    if n_curves < 1:
        raise ValueError("simulation must contain at least one curve")
    if len(truth.observed_pre_missing) != n_curves or len(truth.missingness_mask) != n_curves:
        raise ValueError("functional simulation truth has inconsistent candidate-level lengths")
    return simulation


def _candidate_frame(
    simulation: FunctionalSimulationResult,
    masks: tuple[np.ndarray, ...],
) -> tuple[pd.DataFrame, tuple[str, ...], str | None, tuple[str, ...]]:
    truth = simulation.truth
    n_curves = len(truth.pre_missing_observation_times)
    if len(masks) != n_curves:
        raise ValueError("masks must contain exactly one array per simulated curve")

    metadata = truth.metadata.reset_index(drop=True)
    if len(metadata) != n_curves:
        raise ValueError("functional simulation metadata must contain one row per curve")
    curve_ids = tuple(str(curve_id) for curve_id in simulation.observations.curve_ids)
    if len(curve_ids) != n_curves:
        raise ValueError("functional simulation curve identifiers are inconsistent with truth")

    group_column = "participant_id" if "participant_id" in metadata.columns else None
    design_columns = tuple(
        str(column)
        for column in metadata.columns
        if str(column) != group_column
    )
    coordinate_columns = (
        tuple(map(str, truth.dimension_names))
        if len(truth.dimension_names) == 2
        else ()
    )

    rows: list[dict[str, Any]] = []
    for curve_index, curve_id in enumerate(curve_ids):
        time = np.asarray(truth.pre_missing_observation_times[curve_index], dtype=float)
        values = np.asarray(truth.observed_pre_missing[curve_index], dtype=float)
        mask = np.asarray(masks[curve_index], dtype=bool)
        if mask.shape != (time.size,):
            raise ValueError(f"mask {curve_index} is not aligned to its candidate schedule")
        if values.shape[0] != time.size:
            raise ValueError(f"pre-missing values {curve_index} are not aligned to candidate time")
        metadata_row = metadata.iloc[curve_index]
        for sample_index, candidate_time in enumerate(time):
            row: dict[str, Any] = {
                "curve_id": curve_id,
                "candidate_time": float(candidate_time),
                "observed": int(not mask[sample_index]),
            }
            if group_column is not None:
                row[group_column] = str(metadata_row[group_column])
            for column in design_columns:
                row[column] = metadata_row[column]
            if coordinate_columns:
                for dimension_index, column in enumerate(coordinate_columns):
                    row[column] = (
                        float(values[sample_index, dimension_index])
                        if not mask[sample_index]
                        else np.nan
                    )
            rows.append(row)
    return pd.DataFrame(rows), design_columns, group_column, coordinate_columns


def _build_truth(
    simulation: FunctionalSimulationResult,
    *,
    masks: tuple[np.ndarray, ...],
    retention_probability: tuple[np.ndarray, ...] | None,
    mechanism: str,
    specification: dict[str, Any],
    random_state: int | None,
) -> ObservationProcessSimulationTruth:
    frame, design_columns, group_column, coordinate_columns = _candidate_frame(
        simulation,
        masks,
    )
    process = observation_process_data(
        frame,
        curve_column="curve_id",
        time_column="candidate_time",
        observed_column="observed",
        group_column=group_column,
        candidate_predictors=design_columns,
        predictor_sources={column: "design" for column in design_columns},
        coordinate_columns=coordinate_columns,
        time_unit=simulation.truth.time_unit,
        coordinate_system=simulation.truth.coordinate_system,
        provenance={
            "source": "functional_simulation_truth",
            "observation_process_simulation": True,
            "retention_mechanism": mechanism,
            "retention_specification": dict(specification),
            "retention_random_state": random_state,
        },
    )
    return ObservationProcessSimulationTruth(
        process=process,
        missingness_mask=tuple(np.asarray(mask, dtype=bool).copy() for mask in masks),
        retention_probability=(
            None
            if retention_probability is None
            else tuple(np.asarray(probability, dtype=float).copy() for probability in retention_probability)
        ),
        mechanism=str(mechanism),
        specification=dict(specification),
        random_state=random_state,
        provenance={
            "simulation_only": True,
            "public_correction_estimator": False,
            "candidate_denominator_exact": True,
            "functional_truth_reused": True,
        },
    )


def observation_process_from_functional_simulation(
    simulation: FunctionalSimulationResult,
) -> ObservationProcessSimulationTruth:
    """Convert existing functional-simulation truth to an exact denominator."""

    simulation = _validate_functional_simulation(simulation)
    truth = simulation.truth
    masks = tuple(np.asarray(mask, dtype=bool).copy() for mask in truth.missingness_mask)
    mechanism = str(truth.provenance.get("missingness_kind", "unknown"))
    specification = dict(truth.provenance.get("missingness_specification") or {})

    probabilities: tuple[np.ndarray, ...] | None
    if mechanism == "none":
        probabilities = tuple(np.ones(mask.size, dtype=float) for mask in masks)
    elif mechanism == "mcar":
        probability = float(specification["probability"])
        probabilities = tuple(
            np.full(mask.size, 1.0 - probability, dtype=float) for mask in masks
        )
    elif mechanism == "block":
        probabilities = None
    else:
        raise ValueError(
            "existing functional simulation missingness must be 'none', 'mcar', or 'block'"
        )

    return _build_truth(
        simulation,
        masks=masks,
        retention_probability=probabilities,
        mechanism=mechanism,
        specification=specification,
        random_state=truth.random_state,
    )


def simulate_informative_time_retention(
    simulation: FunctionalSimulationResult,
    *,
    intercept: float = 0.8,
    slope: float = -2.4,
    random_state: int = 166,
) -> ObservationProcessSimulationTruth:
    """Apply a known logistic candidate-time retention process to complete truth.

    The retained probability for candidate time ``t`` is

    ``expit(intercept + slope * z(t))``

    where ``z(t)`` maps the global truth-grid support linearly to ``[-1, 1]``.
    The mechanism is intentionally simulation-only and uses an always-available
    candidate-time predictor rather than contemporaneous missing gaze.
    """

    simulation = _validate_functional_simulation(simulation)
    truth = simulation.truth
    if str(truth.provenance.get("missingness_kind", "unknown")) != "none":
        raise ValueError(
            "informative retention requires a functional simulation generated without prior missingness"
        )
    intercept = float(intercept)
    slope = float(slope)
    if not np.isfinite(intercept) or not np.isfinite(slope):
        raise ValueError("intercept and slope must be finite")
    if not isinstance(random_state, (int, np.integer)) or isinstance(random_state, bool):
        raise TypeError("random_state must be an integer")

    start = float(truth.truth_grid[0])
    end = float(truth.truth_grid[-1])
    if not end > start:
        raise ValueError("functional truth grid must have positive support width")
    rng = np.random.default_rng(int(random_state))
    probabilities: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    for time in truth.pre_missing_observation_times:
        candidate_time = np.asarray(time, dtype=float)
        z = 2.0 * (candidate_time - start) / (end - start) - 1.0
        linear_predictor = np.clip(intercept + slope * z, -35.0, 35.0)
        probability = 1.0 / (1.0 + np.exp(-linear_predictor))
        mask = rng.random(candidate_time.size) >= probability
        probabilities.append(probability)
        masks.append(mask)

    return _build_truth(
        simulation,
        masks=tuple(masks),
        retention_probability=tuple(probabilities),
        mechanism="logistic_candidate_time",
        specification={
            "intercept": intercept,
            "slope": slope,
            "time_transform": "truth_support_to_minus1_plus1",
        },
        random_state=int(random_state),
    )
