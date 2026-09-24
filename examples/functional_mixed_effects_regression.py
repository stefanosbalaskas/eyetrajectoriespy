"""Repeated-measures functional mixed-effects regression example."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_coefficient_frame,
    functional_mixed_effects_reporting_text,
    plot_functional_mixed_effects_coefficient,
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
beta_condition = 0.15 + 0.40 * time
linear_basis = np.column_stack([1.0 - time, time])
random_coefficients = rng.multivariate_normal(
    [0.0, 0.0],
    [[0.030, 0.004], [0.004, 0.020]],
    size=n_participants,
)

curves = []
curve_ids = []
for participant_index in range(n_participants):
    participant_function = (
        random_coefficients[participant_index] @ linear_basis.T
    )
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        curves.append(
            (
                beta0
                + condition[row] * beta_condition
                + participant_function
                + rng.normal(0.0, 0.04, size=time.size)
            )[:, None]
        )
        curve_ids.append(f"C{row:03d}")

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(curves),
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

table = functional_mixed_effects_coefficient_frame(fit)
assert fit.converged
assert fit.n_participants == n_participants
assert fit.n_curves == n_participants * trials_per_participant
assert table.shape[0] == 2 * time.size

ax = plot_functional_mixed_effects_coefficient(
    fit,
    coefficient="condition",
)
plt.close(ax.figure)

print(functional_mixed_effects_reporting_text(fit))
print(table.query("coefficient == 'condition'").to_string(index=False))
