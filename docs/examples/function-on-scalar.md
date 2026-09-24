# Function-on-scalar regression for an experimental condition

This example simulates a continuous functional outcome with a condition effect that changes over trial time.

## Create a functional response

~~~python
import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet

rng = np.random.default_rng(2026)
n = 48
time = np.linspace(0.0, 1.5, 81)
condition = np.repeat([0.0, 1.0], n // 2)

beta0 = 0.2 * np.sin(2 * np.pi * time / 1.5)
beta_condition = 0.35 * np.exp(-((time - 0.8) / 0.25) ** 2)

noise = rng.normal(0.0, 0.12, size=(n, time.size))
response = (
    beta0[None, :]
    + condition[:, None] * beta_condition[None, :]
    + noise
)

trajectories = TrajectorySet(
    time=time,
    values=response[:, :, None],
    curve_ids=tuple(f"C{i:02d}" for i in range(n)),
    dimension_names=("metric",),
    coordinate_system="arbitrary",
    time_unit="s",
)

design = pd.DataFrame({
    "curve_id": trajectories.curve_ids,
    "condition": condition,
})
~~~

## Fit the coefficient functions

~~~python
from eyetrajectoriespy import fit_function_on_scalar_regression

fit = fit_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
)
~~~

The fitted model is

$$
Y_i(t)
=
\beta_0(t)
+
\beta_1(t)\mathrm{Condition}_i
+
\varepsilon_i(t).
$$

No spline basis or time smoothing is inserted. The returned `beta_1(t)` is the observed-grid condition coefficient function.

## Bootstrap and simultaneous band

~~~python
from eyetrajectoriespy import (
    bootstrap_function_on_scalar_coefficients,
    function_on_scalar_simultaneous_bands,
)

boot = bootstrap_function_on_scalar_coefficients(
    fit,
    n_bootstrap=1000,
    multiplier="rademacher",
    random_state=2026,
)

band = function_on_scalar_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
~~~

The critical value is calibrated over the whole observed time grid for the condition coefficient rather than treating every time point as an unrelated test.

## Visualize the condition coefficient

~~~python
from eyetrajectoriespy import plot_function_on_scalar_coefficients

ax = plot_function_on_scalar_coefficients(
    band,
    coefficient="condition",
    dimension="metric",
)
~~~

Interpret the plot as a functional coefficient with an observed-grid simultaneous uncertainty band. Do not call the first grid point where the band excludes zero a statistically validated onset time unless onset estimation was separately defined and calibrated.

## Long-form coefficient table

~~~python
from eyetrajectoriespy import function_on_scalar_coefficient_frame

table = function_on_scalar_coefficient_frame(
    fit,
    band=band,
)

print(table.query("coefficient == 'condition'").head())
~~~

## Repeated-trial guardrail

If multiple trials belong to the same participant and the predictor is a participant-level variable, use participant aggregation:

~~~python
fit_between = fit_function_on_scalar_regression(
    repeated_gaze,
    participant_design,
    predictors=("expert",),
    unit="participant",
    participant_column="participant_id",
)
~~~

If a predictor varies from trial to trial within participant, version 0.35 raises instead of aggregating it. That design requires the repeated-measures functional regression layer planned for the next tranche.

## Reporting text

~~~python
from eyetrajectoriespy import function_on_scalar_reporting_text

print(function_on_scalar_reporting_text(fit, band=band))
~~~

The executable counterpart is `examples/function_on_scalar_regression.py`.
