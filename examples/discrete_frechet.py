"""Discrete Fréchet distance for ordered gaze trajectories."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    discrete_frechet_distance,
    pairwise_discrete_frechet_distances,
)

path_a = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
path_b = np.array([[0.0, 0.0], [2.0, 0.0]])

audit = discrete_frechet_distance(
    path_a,
    path_b,
    return_coupling=True,
)
print("distance:", audit.distance)
print("coupling:", audit.coupling.tolist())
print("local distances:", audit.local_distances.tolist())

time = np.array([0.0, 0.5, 1.0])
values = np.array(
    [
        [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
        [[0.0, 0.0], [1.0, 0.5], [2.0, 0.0]],
        [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
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
print(pairwise_discrete_frechet_distances(gaze, dimensions=("x", "y")))
