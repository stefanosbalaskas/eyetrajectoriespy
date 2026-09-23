# Dynamic time warping trajectory comparison

## A simple unequal-length example

~~~python
import numpy as np
from eyetrajectoriespy import dynamic_time_warping_cost

a = np.array([[0.0], [1.0], [2.0]])
b = np.array([[0.0], [2.0]])

result = dynamic_time_warping_cost(
    a,
    b,
    return_path=True,
)

print(result.cost)
print(result.warping_path)
print(result.local_distances)
~~~

The raw cumulative cost is 1.0.

## DTW and Fréchet are different

~~~python
from eyetrajectoriespy import discrete_frechet_distance

a = np.array([
    [0.0, 0.0],
    [1.0, 0.0],
    [2.0, 0.0],
])
b = np.array([
    [0.0, 1.0],
    [1.0, 1.0],
    [2.0, 1.0],
])

print(discrete_frechet_distance(a, b))
print(dynamic_time_warping_cost(a, b))
~~~

Fréchet reports 1.0 because its estimand is the maximum separation along the optimal coupling.

DTW reports 3.0 because it sums the three unit local deviations.

## Pairwise gaze costs

~~~python
from eyetrajectoriespy import (
    TrajectorySet,
    pairwise_dynamic_time_warping_costs,
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

print(
    pairwise_dynamic_time_warping_costs(
        gaze,
        dimensions=("x", "y"),
    )
)
~~~

The TrajectorySet time values index the observations but are not used by the DTW recurrence.

The executable counterpart is examples/dynamic_time_warping.py.
