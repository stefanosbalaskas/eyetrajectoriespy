"""Canonical repeated-trial functional mixed-effects workflow."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_reporting_text,
    functional_mixed_effects_simultaneous_bands,
)


rng = np.random.default_rng(572)
n_participants = 18
trials_per_participant = 3
time = np.linspace(0.0, 1.0, 7)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
condition = np.tile(np.array([-0.5, 0.0, 0.5]), n_participants)
participant_random = rng.normal(
    0.0,
    0.09,
    size=(n_participants, 1),
)
base = 0.34 + 0.08 * time
condition_effect = 0.10 + 0.16 * time

values = []
for participant_index in range(n_participants):
    for trial_index in range(trials_per_participant):
        row = participant_index * trials_per_participant + trial_index
        response = (
            base
            + condition[row] * condition_effect
            + participant_random[participant_index]
            + rng.normal(0.0, 0.035, size=time.size)
        )
        values.append(response[:, None])

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(f"T{i:03d}" for i in range(len(values))),
    dimension_names=("target_dwell_fraction",),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="unknown",
    time_unit="s",
    provenance={
        "example": "canonical_repeated_trial_mixed_effects",
        "hierarchy": "participant -> trial -> time",
    },
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
    dimension="target_dwell_fraction",
    fixed_basis_size=2,
    random_basis_size=2,
    spline_degree=1,
    reml=True,
)
bootstrap = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=100,
    random_state=572,
)
band = functional_mixed_effects_simultaneous_bands(
    bootstrap,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
print(functional_mixed_effects_reporting_text(fit, band=band))
print(
    "Interpretation: participant clustering and the functional random intercept "
    "are retained; trial rows are not treated as independent participants."
)
