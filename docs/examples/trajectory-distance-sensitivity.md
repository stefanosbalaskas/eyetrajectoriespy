# Compare L2, Fréchet, and DTW conclusions

This example asks whether the same small set of trajectories has similar
pairwise ordering and local neighbors under three different distance
contracts.

## Construct trajectories

~~~python
import numpy as np

from eyetrajectoriespy import TrajectorySet

time = np.linspace(0.0, 1.0, 7)
curves = np.array([
    [0.0, 0.1, 0.4, 0.9, 1.5, 2.2, 3.0],
    [0.0, 0.0, 0.1, 0.4, 0.9, 1.5, 2.2],
    [0.0, 0.2, 0.8, 1.4, 1.9, 2.4, 2.8],
    [3.0, 2.4, 1.8, 1.1, 0.6, 0.2, 0.0],
])

values = np.stack([
    np.column_stack([curve, 0.35 * curve**2])
    for curve in curves
])

gaze = TrajectorySet(
    time=time,
    values=values,
    curve_ids=("A", "B", "C", "D"),
    dimension_names=("x", "y"),
    coordinate_system="unknown",
    time_unit="s",
)
~~~

## Declare three distance contracts

~~~python
from eyetrajectoriespy import trajectory_distance_sensitivity

result = trajectory_distance_sensitivity(
    gaze,
    specifications=(
        {"name": "l2", "method": "functional_l2"},
        {"name": "frechet", "method": "discrete_frechet"},
        {
            "name": "dtw_norm",
            "method": "dtw",
            "step_pattern": "symmetric2",
            "normalize": True,
            "window_radius": None,
        },
    ),
    dimensions=("x", "y"),
    dimension_weights=(1.0, 0.5),
    neighbor_k=2,
)
~~~

The same selected dimensions and dimension weights are used in all three
distance contracts.

## Inspect global agreement

~~~python
from eyetrajectoriespy import trajectory_distance_comparison_frame

comparison = trajectory_distance_comparison_frame(result)
print(comparison[
    [
        "specification_a",
        "specification_b",
        "spearman_rank_correlation",
        "mean_absolute_rank_difference",
        "mean_top_k_neighbor_jaccard",
        "nearest_neighbor_identity_agreement_fraction",
    ]
])
~~~

The rank correlation compares all unique curve pairs. It is descriptive and has
no ordinary correlation p-value.

## Inspect local neighbor changes

~~~python
from eyetrajectoriespy import trajectory_distance_neighbor_frame

neighbors = trajectory_distance_neighbor_frame(result)
print(neighbors[
    [
        "specification_a",
        "specification_b",
        "curve_id",
        "neighbors_a",
        "neighbors_b",
        "jaccard",
        "nearest_neighbor_match",
        "cutoff_tie_a",
        "cutoff_tie_b",
    ]
])
~~~

This can show cases where two distance methods have similar global ordering but
still disagree on the nearest comparison trajectory for a particular trial.

## Plot the specification agreement matrix

~~~python
from eyetrajectoriespy import plot_trajectory_distance_rank_correlations

ax = plot_trajectory_distance_rank_correlations(result)
~~~

## Produce reporting text

~~~python
from eyetrajectoriespy import trajectory_distance_sensitivity_reporting_text

print(trajectory_distance_sensitivity_reporting_text(result))
~~~

## Interpretation

The goal is not to choose the metric with the highest agreement. The goal is
to determine whether claims based on "similar trajectories" survive across the
distance definitions that were scientifically defensible before viewing the
result.

The executable counterpart is
`examples/trajectory_distance_sensitivity.py`.
