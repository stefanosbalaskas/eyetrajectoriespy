"""Executable full-refit functional mixed-effects bootstrap example."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    bootstrap_functional_mixed_effects_full_refit,
    compare_functional_mixed_effects_bootstraps,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_full_refit_audit_frame,
    functional_mixed_effects_variance_bootstrap_frame,
)

rng = np.random.default_rng(460)
n_participants = 8
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 6)
basis = np.column_stack([1.0 - time, time])
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile([-0.5, 0.0, 0.5], n_participants)
random_coefficients = rng.multivariate_normal(
    [0.0, 0.0],
    [[0.03, 0.004], [0.004, 0.02]],
    size=n_participants,
)
random_functions = random_coefficients @ basis.T
beta0 = 0.25 + 0.10 * time
beta1 = 0.15 + 0.25 * time

values = []
curve_ids = []
for participant_index in range(n_participants):
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        response = (
            beta0
            + condition[row] * beta1
            + random_functions[participant_index]
            + rng.normal(0.0, 0.035, size=time.size)
        )
        values.append(response[:, None])
        curve_ids.append(f"C{row:03d}")

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
    spline_degree=1,
    maxiter=1000,
)

full = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=20,
    random_state=46,
)
fixed = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=100,
    random_state=46,
)

audit = functional_mixed_effects_full_refit_audit_frame(full)
variance = functional_mixed_effects_variance_bootstrap_frame(full)
comparison = compare_functional_mixed_effects_bootstraps(
    fixed,
    full,
)

assert full.n_bootstrap == 20
assert len(audit) == 20 * n_participants
assert np.all(full.convergence_flags)
assert np.std(full.residual_variances) > 0
assert np.all(
    np.isfinite(
        comparison["full_refit_to_fixed_covariance_width_ratio"]
    )
)
print(variance.head())
print(comparison.head())
