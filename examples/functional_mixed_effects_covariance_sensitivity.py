"""Executable example: predeclared mixed-effects covariance sensitivity."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalMixedEffectsCovarianceSpecification,
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_covariance_sensitivity,
    functional_mixed_effects_covariance_sensitivity_reporting_text,
)


rng = np.random.default_rng(500)
n_participants = 10
trials_per_participant = 3
time = np.array([0.0, 0.08, 0.22, 0.51, 1.0])
basis = np.column_stack([1.0 - time, time])
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
trial_ids = np.tile(
    [f"T{j:02d}" for j in range(trials_per_participant)],
    n_participants,
)
condition = np.tile(np.array([-0.5, 0.0, 0.5]), n_participants)

beta0 = 0.20 + 0.12 * time
beta1 = 0.10 + 0.22 * time
participant_coefficients = rng.multivariate_normal(
    np.zeros(2),
    np.array([[0.020, 0.003], [0.003, 0.016]]),
    size=n_participants,
)
trial_coefficients = rng.multivariate_normal(
    np.zeros(2),
    np.array([[0.008, 0.001], [0.001, 0.006]]),
    size=n_participants * trials_per_participant,
)
phi = 0.12
correlation = np.exp(
    -np.abs(np.subtract.outer(time, time)) / phi
)
residual_chol = np.linalg.cholesky(0.04**2 * correlation)

values = []
curve_ids = []
for participant_index in range(n_participants):
    participant_function = participant_coefficients[participant_index] @ basis.T
    for trial_index in range(trials_per_participant):
        curve_index = (
            participant_index * trials_per_participant + trial_index
        )
        trial_function = trial_coefficients[curve_index] @ basis.T
        residual = residual_chol @ rng.normal(size=time.size)
        response = (
            beta0
            + condition[curve_index] * beta1
            + participant_function
            + trial_function
            + residual
        )
        values.append(response[:, None])
        curve_ids.append(f"C{curve_index:03d}")

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(curve_ids),
    dimension_names=("metric",),
    metadata=pd.DataFrame(
        {
            "participant_id": participants,
            "trial_id": trial_ids,
        }
    ),
    time_unit="s",
)
design = pd.DataFrame(
    {
        "curve_id": trajectories.curve_ids,
        "condition": condition,
    }
)


def fit_model(*, trial_effect, residual_correlation):
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id" if trial_effect else None,
        trial_random_effect=(
            "functional_intercept" if trial_effect else None
        ),
        residual_correlation=residual_correlation,
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=False,
        method="lbfgs",
        maxiter=900,
    )


fits = {
    "M1": fit_model(trial_effect=False, residual_correlation="iid"),
    "M2": fit_model(trial_effect=True, residual_correlation="iid"),
    "M3": fit_model(
        trial_effect=False,
        residual_correlation="exponential",
    ),
    "M4": fit_model(
        trial_effect=True,
        residual_correlation="exponential",
    ),
}

specifications = (
    FunctionalMixedEffectsCovarianceSpecification(
        "M1",
        residual_correlation="iid",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        "M2",
        trial_random_effect="functional_intercept",
        residual_correlation="iid",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        "M3",
        residual_correlation="exponential",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        "M4",
        trial_random_effect="functional_intercept",
        residual_correlation="exponential",
    ),
)

result = functional_mixed_effects_covariance_sensitivity(
    fits,
    specifications=specifications,
    reference="M1",
    max_lag=2,
)

assert result.n_models == 4
assert result.n_successful == 4
assert result.n_failed == 0
assert list(result.model_summary["model"]) == ["M1", "M2", "M3", "M4"]
assert result.provenance[
    "functional_mixed_effects_covariance_sensitivity"
]["automatic_model_selection"] is False

print(
    result.model_summary[
        [
            "model",
            "log_likelihood",
            "aic",
            "bic",
            "trial_covariance_trace",
            "residual_variance",
            "residual_correlation_parameter",
        ]
    ].to_string(index=False)
)
print()
print(
    functional_mixed_effects_covariance_sensitivity_reporting_text(
        result
    )
)
