# Rosenstein and Kantz LLE comparison

This example compares the two named local-divergence estimators under the same delay embedding, Theiler window, horizon, and fit interval.

## 1. Build a deterministic synthetic series

~~~python
import numpy as np
from eyetrajectoriespy import TrajectorySet

n = 700
x = np.empty(n)
x[0] = 0.217
for i in range(n - 1):
    x[i + 1] = 4.0 * x[i] * (1.0 - x[i])

data = TrajectorySet(
    time=np.arange(n) * 0.01,
    values=x[None, :, None],
    curve_ids=("logistic",),
    dimension_names=("x",),
    time_unit="s",
    coordinate_system="normalized",
)
~~~

## 2. Use one explicit embedding

~~~python
from eyetrajectoriespy import delay_embed_trajectory

embedded = delay_embed_trajectory(
    data,
    embedding_dimension=2,
    delay=1,
    dimensions=("x",),
)
~~~

## 3. Rosenstein path

~~~python
from eyetrajectoriespy import (
    local_divergence_curve,
    estimate_largest_lyapunov_rosenstein,
)

rosenstein_curve = local_divergence_curve(
    embedded,
    curve=0,
    theiler_window=10,
    max_horizon=8,
)

rosenstein = estimate_largest_lyapunov_rosenstein(
    rosenstein_curve,
    fit_start=1,
    fit_end=5,
)
~~~

## 4. Kantz path

~~~python
from eyetrajectoriespy import (
    kantz_divergence_curve,
    estimate_largest_lyapunov_kantz,
)

kantz_curve = kantz_divergence_curve(
    embedded,
    curve=0,
    radius=0.08,
    min_neighbors=2,
    theiler_window=10,
    max_horizon=8,
)

kantz = estimate_largest_lyapunov_kantz(
    kantz_curve,
    fit_start=1,
    fit_end=5,
)
~~~

## 5. Compare without declaring a winner

~~~python
print("Rosenstein:", rosenstein.exponent, rosenstein.exponent_unit)
print("Kantz:", kantz.exponent, kantz.exponent_unit)
print("Kantz reference counts:", kantz_curve.reference_counts)
print("Kantz pair counts:", kantz_curve.pair_counts)
~~~

Different estimates are expected because one method uses a nearest neighbor and the other uses a radius-defined neighborhood.

The comparison is descriptive unless an inferential design for estimator comparison has been declared.

## 6. Plot

~~~python
from eyetrajectoriespy import plot_local_divergence

ax = plot_local_divergence(rosenstein)
ax.figure.savefig("rosenstein-lle.svg")

ax = plot_local_divergence(kantz)
ax.figure.savefig("kantz-lle.svg")
~~~

## 7. Reporting

~~~python
from eyetrajectoriespy import largest_lyapunov_reporting_text

print(largest_lyapunov_reporting_text(rosenstein))
print(largest_lyapunov_reporting_text(kantz))
~~~

The helper names the estimator family and preserves the non-chaos interpretation boundary.

The executable counterpart is `examples/kantz_lle.py`.
