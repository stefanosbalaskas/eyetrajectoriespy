"""Executable example: explicit physical-time residual covariance."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_reporting_text,
)


rng = np.random.default_rng(49)
n_participants = 10
trials_per_participant = 3
time = np.array([0.0, 0.06, 0.16, 0.32, 0.55, 0.78, 1.0])
basis = np.column_stack([1.0 - time, time])

participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile(np.array([-0.6, 0.0, 0.6]), n_participants)
beta0 = 0.25 + 0.10 * time
beta1 = 0.15 + 0.22 * time

participant_covariance = np.array(
    [[0.022, 0.003], [0.003, 0.017]]
)
participant_coefficients = rng.multivariate_normal(
    np.zeros(2),
    participant_covariance,
    size=n_participants,
)

phi = 0.16
residual_sd = 0.055
distance = np.abs(np.subtract.outer(time, time))
residual_correlation = np.exp(-distance / phi)
residual_chol = np.linalg.cholesky(
    residual_sd**2 * residual_correlation
)

values = []
curve_ids = []
for participant_index in range(n_participants):
    participant_function = (
        participant_coefficients[participant_index] @ basis.T
    )
    for trial_index in range(trials_per_participant):
        curve_index = (
            participant_index * trials_per_participant + trial_index
        )
        response = (
            beta0
            + condition[curve_index] * beta1
            + participant_function
            + residual_chol @ rng.normal(size=time.size)
        )
        values.append(response[:, None])
        curve_ids.append(f"C{curve_index:03d}")

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(curve_ids),
    dimension_names=("metric",),
    metadata=pd.DataFrame({"participant_id": participants}),
    time_unit="s",
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
    residual_correlation="exponential",
    spline_degree=1,
    reml=False,
    method="lbfgs",
    maxiter=1000,
)

raw = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=3,
    residual_scale="raw",
)
white = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=3,
    residual_scale="whitened",
)

print("Residual family:", fit.residual_correlation)
print(
    "Estimated phi:",
    round(float(fit.residual_correlation_parameter), 4),
    fit.residual_correlation_parameter_unit,
)
print(
    "Boundary flag:",
    fit.residual_correlation_boundary_fit,
)
print(
    "Raw lag-1 ACF:",
    round(
        float(
            raw.overall_diagnostics.loc[
                raw.overall_diagnostics["lag_index"] == 1,
                "autocorrelation",
            ].iloc[0]
        ),
        3,
    ),
)
print(
    "Whitened lag-1 ACF:",
    round(
        float(
            white.overall_diagnostics.loc[
                white.overall_diagnostics["lag_index"] == 1,
                "autocorrelation",
            ].iloc[0]
        ),
        3,
    ),
)
print(functional_mixed_effects_reporting_text(fit))
