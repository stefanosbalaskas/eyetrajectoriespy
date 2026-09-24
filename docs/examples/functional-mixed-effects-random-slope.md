# Worked random functional slope example

This example allows participants to differ over trial time in how strongly a
within-participant condition changes the functional response.

~~~python
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_random_effect_frame,
    plot_functional_random_effects,
)

rng = np.random.default_rng(2045)
n_participants = 20
trials_per_participant = 4
time = np.linspace(0.0, 1.0, 9)
basis = np.column_stack([1.0 - time, time])

condition = np.tile(
    np.array([-0.75, -0.25, 0.25, 0.75]),
    n_participants,
)
participants = np.repeat(
    [f"P{i:03d}" for i in range(n_participants)],
    trials_per_participant,
)

beta0 = 0.25 + 0.12 * time
beta_condition = 0.18 + 0.30 * time

covariance = np.array(
    [
        [0.030, 0.004, 0.010, 0.002],
        [0.004, 0.022, 0.002, 0.008],
        [0.010, 0.002, 0.022, 0.003],
        [0.002, 0.008, 0.003, 0.017],
    ]
)
random_coefficients = rng.multivariate_normal(
    np.zeros(4),
    covariance,
    size=n_participants,
)
random_intercept = random_coefficients[:, :2] @ basis.T
random_slope = random_coefficients[:, 2:] @ basis.T

values = []
curve_ids = []
for participant_index in range(n_participants):
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        values.append(
            (
                beta0
                + condition[row] * beta_condition
                + random_intercept[participant_index]
                + condition[row] * random_slope[participant_index]
                + rng.normal(0.0, 0.025, size=time.size)
            )[:, None]
        )
        curve_ids.append(f"C{row:04d}")

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(curve_ids),
    dimension_names=("metric",),
    metadata=pd.DataFrame({"participant_id": participants}),
    time_unit="s",
    coordinate_system="unknown",
)

design = pd.DataFrame(
    {
        "curve_id": trajectories.curve_ids,
        "condition": condition,
    }
)

fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=2,
    random_basis_size=2,
    random_slope_predictor="condition",
    spline_degree=1,
    maxiter=1000,
)
~~~

With $q=2$, the stacked random-effect vector has dimension four and its
unstructured covariance has ten free parameters. The 20-participant example
therefore passes the 0.45 covariance-complexity guard.

## Inspect the covariance structure

~~~python
print(fit.random_effect_dimension)
print(fit.random_effect_covariance_parameter_count)
print(fit.random_effect_covariance_eigenvalues)
print(fit.random_effect_covariance_condition_number)

print(fit.random_intercept_covariance)
print(fit.random_slope_covariance)
print(fit.random_intercept_slope_covariance)
~~~

Do not interpret a large covariance matrix as scientifically stable merely
because the optimizer converged. Inspect the retained eigenvalues, condition
number, boundary diagnostics, participant count, and substantive plausibility.

## Inspect participant slope functions

~~~python
slope_table = functional_random_effect_frame(
    fit,
    effect="slope",
)

ax = plot_functional_random_effects(
    fit,
    effect="slope",
)
~~~

Each plotted curve is a participant BLUP
$\widehat b_{1i}(t)$. Positive values indicate a participant-specific
condition response above the population fixed condition coefficient at that
time; negative values indicate a response below it.

## Keep 0.44 simultaneous inference conditional

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    functional_mixed_effects_simultaneous_bands,
)

boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=500,
    random_state=45,
)

band = functional_mixed_effects_simultaneous_bands(
    boot,
    simultaneous_scope="coefficient",
)
~~~

This bootstrap keeps the fitted random intercept/slope covariance fixed. It
does not refit the covariance matrix inside each bootstrap sample.
