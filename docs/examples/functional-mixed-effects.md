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

## Export the coefficient table

~~~python
from eyetrajectoriespy import functional_mixed_effects_coefficient_frame

table = functional_mixed_effects_coefficient_frame(fit)
print(table.query("coefficient == 'condition'"))
~~~

## Report the model contract

~~~python
from eyetrajectoriespy import functional_mixed_effects_reporting_text

print(functional_mixed_effects_reporting_text(fit))
~~~

Report the participant count, trial count, exact scalar design coding, fixed and
random basis sizes, spline degree, ML/REML choice, optimizer, convergence,
boundary-fit status, residual structure, and whether predictors varied within
participant.

The executable counterpart is
`examples/functional_mixed_effects_regression.py`.
