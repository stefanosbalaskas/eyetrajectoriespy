"""Compare sampled gaze trajectories with discrete Frechet distance."""

import numpy as np

from eyetrajectoriespy import (
    discrete_frechet_distance,
    pairwise_discrete_frechet_distances,
    pairwise_functional_distances,
    simulate_planar_trajectories,
)


a = np.asarray([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
b = np.asarray([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
print("same ordered route, different sampling density:", discrete_frechet_distance(a, b))

gaze = simulate_planar_trajectories(
    n_participants=4,
    trials_per_participant=2,
    n_time=61,
    random_state=32,
)
frechet = pairwise_discrete_frechet_distances(
    gaze,
    dimensions=("x", "y"),
)
l2 = pairwise_functional_distances(gaze)

print("pairwise Frechet shape:", frechet.shape)
print("curve 0 vs 1 Frechet:", frechet[0, 1])
print("curve 0 vs 1 common-time L2:", l2[0, 1])
