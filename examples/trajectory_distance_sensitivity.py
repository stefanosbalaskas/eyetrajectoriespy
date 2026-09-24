"""Trajectory-distance specification sensitivity example."""

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    plot_trajectory_distance_rank_correlations,
    trajectory_distance_comparison_frame,
    trajectory_distance_neighbor_frame,
    trajectory_distance_sensitivity,
    trajectory_distance_sensitivity_reporting_text,
)


time = np.linspace(0.0, 1.0, 7)
curves = np.array(
    [
        [0.0, 0.1, 0.4, 0.9, 1.5, 2.2, 3.0],
        [0.0, 0.0, 0.1, 0.4, 0.9, 1.5, 2.2],
        [0.0, 0.2, 0.8, 1.4, 1.9, 2.4, 2.8],
        [3.0, 2.4, 1.8, 1.1, 0.6, 0.2, 0.0],
    ],
    dtype=float,
)
values = np.stack(
    [
        np.column_stack([curve, 0.35 * curve**2])
        for curve in curves
    ]
)

gaze = TrajectorySet(
    time=time,
    values=values,
    curve_ids=("A", "B", "C", "D"),
    dimension_names=("x", "y"),
    coordinate_system="unknown",
    time_unit="s",
)

result = trajectory_distance_sensitivity(
    gaze,
    specifications=(
        {"name": "l2", "method": "functional_l2"},
        {"name": "frechet", "method": "discrete_frechet"},
        {
            "name": "dtw_norm",
            "method": "dtw",
            "step_pattern": "symmetric2",
            "normalize": True,
            "window_radius": None,
        },
    ),
    dimensions=("x", "y"),
    dimension_weights=(1.0, 0.5),
    neighbor_k=2,
)

comparison = trajectory_distance_comparison_frame(result)
neighbors = trajectory_distance_neighbor_frame(result)

assert result.distance_matrices.shape == (3, 4, 4)
assert comparison.shape[0] == 3
assert neighbors.shape[0] == 12

ax = plot_trajectory_distance_rank_correlations(result)
plt.close(ax.figure)

print(trajectory_distance_sensitivity_reporting_text(result))
print(comparison.to_string(index=False))
