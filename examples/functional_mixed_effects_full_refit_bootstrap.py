"""Executable full-refit participant bootstrap example."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_full_refit,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_bootstrap_identity_frame,
    functional_mixed_effects_variance_bootstrap_frame,
)

rng = np.random.default_rng(46)
n_participants = 20
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 5)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile([-0.75, 0.0, 0.75], n_participants)

beta0 = 0.25 + 0.10 * time
beta1 = 0.20 + 0.25 * time
linear_basis = np.column_stack([1.0 - time, time])
random_coefficients = rng.multivariate_normal(
    [0.0, 0.0],
    [[0.045, 0.008], [0.008, 0.035]],
    size=n_participants,
)
random_functions = random_coefficients @ linear_basis.T

values = []
curve_ids = []
for participant_index in range(n_participants):
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        values.append(
            (
                beta0
                + condition[row] * beta1
                + random_functions[participant_index]
                + rng.normal(0.0, 0.035, size=time.size)
            )[:, None]
        )
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
    reml=True,
    method="lbfgs",
    maxiter=1000,
)

boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=100,
    random_state=46,
)

identity = functional_mixed_effects_bootstrap_identity_frame(boot)
variance = functional_mixed_effects_variance_bootstrap_frame(boot)

assert boot.n_bootstrap == 100
assert boot.provenance[
    "functional_mixed_effects_full_refit_bootstrap"
]["variance_components_refit"] is True
assert (
    identity.groupby("replicate")["bootstrap_participant_id"]
    .nunique()
    .eq(n_participants)
    .all()
)
assert np.all(variance["converged"])
assert len(variance) == 100

print(variance["residual_variance"].describe())
