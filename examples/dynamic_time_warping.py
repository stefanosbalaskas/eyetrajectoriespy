"""Raw cumulative DTW cost for ordered gaze trajectories."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    discrete_frechet_distance,
    dynamic_time_warping_cost,
    pairwise_dynamic_time_warping_costs,
)

a = np.array([[0.0], [1.0], [2.0]])
b = np.array([[0.0], [2.0]])
audit = dynamic_time_warping_cost(a, b, return_path=True)

print("DTW cost:", audit.cost)
print("warping path:", audit.warping_path.tolist())
print("local distances:", audit.local_distances.tolist())

parallel_a = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
parallel_b = np.array([[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])
print("Fréchet:", discrete_frechet_distance(parallel_a, parallel_b))
print("DTW:", dynamic_time_warping_cost(parallel_a, parallel_b))

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
print(pairwise_dynamic_time_warping_costs(gaze, dimensions=("x", "y")))
