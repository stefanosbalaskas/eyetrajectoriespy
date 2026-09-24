# Dynamic time warping trajectory comparison

This example contrasts the backward-compatible symmetric1 raw-cost contract with the normalizable symmetric2 variant.

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

legacy = dynamic_time_warping_distance(
    a,
    b,
    step_pattern="symmetric1",
    return_path=True,
)

normalizable = dynamic_time_warping_distance(
    a,
    b,
    step_pattern="symmetric2",
    normalize=True,
    return_path=True,
)

print(legacy.raw_distance)
print(normalizable.raw_distance)
print(normalizable.normalized_distance)
~~~

Both alignments can remove this one-sample shift. That can be useful when local progression rate is nuisance variation and problematic when the shift is the psychological effect itself.

## Inspect the weighted path audit

~~~python
print(normalizable.path)
print(normalizable.local_distances)
print(normalizable.step_weights)
print(normalizable.weighted_local_costs)

assert np.isclose(
    normalizable.raw_distance,
    normalizable.weighted_local_costs.sum(),
)
~~~

For symmetric2, diagonal advances receive weight two and horizontal/vertical advances weight one. The initial matched pair also has weight two. The normalized distance divides the raw cumulative cost by n_a + n_b.

## Constrain the index warp

~~~python
diagonal_only = dynamic_time_warping_distance(
    a,
    b,
    step_pattern="symmetric2",
    normalize=True,
    window_radius=0,
)

print(diagonal_only)
~~~

A zero-radius band forces same-index alignment. Window radius is therefore part of the estimand and should not be tuned after inspecting group differences.

## Plot the alignment

~~~python
from eyetrajectoriespy import plot_dynamic_time_warping_alignment

ax = plot_dynamic_time_warping_alignment(normalizable)
~~~

The same-index diagonal is shown as a reference. Departures from it make the amount and location of index warping visible.

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
    step_pattern="symmetric2",
    normalize=True,
    window_radius=1,
)

print(matrix)
~~~

The TrajectorySet time grid describes the source representation, but numeric timestamps are not used by DTW.

## Manuscript-oriented text

~~~python
from eyetrajectoriespy import dynamic_time_warping_reporting_text

print(dynamic_time_warping_reporting_text(normalizable))
~~~

Report the step pattern, normalization rule, window, coordinate representation, dimensions/units, sequence lengths, upstream preprocessing, and whether latency was analyzed separately.

The executable counterpart is examples/dynamic_time_warping.py.
