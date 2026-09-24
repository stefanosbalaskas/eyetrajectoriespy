# Dynamic time warping trajectory comparison

This example shows why an elastic index alignment can be useful and why it can also remove a timing difference that matters scientifically.

## A one-sample shift

~~~python
import numpy as np
from eyetrajectoriespy import dynamic_time_warping_distance

a = np.array([
    [0.0],
    [0.0],
    [1.0],
])

b = np.array([
    [0.0],
    [1.0],
    [1.0],
])

audit = dynamic_time_warping_distance(
    a,
    b,
    return_path=True,
)

print(audit.distance)
print(audit.path)
~~~

Unconstrained DTW can align the repeated zeros and repeated ones so the cumulative cost is 0.0. This is exactly why DTW can be useful when local timing differences are nuisance variation.

It is also exactly why DTW should not be the only analysis when the onset shift is itself the psychological effect.

## Constrain the index warp

~~~python
diagonal_only = dynamic_time_warping_distance(
    a,
    b,
    window_radius=0,
)

print(diagonal_only)
~~~

A zero-radius band forces same-index matching. The distance is then 1.0.

The comparison demonstrates that window_radius is part of the estimand. Do not choose it after looking for the most favorable group separation.

## Auditable cumulative cost

~~~python
print(audit.local_distances)
print(audit.path_length)
print(audit.mean_local_distance)
print(audit.provenance)
~~~

The public distance is the **sum** of local costs on the selected path. mean_local_distance is retained as an audit summary, but the package does not substitute it for the defined DTW distance.

## Pairwise planar gaze trajectories

~~~python
from eyetrajectoriespy import (
    TrajectorySet,
    pairwise_dynamic_time_warping_distances,
)

time = np.array([0.0, 0.5, 1.0])
values = np.array([
    [[0.0, 0.0], [0.0, 0.0], [1.0, 0.0]],
    [[0.0, 0.0], [1.0, 0.0], [1.0, 0.0]],
    [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]],
])

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

print(matrix)
~~~

The stored time grid establishes the source trajectory object, but the DTW recurrence itself uses sequence indices, not the numeric time values.

## What to report

For this workflow report:

- the coordinate representation and units;
- the selected dimensions and any explicit dimension weights;
- each sequence length;
- the symmetric diagonal/up/left step pattern;
- the Sakoe-Chiba sample-index radius or that alignment was unconstrained;
- that the public distance is an unnormalized cumulative local-cost sum;
- all upstream interpolation, resampling, smoothing, or normalization;
- whether a time-preserving sensitivity analysis was also used.

The executable counterpart is examples/dynamic_time_warping.py.
