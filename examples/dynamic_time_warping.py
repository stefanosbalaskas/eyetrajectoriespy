"""Dynamic time warping for ordered gaze trajectories."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    dynamic_time_warping_distance,
    pairwise_dynamic_time_warping_distances,
)


a = np.array([[0.0], [0.0], [1.0]])
b = np.array([[0.0], [1.0], [1.0]])

audit = dynamic_time_warping_distance(a, b, return_path=True)
assert audit.distance == 0.0
assert audit.provenance["recorded_time_used"] is False
assert dynamic_time_warping_distance(a, b, window_radius=0) == 1.0

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
    window_radius=1,
)
assert matrix.shape == (3, 3)
assert np.allclose(matrix, matrix.T)

print("DTW distance:", audit.distance)
print("DTW path:", audit.path.tolist())
print("Pairwise DTW matrix:\n", matrix)
