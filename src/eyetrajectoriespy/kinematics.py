"""Derived continuous functions from planar gaze trajectories."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .types import TrajectorySet
from .validation import validate_trajectory_set


def differentiate_trajectories(
    trajectories: TrajectorySet,
    *,
    order: int = 1,
) -> TrajectorySet:
    """Differentiate functional trajectories numerically with respect to time.

    No smoothing is applied. Derivatives can amplify measurement noise, so
    preprocessing decisions should be made and reported explicitly upstream.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if order not in {1, 2}:
        raise ValueError("order must be 1 or 2")
    values = trajectories.values.copy()
    for _ in range(order):
        values = np.gradient(values, trajectories.time, axis=1, edge_order=2)
    suffix = "velocity" if order == 1 else "acceleration"
    names = tuple(f"{name}_{suffix}" for name in trajectories.dimension_names)
    return TrajectorySet(
        time=trajectories.time,
        values=values,
        curve_ids=trajectories.curve_ids,
        dimension_names=names,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "derivative": {"order": order, "method": "numpy_gradient", "smoothing": False},
        },
    )


def speed_function(trajectories: TrajectorySet) -> TrajectorySet:
    """Compute the Euclidean speed function of a planar gaze path."""

    if trajectories.n_dimensions < 2:
        raise ValueError("Planar x/y dimensions are required")
    velocity = differentiate_trajectories(trajectories, order=1)
    speed = np.linalg.norm(velocity.values[:, :, :2], axis=2, keepdims=True)
    return TrajectorySet(
        time=trajectories.time,
        values=speed,
        curve_ids=trajectories.curve_ids,
        dimension_names=("speed",),
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={**dict(velocity.provenance), "derived_function": "speed"},
    )


def acceleration_magnitude_function(trajectories: TrajectorySet) -> TrajectorySet:
    """Compute Euclidean acceleration magnitude for planar trajectories."""

    acceleration = differentiate_trajectories(trajectories, order=2)
    magnitude = np.linalg.norm(acceleration.values[:, :, :2], axis=2, keepdims=True)
    return TrajectorySet(
        time=trajectories.time,
        values=magnitude,
        curve_ids=trajectories.curve_ids,
        dimension_names=("acceleration_magnitude",),
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={**dict(acceleration.provenance), "derived_function": "acceleration_magnitude"},
    )


def distance_to_landmark_function(
    trajectories: TrajectorySet,
    *,
    landmark_x: float | np.ndarray,
    landmark_y: float | np.ndarray,
) -> TrajectorySet:
    """Compute continuous Euclidean distance from gaze to a spatial landmark."""

    validate_trajectory_set(trajectories)
    if trajectories.n_dimensions < 2:
        raise ValueError("Planar x/y dimensions are required")
    lx = np.asarray(landmark_x, dtype=float)
    ly = np.asarray(landmark_y, dtype=float)
    if lx.ndim == 0:
        lx = np.repeat(lx, trajectories.n_curves)
    if ly.ndim == 0:
        ly = np.repeat(ly, trajectories.n_curves)
    if lx.shape != (trajectories.n_curves,) or ly.shape != (trajectories.n_curves,):
        raise ValueError("landmark coordinates must be scalars or one value per trajectory")
    dx = trajectories.values[:, :, 0] - lx[:, None]
    dy = trajectories.values[:, :, 1] - ly[:, None]
    distance = np.sqrt(dx**2 + dy**2)[:, :, None]
    return TrajectorySet(
        time=trajectories.time,
        values=distance,
        curve_ids=trajectories.curve_ids,
        dimension_names=("distance_to_landmark",),
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "derived_function": "distance_to_landmark",
        },
    )


def cumulative_path_length(trajectories: TrajectorySet) -> TrajectorySet:
    """Compute cumulative 2-D path length as a function of trial time."""

    validate_trajectory_set(trajectories, require_complete=True)
    if trajectories.n_dimensions < 2:
        raise ValueError("Planar x/y dimensions are required")
    delta = np.diff(trajectories.values[:, :, :2], axis=1)
    steps = np.linalg.norm(delta, axis=2)
    cumulative = np.concatenate(
        [np.zeros((trajectories.n_curves, 1)), np.cumsum(steps, axis=1)], axis=1
    )[:, :, None]
    return TrajectorySet(
        time=trajectories.time,
        values=cumulative,
        curve_ids=trajectories.curve_ids,
        dimension_names=("cumulative_path_length",),
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={**dict(trajectories.provenance), "derived_function": "cumulative_path_length"},
    )


def _resolve_planar_dimensions(
    trajectories: TrajectorySet,
    dimensions: Sequence[str] | None,
) -> tuple[tuple[str, str], tuple[int, int]]:
    """Resolve exactly two declared planar dimensions without silent guessing."""

    validate_trajectory_set(trajectories, require_complete=True)
    if dimensions is None:
        names = ("x", "y")
        missing = [name for name in names if name not in trajectories.dimension_names]
        if missing:
            raise ValueError(
                "dimensions must be supplied explicitly when TrajectorySet does "
                "not contain named 'x' and 'y' dimensions"
            )
    else:
        if isinstance(dimensions, (str, bytes)):
            raise TypeError("dimensions must be a non-string sequence of two names")
        raw = tuple(dimensions)
        if len(raw) != 2:
            raise ValueError("dimensions must contain exactly two planar dimensions")
        if not all(isinstance(name, str) for name in raw):
            raise TypeError("dimension names must be strings")
        names = (raw[0], raw[1])
        if names[0] == names[1]:
            raise ValueError("planar dimensions must be distinct")
        missing = [name for name in names if name not in trajectories.dimension_names]
        if missing:
            raise KeyError(f"Unknown trajectory dimensions: {missing}")

    if trajectories.n_time < 3:
        raise ValueError(
            "planar differential geometry requires at least three time samples "
            "for second-order edge-aware numerical derivatives"
        )
    indices = (
        trajectories.dimension_names.index(names[0]),
        trajectories.dimension_names.index(names[1]),
    )
    return names, indices


def _nonnegative_finite_threshold(value: float, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise TypeError(f"{name} must be numeric and not boolean")
    numeric = float(value)
    if not np.isfinite(numeric) or numeric < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return numeric


def _validate_undefined_policy(undefined_policy: str) -> str:
    if undefined_policy not in {"nan", "raise"}:
        raise ValueError("undefined_policy must be 'nan' or 'raise'")
    return undefined_policy


def _planar_derivatives(
    trajectories: TrajectorySet,
    *,
    dimensions: Sequence[str] | None,
) -> tuple[tuple[str, str], np.ndarray, np.ndarray, np.ndarray]:
    names, indices = _resolve_planar_dimensions(trajectories, dimensions)
    planar = trajectories.values[:, :, indices]
    velocity = np.gradient(
        planar,
        trajectories.time,
        axis=1,
        edge_order=2,
    )
    acceleration = np.gradient(
        velocity,
        trajectories.time,
        axis=1,
        edge_order=2,
    )
    speed = np.linalg.norm(velocity, axis=2)
    return names, velocity, acceleration, speed


def _apply_low_speed_contract(
    values: np.ndarray,
    *,
    speed: np.ndarray,
    min_speed: float,
    undefined_policy: str,
    curve_ids: tuple[str, ...],
    quantity: str,
) -> tuple[np.ndarray, np.ndarray]:
    threshold = _nonnegative_finite_threshold(min_speed, name="min_speed")
    policy = _validate_undefined_policy(undefined_policy)
    undefined = speed <= threshold
    if np.any(undefined) and policy == "raise":
        counts = np.sum(undefined, axis=1)
        affected = [
            f"{curve_ids[index]}:{int(count)}"
            for index, count in enumerate(counts)
            if count > 0
        ]
        raise ValueError(
            f"{quantity} is undefined where speed <= min_speed={threshold}; "
            f"affected curve/sample counts: {affected[:8]}"
        )
    out = np.asarray(values, dtype=float).copy()
    out[undefined] = np.nan
    return out, undefined


def _geometry_result(
    trajectories: TrajectorySet,
    *,
    values: np.ndarray,
    dimension_name: str,
    planar_dimensions: tuple[str, str],
    min_speed: float,
    undefined_policy: str,
    undefined_mask: np.ndarray,
    value_unit: str,
    extra_provenance: dict[str, object] | None = None,
) -> TrajectorySet:
    counts = np.sum(undefined_mask, axis=1).astype(int)
    return TrajectorySet(
        time=trajectories.time,
        values=np.asarray(values, dtype=float)[:, :, None],
        curve_ids=trajectories.curve_ids,
        dimension_names=(dimension_name,),
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system="unknown",
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "derived_function": dimension_name,
            "source_coordinate_system": trajectories.coordinate_system,
            "planar_dimensions": planar_dimensions,
            "derivative_method": "numpy_gradient",
            "smoothing": False,
            "min_speed": float(min_speed),
            "low_speed_rule": "speed <= min_speed",
            "undefined_policy": undefined_policy,
            "undefined_sample_counts": counts.tolist(),
            "undefined_sample_fractions": (
                counts.astype(float) / trajectories.n_time
            ).tolist(),
            "value_unit": value_unit,
            **(extra_provenance or {}),
        },
    )
