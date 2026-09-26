"""Canonical grouped-binomial generalized functional-response workflow."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_generalized_function_on_scalar_coefficients,
    fit_generalized_function_on_scalar_regression,
    generalized_function_on_scalar_reporting_text,
    generalized_function_on_scalar_simultaneous_bands,
)


rng = np.random.default_rng(573)
n_participants = 20
trials_per_participant = 2
time = np.linspace(0.0, 1.0, 7)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile(np.array([0.0, 1.0]), n_participants)
denominator = np.full((condition.size, time.size), 12.0)
eta = (
    -0.35
    + 0.30 * time[None, :]
    + condition[:, None] * (0.55 - 0.20 * time[None, :])
)
probability = 1.0 / (1.0 + np.exp(-eta))
successes = rng.binomial(denominator.astype(int), probability).astype(float)

trajectories = TrajectorySet(
    time=time,
    values=successes[:, :, None],
    curve_ids=tuple(f"B{i:03d}" for i in range(successes.shape[0])),
    dimension_names=("target_successes",),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="unknown",
    time_unit="s",
    provenance={
        "example": "canonical_generalized_responses",
        "observation": "successes out of explicit opportunities",
    },
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
    dimension="target_successes",
    family="binomial",
    binomial_denominator=denominator,
    basis_size=2,
    spline_degree=1,
)
bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
    fit,
    n_bootstrap=100,
    random_state=573,
)
band = generalized_function_on_scalar_simultaneous_bands(
    bootstrap,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
print(generalized_function_on_scalar_reporting_text(fit, band=band))
print(
    "Interpretation: integer successes and denominators remain distinct; "
    "coefficients are marginal log-odds effects, not analyses of raw proportions."
)
