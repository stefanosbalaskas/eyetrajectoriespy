"""Executable one-random-functional-slope example."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_random_effect_frame,
)

rng = np.random.default_rng(2045)
n_participants = 16
trials_per_participant = 4
time = np.linspace(0.0, 1.0, 7)
basis = np.column_stack([1.0 - time, time])
condition = np.tile(
    np.array([-0.75, -0.25, 0.25, 0.75]),
    n_participants,
)
participants = np.repeat(
    [f"P{i:03d}" for i in range(n_participants)],
    trials_per_participant,
)

covariance = np.array(
    [
        [0.030, 0.004, 0.009, 0.002],
        [0.004, 0.022, 0.002, 0.007],
        [0.009, 0.002, 0.020, 0.003],
        [0.002, 0.007, 0.003, 0.016],
    ]
)
random_coefficients = rng.multivariate_normal(
    np.zeros(4),
    covariance,
    size=n_participants,
)
random_intercept = random_coefficients[:, :2] @ basis.T
random_slope = random_coefficients[:, 2:] @ basis.T
beta0 = 0.25 + 0.12 * time
beta1 = 0.18 + 0.30 * time

values = []
curve_ids = []
for participant_index in range(n_participants):
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        values.append(
            (
                beta0
                + condition[row] * beta1
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
    coordinate_system="unknown",
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
    random_slope_predictor="condition",
    spline_degree=1,
    maxiter=1000,
)

frame = functional_random_effect_frame(fit, effect="slope")
assert fit.random_slope_predictor == "condition"
assert fit.random_effect_dimension == 4
assert fit.random_effect_covariance_parameter_count == 10
assert fit.n_participants == 16
assert len(frame) == fit.n_participants * fit.time.size
assert fit.random_slope_functions is not None
assert fit.random_intercept_slope_covariance.shape == (2, 2)

print(fit.random_effect_covariance_eigenvalues)
print(fit.random_effect_covariance_condition_number)
