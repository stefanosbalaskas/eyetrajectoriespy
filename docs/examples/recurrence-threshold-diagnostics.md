# Recurrence-threshold diagnostics

This example makes the radius-to-recurrence relationship visible before a recurrence threshold is interpreted.

## Synthetic planar trajectory

~~~python
import numpy as np
from eyetrajectoriespy import TrajectorySet

time = np.arange(240, dtype=float) * 0.01
x = np.sin(2 * np.pi * 1.2 * time)
y = 0.7 * np.cos(2 * np.pi * 0.8 * time + 0.3)

gaze = TrajectorySet(
    time=time,
    values=np.column_stack([x, y])[None, :, :],
    curve_ids=("synthetic",),
    dimension_names=("x", "y"),
    time_unit="s",
    coordinate_system="normalized",
)
~~~

## 1. Evaluate a declared radius grid

~~~python
from eyetrajectoriespy import recurrence_radius_profile

profile = recurrence_radius_profile(
    gaze,
    curve="synthetic",
    dimensions=("x", "y"),
    radii=(0.02, 0.04, 0.06, 0.08, 0.12, 0.20),
    metric="euclidean",
    theiler_window=0.05,
    theiler_window_units="seconds",
)
~~~

Inspect both cumulative recurrence and the pair-distance mass entering at each step:

~~~python
print(
    profile.table[
        [
            "previous_radius",
            "radius",
            "shell_pair_count",
            "shell_pair_fraction",
            "cumulative_recurrent_pairs",
            "recurrence_rate",
        ]
    ]
)
~~~

The recurrence-rate column is the empirical pair-distance CDF at the declared radii.

## 2. Plot the curve

~~~python
from eyetrajectoriespy import plot_recurrence_rate_curve

ax = plot_recurrence_rate_curve(profile)
~~~

A steep section means a small change in radius admits many additional state pairs. That is a sensitivity warning, not a prescription to avoid or prefer the region.

## 3. Confirm the base recurrence estimator

Suppose 0.08 was independently justified as the primary radius.

~~~python
from eyetrajectoriespy import recurrence_matrix

recurrence = recurrence_matrix(
    gaze,
    curve="synthetic",
    dimensions=("x", "y"),
    radius=0.08,
    metric="euclidean",
    theiler_window=0.05,
    theiler_window_units="seconds",
)

row = profile.table.loc[profile.table["radius"] == 0.08].iloc[0]

print(row["recurrence_rate"])
print(recurrence.achieved_recurrence_rate)
~~~

Those values use the same denominator and threshold convention and agree exactly.

## 4. Inspect profile coverage

~~~python
print(profile.provenance["maximum_radius_coverage_fraction"])
print(profile.provenance["full_distance_distribution_captured"])
~~~

If the maximum radius covers only part of the empirical distance distribution, do not describe the shell table as a histogram of all pairwise distances.

## 5. Target-RR analysis remains explicit

If the scientific protocol instead controls recurrence density:

~~~python
targeted = recurrence_matrix(
    gaze,
    curve="synthetic",
    dimensions=("x", "y"),
    target_recurrence_rate=0.05,
    metric="euclidean",
    theiler_window=0.05,
    theiler_window_units="seconds",
)

print(targeted.target_recurrence_rate)
print(targeted.radius)
print(targeted.achieved_recurrence_rate)
~~~

Here the radius is solved to implement the target-RR policy. The resulting RR is controlled by design and should not be treated as an unconstrained outcome.

## Reporting

~~~python
from eyetrajectoriespy import recurrence_radius_profile_reporting_text

print(recurrence_radius_profile_reporting_text(profile))
~~~

The executable counterpart is examples/recurrence_threshold_diagnostics.py.
