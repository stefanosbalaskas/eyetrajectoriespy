"""Dynamic time warping for ordered gaze trajectories."""

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    dynamic_time_warping_distance,
    dynamic_time_warping_reporting_text,
    pairwise_dynamic_time_warping_distances,
    plot_dynamic_time_warping_alignment,
)


a = np.array([[0.0], [0.0], [1.0]])
b = np.array([[0.0], [1.0], [1.0]])

legacy = dynamic_time_warping_distance(
    a,
    b,
    step_pattern="symmetric1",
    return_path=True,
)
assert legacy.distance == 0.0
assert legacy.raw_distance == 0.0
assert legacy.normalized_distance is None

audit = dynamic_time_warping_distance(
    a,
    b,
    step_pattern="symmetric2",
    normalize=True,
    return_path=True,
)
assert audit.distance == audit.normalized_distance
assert np.isclose(audit.raw_distance, audit.weighted_local_costs.sum())
assert audit.provenance["recorded_time_used"] is False
assert dynamic_time_warping_distance(
    a,
    b,
    step_pattern="symmetric2",
    normalize=True,
    window_radius=0,
) > audit.distance

ax = plot_dynamic_time_warping_alignment(audit)
plt.close(ax.figure)

time = np.array([0.0, 0.5, 1.0])
values = np.array(
    [
        [[0.0, 0.0], [0.0, 0.0], [1.0, 0.0]],
        [[0.0, 0.0], [1.0, 0.0], [1.0, 0.0]],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]],
    ]
)
gaze = TrajectorySet(
    time=time,
    values=values,
    curve_ids=("A", "B", "C"),
    dimension_names=("x", "y"),
    coordinate_system="degrees",
    time_unit="s",
)

matrix = pairwise_dynamic_time_warping_distances(
    gaze,
    dimensions=("x", "y"),
    step_pattern="symmetric2",
    normalize=True,
    window_radius=1,
)
assert matrix.shape == (3, 3)
assert np.allclose(matrix, matrix.T)

print(dynamic_time_warping_reporting_text(audit))
print("DTW path:", audit.path.tolist())
print("Pairwise normalized symmetric2 DTW matrix:\n", matrix)
