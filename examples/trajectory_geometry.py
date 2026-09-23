"""Continuous heading, curvature, turning rate, and tortuosity."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    heading_function,
    signed_curvature_function,
    trajectory_tortuosity,
    turning_rate_function,
)


time = np.linspace(0.0, np.pi / 2.0, 401)
radius = 5.0
values = np.column_stack(
    [
        radius * np.cos(time),
        radius * np.sin(time),
    ]
)[None, :, :]

gaze = TrajectorySet(
    time=time,
    values=values,
    curve_ids=("quarter-circle",),
    dimension_names=("x", "y"),
    time_unit="s",
    coordinate_system="degrees",
)

heading = heading_function(gaze, min_speed=0.0)
curvature = signed_curvature_function(gaze, min_speed=0.0)
turning = turning_rate_function(gaze, min_speed=0.0)
tortuosity = trajectory_tortuosity(gaze)

interior = slice(5, -5)
print("heading range:", np.nanmin(heading.values), np.nanmax(heading.values))
print(
    "mean interior curvature:",
    np.nanmean(curvature.values[0, interior, 0]),
)
print(
    "mean interior turning rate:",
    np.nanmean(turning.values[0, interior, 0]),
)
print(tortuosity)
