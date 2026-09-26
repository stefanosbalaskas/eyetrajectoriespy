"""Executable example: marginal generalized function-on-scalar regression."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_generalized_function_on_scalar_coefficients,
    fit_generalized_function_on_scalar_regression,
    generalized_function_on_scalar_reporting_text,
    generalized_function_on_scalar_simultaneous_bands,
)


rng = np.random.default_rng(51)
n_participants = 18
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 7)
condition_template = np.array([-0.7, 0.0, 0.7])
condition = np.tile(condition_template, n_participants)
participants = np.repeat(
    [f"P{i:03d}" for i in range(n_participants)],
    trials_per_participant,
)

beta0 = -0.40 + 0.45 * time
beta1 = 0.85 - 0.30 * time
eta = beta0[None, :] + condition[:, None] * beta1[None, :]
probability = 1.0 / (1.0 + np.exp(-eta))
response = rng.binomial(1, probability).astype(float)

trajectories = TrajectorySet(
    time=time,
    values=response[:, :, None],
    curve_ids=tuple(f"C{i:04d}" for i in range(response.shape[0])),
    dimension_names=("target_aoi",),
    metadata=pd.DataFrame({"participant_id": participants}),
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
    dimension="target_aoi",
    family="binomial",
    basis_size=2,
    spline_degree=1,
)

assert fit.family == "binomial"
assert fit.link == "logit"
assert fit.working_correlation == "independence"
assert fit.n_participants == n_participants
assert np.all((fit.mean_functions > 0) & (fit.mean_functions < 1))

bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
    fit,
    n_bootstrap=100,
    random_state=51,
)
band = generalized_function_on_scalar_simultaneous_bands(
    bootstrap,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)

assert band.lower.shape == fit.coefficient_functions.shape
assert np.all(band.lower <= fit.coefficient_functions)
assert np.all(fit.coefficient_functions <= band.upper)

print("Condition coefficient:")
print(np.round(fit.coefficient_functions[1], 3))
print()
print(generalized_function_on_scalar_reporting_text(fit, band=band))
