# Discrete Fréchet trajectory comparison

## Unequal sampling density

~~~python
import numpy as np
from eyetrajectoriespy import discrete_frechet_distance

path_a = np.array([
    [0.0, 0.0],
    [1.0, 0.0],
    [2.0, 0.0],
])
path_b = np.array([
    [0.0, 0.0],
    [2.0, 0.0],
])

result = discrete_frechet_distance(
    path_a,
    path_b,
    return_coupling=True,
)

print(result.distance)
print(result.coupling)
print(result.local_distances)
~~~

The distance is 1.0 because the intermediate point of path_a must be coupled to one endpoint of path_b.

## Outlier sensitivity

~~~python
path_c = np.array([
    [0.0, 0.0],
    [1.0, 5.0],
    [2.0, 0.0],
])

print(discrete_frechet_distance(path_a, path_c))
~~~

The central deviation drives the bottleneck distance to 5.0.

## Pairwise gaze comparison

~~~python
from eyetrajectoriespy import (
    TrajectorySet,
    pairwise_discrete_frechet_distances,
)

time = np.array([0.0, 0.5, 1.0])
values = np.array([
    [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
    [[0.0, 0.0], [1.0, 0.5], [2.0, 0.0]],
    [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]],
])

gaze = TrajectorySet(
    time=time,
    values=values,
    curve_ids=("A", "B", "C"),
    dimension_names=("x", "y"),
    coordinate_system="degrees",
    time_unit="s",
)

matrix = pairwise_discrete_frechet_distances(
    gaze,
    dimensions=("x", "y"),
)
print(matrix)
~~~

The TrajectorySet time grid indexes point order but is not passed into the Fréchet recurrence. Use a time-preserving method when latency or traversal timing is part of the estimand.

The executable counterpart is examples/discrete_frechet.py.
