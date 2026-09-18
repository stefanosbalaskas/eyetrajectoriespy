"""Derived continuous functions from planar gaze trajectories."""

from __future__ import annotations

import numpy as np

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
