"""Executable simultaneous functional mixed-effects inference example."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_simultaneous_bands,
)

rng = np.random.default_rng(2026)
n_participants = 12
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 9)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile([0.0, 1.0, 0.5], n_participants)
beta0 = 0.20 + 0.15 * time
beta1 = 0.15 + 0.40 * time
basis = np.column_stack([1.0 - time, time])
random_coefficients = rng.multivariate_normal(
    [0.0, 0.0],
    [[0.030, 0.004], [0.004, 0.020]],
    size=n_participants,
)

values = []
curve_ids = []
for participant_index in range(n_participants):
    random_function = random_coefficients[participant_index] @ basis.T
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        values.append(
            (
                beta0
                + condition[row] * beta1
                + random_function
                + rng.normal(0.0, 0.04, size=time.size)
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
)
boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=120,
    random_state=44,
)
band = functional_mixed_effects_simultaneous_bands(boot)

assert boot.n_bootstrap == 120
assert boot.n_participants == n_participants
assert band.simultaneous_scope == "coefficient"
assert np.all(band.lower < fit.coefficient_functions)
assert np.all(fit.coefficient_functions < band.upper)
assert (
    boot.provenance["functional_mixed_effects_bootstrap"]["resampling_unit"]
    == "participant"
)

print(band.critical_values)
print(boot.bootstrap_standard_errors)
