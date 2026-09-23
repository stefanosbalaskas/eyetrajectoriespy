# Discrete Fréchet distance

This example shows why discrete Fréchet and common-time functional \(L_2\) answer different questions.

## 1. Same ordered path, different sampling density

~~~python
import numpy as np
from eyetrajectoriespy import discrete_frechet_distance

a = np.array(
    [
        [0.0, 0.0],
        [1.0, 0.0],
        [2.0, 0.0],
    ]
)

b = np.array(
    [
        [0.0, 0.0],
        [0.0, 0.0],
        [1.0, 0.0],
        [2.0, 0.0],
    ]
)

print(discrete_frechet_distance(a, b))
~~~

The result is zero because both sampled sequences can be coupled monotonically along the same ordered locations.

This does **not** mean the trajectories have identical timing. The low-level Fréchet API has no time argument.

## 2. Order matters

~~~python
reversed_path = a[::-1].copy()

print(discrete_frechet_distance(a, reversed_path))
~~~

The distance is non-zero because the traversal order is reversed.

Discrete Fréchet permits monotone differences in progression; it does not permit backtracking through the other path's sample order.

## 3. Explicit dimension weighting

~~~python
weighted = discrete_frechet_distance(
    a,
    b,
    dimension_weights=(1.0, 2.0),
)
~~~

Weights alter the point metric and therefore the path distance. They are never estimated or standardized automatically.

## 4. Pairwise distances for a TrajectorySet

~~~python
from eyetrajectoriespy import (
    pairwise_discrete_frechet_distances,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=4,
    trials_per_participant=2,
    n_time=61,
    random_state=32,
)

distances = pairwise_discrete_frechet_distances(
    gaze,
    dimensions=("x", "y"),
)

print(distances.shape)
print(distances[:3, :3])
~~~

The returned matrix is symmetric with a zero diagonal.

## 5. Contrast with common-time L2

~~~python
from eyetrajectoriespy import pairwise_functional_distances

l2 = pairwise_functional_distances(gaze)

print("Fréchet:", distances[0, 1])
print("L2:", l2[0, 1])
~~~

The numbers need not agree because the estimands differ:

- \(L_2\) compares the two functions at shared trial time;
- discrete Fréchet compares the ordered sampled routes under a monotone coupling.

Neither should be selected after outcome inspection simply because it produces a more convenient group difference.

## Scope boundary

Version 0.32 returns the distance only. It does not expose a coupling path, continuous Fréchet solver, DTW cost/path, automatic simplification, or automatic downsampling.
