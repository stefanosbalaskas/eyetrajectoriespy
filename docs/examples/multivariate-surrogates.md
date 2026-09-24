# Planar gaze surrogate analysis

This example generates joint x/y MIAAFT surrogates instead of independently
randomizing the two gaze coordinates.

## Coupled planar signal

~~~python
import numpy as np

from eyetrajectoriespy import TrajectorySet

rng = np.random.default_rng(12)
n = 256
x = np.empty(n)
y = np.empty(n)
x[0] = rng.normal()
y[0] = rng.normal()

for i in range(1, n):
    x[i] = 0.82 * x[i - 1] + rng.normal(0.0, 0.55)
    y[i] = (
        0.55 * y[i - 1]
        + 0.65 * x[i - 1]
        + rng.normal(0.0, 0.35)
    )

gaze = TrajectorySet(
    time=np.arange(n) * 0.01,
    values=np.column_stack([x, y])[None, :, :],
    curve_ids=("coupled",),
    dimension_names=("x", "y"),
    coordinate_system="unknown",
    time_unit="s",
)
~~~

The two dimensions have structured lagged linear dependence.

## Generate multivariate surrogates

~~~python
from eyetrajectoriespy import generate_multivariate_iaaft_surrogates

result = generate_multivariate_iaaft_surrogates(
    gaze,
    curve="coupled",
    dimensions=("x", "y"),
    reference_dimension="x",
    n_surrogates=20,
    max_iterations=1000,
    tolerance=1e-8,
    random_state=2026,
)
~~~

Each returned surrogate has shape time × dimension.

## Verify exact marginal restoration

~~~python
for surrogate in result.surrogates:
    np.testing.assert_allclose(
        np.sort(surrogate[:, 0]),
        np.sort(result.source_values[:, 0]),
    )
    np.testing.assert_allclose(
        np.sort(surrogate[:, 1]),
        np.sort(result.source_values[:, 1]),
    )
~~~

This exact rank constraint should not be confused with exact spectral
preservation.

## Inspect spectral preservation

~~~python
from eyetrajectoriespy import multivariate_iaaft_diagnostics_frame

diagnostics = multivariate_iaaft_diagnostics_frame(result)
print(diagnostics.head())
~~~

The table reports maximum and mean relative per-channel spectrum error and
pairwise cross-spectrum error for every surrogate.

## Plot diagnostics

~~~python
from eyetrajectoriespy import plot_multivariate_iaaft_diagnostics

ax = plot_multivariate_iaaft_diagnostics(result)
~~~

Large or unstable retained errors are a reason to review the declared
tolerance, sample length, reference dimension, or suitability of the
surrogate model rather than silently accepting the ensemble.

## Multichannel nonlinear-statistic test

~~~python
from eyetrajectoriespy import multivariate_surrogate_nonlinearity_test

test = multivariate_surrogate_nonlinearity_test(
    gaze,
    curve="coupled",
    dimensions=("x", "y"),
    reference_dimension="x",
    statistic="largest_lyapunov",
    embedding_dimension=2,
    delay=1,
    theiler_window=8,
    max_horizon=6,
    fit_start=1,
    fit_end=4,
    n_surrogates=19,
    max_iterations=1000,
    tolerance=1e-8,
    random_state=2026,
)
~~~

The smallest possible one-sided plus-one Monte Carlo p-value with 19
surrogates is 0.05. Use more surrogates when finer Monte Carlo resolution is
required.

## Reporting helper

~~~python
from eyetrajectoriespy import (
    multivariate_surrogate_nonlinearity_reporting_text,
)

print(multivariate_surrogate_nonlinearity_reporting_text(test))
~~~

The executable counterpart is
`examples/multivariate_iaaft_surrogates.py`.
