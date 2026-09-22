"""CI-small nonlinear dynamics workflow."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    embedding_delay_diagnostics,
    embedding_dimension_diagnostics,
    estimate_largest_lyapunov_rosenstein,
    local_divergence_curve,
    recurrence_matrix,
    rqa_metrics,
    surrogate_nonlinearity_test,
    windowed_rqa,
)


time = np.arange(450, dtype=float) * 0.01
x = np.empty(time.size)
x[0] = 0.217
for i in range(time.size - 1):
    x[i + 1] = 4.0 * x[i] * (1.0 - x[i])

gaze = TrajectorySet(
    time=time,
    values=x[None, :, None],
    curve_ids=("demo",),
    dimension_names=("x",),
    time_unit="s",
    coordinate_system="arbitrary",
)

delay_diag = embedding_delay_diagnostics(
    gaze,
    curve=0,
    dimension="x",
    max_lag=20,
    bins=12,
)
dimension_diag = embedding_dimension_diagnostics(
    gaze,
    curve=0,
    dimension="x",
    delay=1,
    max_dimension=4,
    theiler_window=8,
)
embedded = delay_embed_trajectory(
    gaze,
    embedding_dimension=2,
    delay=1,
    dimensions=("x",),
)
recurrence = recurrence_matrix(
    embedded,
    curve=0,
    target_recurrence_rate=0.05,
    theiler_window=8,
)
metrics = rqa_metrics(recurrence)

dynamic = windowed_rqa(
    gaze,
    curve=0,
    window=120,
    step=60,
    radius=0.05,
    theiler_window=8,
    dimensions=("x",),
)

divergence = local_divergence_curve(
    embedded,
    curve=0,
    theiler_window=8,
    max_horizon=7,
)
lle = estimate_largest_lyapunov_rosenstein(
    divergence,
    fit_start=1,
    fit_end=4,
)

surrogate = surrogate_nonlinearity_test(
    gaze,
    curve=0,
    dimension="x",
    statistic="largest_lyapunov",
    embedding_dimension=2,
    delay=1,
    theiler_window=8,
    max_horizon=7,
    fit_start=1,
    fit_end=4,
    n_surrogates=3,
    max_iterations=30,
    tolerance=1e-6,
    random_state=42,
)

assert not delay_diag.table.empty
assert not dimension_diag.table.empty
assert recurrence.matrix.nnz > 0
assert 0 <= metrics.recurrence_rate <= 1
assert not dynamic.table.empty
assert np.isfinite(lle.exponent)
assert surrogate.surrogate_statistics.shape == (3,)

print("RQA recurrence rate:", metrics.recurrence_rate)
print("LLE:", lle.exponent, lle.exponent_unit)
print("surrogate p:", surrogate.p_value)
