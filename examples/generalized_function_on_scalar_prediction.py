"""Executable example: fixed-profile generalized FoSR marginal inference."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_generalized_function_on_scalar_coefficients,
    bootstrap_generalized_function_on_scalar_predictions,
    fit_generalized_function_on_scalar_regression,
    generalized_function_on_scalar_mean_difference_band,
    generalized_function_on_scalar_predict,
    generalized_function_on_scalar_prediction_bands,
)


rng = np.random.default_rng(52)
n_participants = 14
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 5)
condition_template = np.array([-0.5, 0.0, 0.5])
condition = np.tile(condition_template, n_participants)
participant_ids = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)

beta0 = 0.25 + 0.15 * time
beta1 = 0.35 - 0.10 * time
eta = beta0[None, :] + condition[:, None] * beta1[None, :]
mean = np.exp(eta)
response = rng.poisson(mean).astype(float)

trajectories = TrajectorySet(
    time=time,
    values=response[:, :, None],
    curve_ids=tuple(f"C{i:03d}" for i in range(response.shape[0])),
    dimension_names=("fixation_count",),
    metadata=pd.DataFrame({"participant_id": participant_ids}),
    time_unit="s",
)

design = pd.DataFrame(
    {
        "curve_id": trajectories.curve_ids,
        "condition": condition,
    }
)

fit = fit_generalized_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="fixation_count",
    family="poisson",
    basis_size=2,
    spline_degree=1,
)

profiles = pd.DataFrame(
    {
        "profile_id": ("low", "high", "extrapolated"),
        "condition": (-0.5, 0.5, 1.0),
    }
)

prediction = generalized_function_on_scalar_predict(
    fit,
    profiles,
)
assert prediction.extrapolation_flags.tolist() == [False, False, True]
assert np.all(prediction.mean_functions > 0.0)

coefficient_bootstrap = (
    bootstrap_generalized_function_on_scalar_coefficients(
        fit,
        n_bootstrap=100,
        random_state=52,
    )
)

prediction_bootstrap = (
    bootstrap_generalized_function_on_scalar_predictions(
        coefficient_bootstrap,
        profiles,
    )
)

band = generalized_function_on_scalar_prediction_bands(
    prediction_bootstrap,
    confidence_level=0.95,
    simultaneous_scope="family",
)
assert np.all(band.mean_lower > 0.0)
assert np.all(band.mean_lower <= prediction.mean_functions)
assert np.all(prediction.mean_functions <= band.mean_upper)

difference = generalized_function_on_scalar_mean_difference_band(
    prediction_bootstrap,
    profile_a="high",
    profile_b="low",
    confidence_level=0.95,
)
assert difference.estimate.shape == time.shape
assert np.all(difference.lower <= difference.estimate)
assert np.all(difference.estimate <= difference.upper)

print(
    "Fixed profiles:",
    ", ".join(prediction.profile_ids),
)
print(
    "Extrapolation flags:",
    prediction.extrapolation_flags.tolist(),
)
print(
    "Mean difference high-low:",
    np.round(difference.estimate, 4).tolist(),
)
