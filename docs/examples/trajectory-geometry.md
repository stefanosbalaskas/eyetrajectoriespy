# Continuous trajectory geometry

This worked example uses a quarter circle so the expected geometry is known analytically.

## Build a quarter-circle trajectory

For \(R=5\) degrees of visual angle,

\[
x(t)=R\cos t,\qquad y(t)=R\sin t,\qquad 0\le t\le \pi/2.
\]

~~~python
import numpy as np
from eyetrajectoriespy import TrajectorySet

time = np.linspace(0.0, np.pi / 2.0, 401)
radius = 5.0
values = np.column_stack(
    [radius * np.cos(time), radius * np.sin(time)]
)[None, :, :]

gaze = TrajectorySet(
    time=time,
    values=values,
    curve_ids=("quarter-circle",),
    dimension_names=("x", "y"),
    time_unit="s",
    coordinate_system="degrees",
)
~~~

## Compute continuous geometry

~~~python
from eyetrajectoriespy import (
    heading_function,
    signed_curvature_function,
    turning_rate_function,
)

heading = heading_function(gaze, min_speed=0.0)
curvature = signed_curvature_function(gaze, min_speed=0.0)
turning = turning_rate_function(gaze, min_speed=0.0)
~~~

For this path,

\[
\kappa(t)=1/R=0.2\ \text{degree}^{-1},
\]

while

\[
\omega(t)=1\ \text{rad/s}
\]

because the time parameter is also the angular phase.

~~~python
interior = slice(5, -5)

print(np.nanmean(curvature.values[0, interior, 0]))
print(np.nanmean(turning.values[0, interior, 0]))
~~~

Small edge deviations are expected from numerical differentiation.

## Tortuosity

~~~python
from eyetrajectoriespy import trajectory_tortuosity

summary = trajectory_tortuosity(gaze)
print(summary)
~~~

For the continuous quarter circle,

\[
T
=
\frac{R\pi/2}{R\sqrt 2}
=
\frac{\pi}{2\sqrt 2}
\approx 1.111.
\]

The implementation uses the observed polyline path length, so the numerical value approaches this limit as the grid becomes dense.

## Plot curvature as a function

~~~python
from eyetrajectoriespy import plot_trajectory_overlay

ax = plot_trajectory_overlay(
    curvature,
    dimension="signed_curvature",
)
ax.figure.savefig("signed-curvature.svg")
~~~

The curvature result is a native `TrajectorySet` and can enter compatible functional workflows if its missing-value contract is satisfied.

## Low-speed handling

~~~python
curvature = signed_curvature_function(
    gaze,
    min_speed=0.05,
    undefined_policy="nan",
)

print(curvature.provenance["undefined_sample_counts"])
~~~

Undefined samples stay `NaN`; they are not changed to zero or repaired.

Use `undefined_policy="raise"` when any low-speed undefinedness should stop the analysis.

## Interpretation boundary

This workflow computes continuous differential geometry. It does not reproduce event-level saccade metrics such as maximum deviation, area curvature, or polynomial-fit curvature.
