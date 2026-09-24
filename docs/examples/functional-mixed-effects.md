# Repeated-measures functional regression

This example fits a condition effect that varies over trial time while
preserving repeated trials within participant.

## Simulate repeated trajectories

~~~python
import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet

rng = np.random.default_rng(2026)
n_participants = 12
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 9)

participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile([0.0, 1.0, 0.5], n_participants)

beta0 = 0.20 + 0.15 * time
beta_condition = 0.15 + 0.40 * time

linear_basis = np.column_stack([1.0 - time, time])
random_coefficients = rng.multivariate_normal(
    [0.0, 0.0],
    [[0.030, 0.004], [0.004, 0.020]],
    size=n_participants,
)

curves = []
curve_ids = []
for i in range(n_participants):
    participant_function = random_coefficients[i] @ linear_basis.T
    for j in range(trials_per_participant):
        row = i * trials_per_participant + j
        curves.append(
            (
                beta0
                + condition[row] * beta_condition
                + participant_function
                + rng.normal(0.0, 0.04, size=time.size)
            )[:, None]
        )
        curve_ids.append(f"C{row:03d}")

gaze_metric = TrajectorySet(
    time=time,
    values=np.asarray(curves),
    curve_ids=tuple(curve_ids),
    dimension_names=("metric",),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="unknown",
    time_unit="s",
)

design = pd.DataFrame({
    "curve_id": gaze_metric.curve_ids,
    "condition": condition,
})
~~~

The condition predictor varies within every participant, so participant-level
aggregation would erase the repeated-measures contrast.

## Fit one joint functional mixed model

~~~python
from eyetrajectoriespy import fit_functional_mixed_effects_regression

fit = fit_functional_mixed_effects_regression(
    gaze_metric,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=2,
    random_basis_size=2,
    spline_degree=1,
    reml=True,
)
~~~

The model is

$$
Y_{ij}(t)
=
\beta_0(t)
+
\beta_1(t)\mathrm{Condition}_{ij}
+
b_i(t)
+
\varepsilon_{ij}(t).
$$

All time points and trials enter a single mixed-effects likelihood.

## Inspect the coefficient function

~~~python
from eyetrajectoriespy import plot_functional_mixed_effects_coefficient

ax = plot_functional_mixed_effects_coefficient(
    fit,
    coefficient="condition",
)
~~~

The shaded region is a 95% pointwise Wald interval. It should not be described
as a simultaneous whole-function confidence band.

## Add a simultaneous whole-function band

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    functional_mixed_effects_simultaneous_bands,
)

boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=500,
    random_state=44,
)

band = functional_mixed_effects_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)

ax = plot_functional_mixed_effects_coefficient(
    band,
    coefficient="condition",
)
~~~

This band is simultaneous over the observed time grid for the declared
coefficient. Whole participant trial bundles are resampled; the fitted
random-effect covariance and residual variance are held fixed.

## Refit variance components under participant resampling

For sensitivity to covariance-estimation uncertainty, version 0.46 provides a
separate full-refit bootstrap:

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
)

full = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=500,
    random_state=46,
)

full_band = functional_mixed_effects_simultaneous_bands(full)
~~~

Every selected participant occurrence receives a distinct bootstrap group ID;
fixed effects, random-effect covariance and residual variance are refit in every
replicate. See the
[full-refit worked example](functional-mixed-effects-full-refit-bootstrap.md)
for covariance-stability and fixed-versus-full uncertainty diagnostics.

## Export the coefficient table

~~~python
from eyetrajectoriespy import functional_mixed_effects_coefficient_frame

table = functional_mixed_effects_coefficient_frame(fit, band=band)
print(table.query("coefficient == 'condition'"))
~~~

## Report the model contract

~~~python
from eyetrajectoriespy import functional_mixed_effects_reporting_text

print(functional_mixed_effects_reporting_text(fit, band=band))
~~~

Report the participant count, trial count, exact scalar design coding, fixed and
random basis sizes, spline degree, ML/REML choice, optimizer, convergence,
boundary-fit status, residual structure, whether predictors varied within
participant, bootstrap replicate count, simultaneous scope, and the fact that
variance components were conditioned on rather than refitted.

The executable counterpart is
`examples/functional_mixed_effects_regression.py`.

## Participant-specific random condition effects

If the scientific question is not only the population condition coefficient
but whether participants differ in that time-varying condition response, use
the guarded 0.45 random-slope extension rather than manually fitting separate
participant curves:

~~~python
fit_slope = fit_functional_mixed_effects_regression(
    gaze_metric,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=2,
    random_basis_size=2,
    random_slope_predictor="condition",
    spline_degree=1,
)
~~~

The predictor must vary within every participant and the participant count must
exceed the number of free unstructured random-effect covariance parameters.
See the
[random-functional-slope worked example](functional-mixed-effects-random-slope.md)
for covariance diagnostics and participant BLUP slope inspection.
