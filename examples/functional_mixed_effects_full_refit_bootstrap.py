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
n_participants = 5
trials_per_participant = 2
time = np.linspace(0.0, 1.0, 4)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile([-0.5, 0.5], n_participants)
beta0 = 0.2 + 0.1 * time
beta1 = 0.15 + 0.2 * time
random_intercepts = rng.normal(0.0, 0.08, size=n_participants)

values = []
curve_ids = []
for participant_index in range(n_participants):
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        values.append(
            (
                beta0
                + condition[row] * beta1
                + random_intercepts[participant_index]
                + rng.normal(0.0, 0.025, size=time.size)
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
    fixed_basis_size=1,
    random_basis_size=1,
    spline_degree=0,
    reml=False,
    method="lbfgs",
    maxiter=500,
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
assert len(variance) == 100

print(variance["residual_variance"].describe())
