"""Compare named Rosenstein and Kantz largest-Lyapunov estimators."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    estimate_largest_lyapunov_kantz,
    estimate_largest_lyapunov_rosenstein,
    kantz_divergence_curve,
    largest_lyapunov_reporting_text,
    local_divergence_curve,
)


n = 700
x = np.empty(n, dtype=float)
x[0] = 0.217
for i in range(n - 1):
    x[i + 1] = 4.0 * x[i] * (1.0 - x[i])

data = TrajectorySet(
    time=np.arange(n, dtype=float) * 0.01,
    values=x[None, :, None],
    curve_ids=("logistic",),
    dimension_names=("x",),
    time_unit="s",
    coordinate_system="normalized",
)

embedded = delay_embed_trajectory(
    data,
    embedding_dimension=2,
    delay=1,
    dimensions=("x",),
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

print(largest_lyapunov_reporting_text(rosenstein))
print(largest_lyapunov_reporting_text(kantz))
print("Kantz reference counts:", kantz_curve.reference_counts.tolist())
print("Kantz pair counts:", kantz_curve.pair_counts.tolist())
