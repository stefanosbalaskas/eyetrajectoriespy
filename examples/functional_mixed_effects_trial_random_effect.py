"""Executable 0.48 nested trial functional random-effect example."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_residual_diagnostics,
    functional_trial_random_effect_frame,
)


rng = np.random.default_rng(48)
n_participants = 10
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 7)
basis = np.column_stack([1.0 - time, time])

participant_ids = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
trial_ids = np.tile(
    [f"T{j:02d}" for j in range(trials_per_participant)],
    n_participants,
)
condition = np.tile(
    np.array([-0.75, 0.0, 0.75]),
    n_participants,
)

beta0 = 0.25 + 0.10 * time
beta1 = 0.18 + 0.28 * time
participant_covariance = np.array(
    [[0.030, 0.005], [0.005, 0.022]]
)
trial_covariance = np.array(
    [[0.022, 0.006], [0.006, 0.017]]
)

participant_coefficients = rng.multivariate_normal(
    np.zeros(2),
    participant_covariance,
    size=n_participants,
)
trial_coefficients = rng.multivariate_normal(
    np.zeros(2),
    trial_covariance,
    size=n_participants * trials_per_participant,
)

values = []
curve_ids = []
for participant_index in range(n_participants):
    participant_function = participant_coefficients[participant_index] @ basis.T
    for trial_index in range(trials_per_participant):
        curve_index = participant_index * trials_per_participant + trial_index
        trial_function = trial_coefficients[curve_index] @ basis.T
        response = (
            beta0
            + condition[curve_index] * beta1
            + participant_function
            + trial_function
            + rng.normal(0.0, 0.02, size=time.size)
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
            "participant_id": participant_ids,
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

fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    trial_column="trial_id",
    trial_random_effect="functional_intercept",
    dimension="metric",
    fixed_basis_size=2,
    random_basis_size=2,
    trial_random_basis_size=2,
    spline_degree=1,
    reml=True,
    method="lbfgs",
    maxiter=1000,
)

trial_frame = functional_trial_random_effect_frame(fit)
diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=2,
)

assert fit.trial_random_effect == "functional_intercept"
assert fit.trial_random_effect_covariance.shape == (2, 2)
assert len(trial_frame) == trajectories.n_curves * trajectories.n_time
assert diagnostics.reference is fit
assert fit.provenance["functional_mixed_effects_regression"][
    "automatic_trial_random_effect_selection"
] is False

print(fit.trial_random_effect_covariance)
print(diagnostics.overall_diagnostics.to_string(index=False))
