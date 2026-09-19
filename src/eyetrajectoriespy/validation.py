"""Validation and scientific-contract helpers."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from .types import TrajectorySet


_ALLOWED_COORDINATE_SYSTEMS = {
    "pixels",
    "normalized",
    "degrees",
    "landmark_relative",
    "probability_simplex",
    "simplex_logratio",
    "phase_time",
    "unknown",
}


def validate_trajectory_set(
    trajectories: TrajectorySet,
    *,
    require_complete: bool = False,
    require_dimensions: Iterable[str] | None = None,
) -> TrajectorySet:
    """Validate scientific assumptions that are not enforced by construction.

    This function never repairs data. It either returns the input object or
    raises a descriptive error.
    """

    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("trajectories must be a TrajectorySet")
    if trajectories.coordinate_system not in _ALLOWED_COORDINATE_SYSTEMS:
        raise ValueError(
            "coordinate_system must be one of " + ", ".join(sorted(_ALLOWED_COORDINATE_SYSTEMS))
        )
    if require_complete and np.isnan(trajectories.values).any():
        raise ValueError("TrajectorySet contains missing values; explicit handling is required")
    if require_dimensions is not None:
        missing = set(require_dimensions) - set(trajectories.dimension_names)
        if missing:
            raise ValueError(f"Missing required dimensions: {sorted(missing)}")
    return trajectories


def validate_common_grid(trajectories: TrajectorySet) -> None:
    """Confirm a finite, strictly increasing common grid."""

    time = trajectories.time
    if time.ndim != 1 or not np.all(np.isfinite(time)) or not np.all(np.diff(time) > 0):
        raise ValueError("A finite, strictly increasing common grid is required")


def validate_simplex(values: np.ndarray, *, atol: float = 1e-7) -> None:
    """Validate non-negative functions that sum to one across dimensions."""

    arr = np.asarray(values, dtype=float)
    if arr.ndim != 3:
        raise ValueError("simplex values must have shape (n_curves, n_time, n_dimensions)")
    if np.isnan(arr).any():
        raise ValueError("simplex values cannot contain missing values")
    if np.any(arr < -atol):
        raise ValueError("simplex values must be non-negative")
    totals = arr.sum(axis=2)
    if not np.allclose(totals, 1.0, atol=atol):
        raise ValueError("simplex values must sum to one across dimensions at every time point")


def validate_no_long_missing_runs(
    trajectories: TrajectorySet,
    *,
    max_missing_fraction: float,
) -> None:
    """Fail when a trajectory exceeds an explicit missingness tolerance."""

    if not 0 <= max_missing_fraction < 1:
        raise ValueError("max_missing_fraction must be in [0, 1)")
    missing = np.isnan(trajectories.values).any(axis=2).mean(axis=1)
    bad = np.flatnonzero(missing > max_missing_fraction)
    if bad.size:
        ids = [trajectories.curve_ids[i] for i in bad]
        raise ValueError(
            f"{len(ids)} trajectories exceed max_missing_fraction={max_missing_fraction}: {ids[:5]}"
        )
