"""Executable 0.47 mixed-effects residual-diagnostics example."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_residual_diagnostic_frame,
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_residual_pair_frame,
    functional_mixed_effects_residual_reporting_text,
)


rng = np.random.default_rng(47)
n_participants = 12
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 9)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile(np.array([0.0, 1.0, 0.5]), n_participants)

intercept = 0.20 + 0.15 * time
condition_effect = 0.15 + 0.40 * time
basis = np.column_stack([1.0 - time, time])
covariance = np.array([[0.030, 0.004], [0.004, 0.020]])
random_coefficients = rng.multivariate_normal(
    np.zeros(2),
    covariance,
    size=n_participants,
)

values = []
curve_ids = []
for participant_index in range(n_participants):
    participant_function = random_coefficients[participant_index] @ basis.T
    for trial_index in range(trials_per_participant):
        curve_index = participant_index * trials_per_participant + trial_index
        curve_ids.append(f"C{curve_index:03d}")

        # Add an explicit short-range residual component only so the diagnostic
        # example has a visible target; no covariance model is fitted to it.
        innovation = rng.normal(0.0, 0.035, size=time.size)
        serial = innovation.copy()
        serial[1:] += 0.55 * innovation[:-1]

        response = (
            intercept
            + condition[curve_index] * condition_effect
            + participant_function
            + serial
        )
        values.append(response[:, None])

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
    spline_degree=1,
)

diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=3,
)
overall = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="overall",
)
pairs = functional_mixed_effects_residual_pair_frame(
    diagnostics,
    lag_index=1,
    curve_id=fit.source_curve_ids[0],
)

assert len(overall) == 4
assert len(pairs) == time.size - 1
assert diagnostics.provenance[
    "functional_mixed_effects_residual_diagnostics"
]["automatic_covariance_structure_selection"] is False

print(
    overall[
        [
            "lag_index",
            "lag_time_mean",
            "autocorrelation",
            "semivariance",
        ]
    ].to_string(index=False)
)
print(functional_mixed_effects_residual_reporting_text(diagnostics))
