# Worked example: nonlinear gaze dynamics

This example uses deterministic synthetic data so the workflow can be run in CI. The goal is to demonstrate the analysis contract, not to claim that the synthetic signal reproduces human gaze.

## Create a continuous trajectory

```python
import numpy as np
from eyetrajectoriespy import TrajectorySet

time = np.arange(600, dtype=float) * 0.01
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
```

## Inspect delay and dimension diagnostics

```python
from eyetrajectoriespy import (
    embedding_delay_diagnostics,
    embedding_dimension_diagnostics,
)

delay_diag = embedding_delay_diagnostics(
    gaze,
    curve=0,
    dimension="x",
    max_lag=30,
    bins=12,
)

dimension_diag = embedding_dimension_diagnostics(
    gaze,
    curve=0,
    dimension="x",
    delay=1,
    max_dimension=5,
    theiler_window=10,
)
```

These are diagnostics only. The analysis still declares its own \(m\) and \(\tau\).

## Reconstruct state space

```python
from eyetrajectoriespy import delay_embed_trajectory

embedded = delay_embed_trajectory(
    gaze,
    embedding_dimension=2,
    delay=1,
    dimensions=("x",),
)
```

## Sparse recurrence and RQA

```python
from eyetrajectoriespy import recurrence_matrix, rqa_metrics

recurrence = recurrence_matrix(
    embedded,
    curve=0,
    target_recurrence_rate=0.05,
    theiler_window=10,
)

metrics = rqa_metrics(
    recurrence,
    min_diagonal_length=2,
    min_vertical_length=2,
)

print(metrics)
```

The solved radius and achieved recurrence rate remain in `recurrence`.

## Time-varying recurrence

```python
from eyetrajectoriespy import windowed_rqa

dynamic = windowed_rqa(
    gaze,
    curve=0,
    window=150,
    step=75,
    radius=0.05,
    theiler_window=10,
    dimensions=("x",),
)

print(dynamic.table)
print("tail samples not in a full window:", dynamic.dropped_tail_samples)
```

## Local divergence and LLE

```python
from eyetrajectoriespy import (
    local_divergence_curve,
    estimate_largest_lyapunov_rosenstein,
)

divergence = local_divergence_curve(
    embedded,
    curve=0,
    theiler_window=10,
    max_horizon=8,
)

lle = estimate_largest_lyapunov_rosenstein(
    divergence,
    fit_start=1,
    fit_end=5,
)

print(lle.exponent, lle.exponent_unit)
print(lle.r_squared)
```

The fit interval is deliberately explicit.

## IAAFT surrogate test

```python
from eyetrajectoriespy import surrogate_nonlinearity_test

surrogate = surrogate_nonlinearity_test(
    gaze,
    curve=0,
    dimension="x",
    statistic="largest_lyapunov",
    embedding_dimension=2,
    delay=1,
    theiler_window=10,
    max_horizon=8,
    fit_start=1,
    fit_end=5,
    n_surrogates=19,
    max_iterations=100,
    tolerance=1e-6,
    random_state=42,
)

print(surrogate.p_value)
```

For research use, choose the surrogate count before examining the result and use substantially more than this CI-sized example.

## Plots

```python
from eyetrajectoriespy import (
    plot_embedding_delay_diagnostics,
    plot_embedding_dimension_diagnostics,
    plot_local_divergence,
    plot_recurrence,
    plot_surrogate_nonlinearity,
    plot_windowed_rqa,
)

plot_embedding_delay_diagnostics(delay_diag)
plot_embedding_dimension_diagnostics(dimension_diag)
plot_recurrence(recurrence)
plot_windowed_rqa(dynamic)
plot_local_divergence(lle)
plot_surrogate_nonlinearity(surrogate)
```

See the [visual gallery](../methods/visual-gallery.md) for CI-generated SVG versions.
