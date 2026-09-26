"""Canonical experimental functional regression workflow."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_function_on_scalar_coefficients,
    fit_function_on_scalar_regression,
    function_on_scalar_reporting_text,
    function_on_scalar_simultaneous_bands,
)


rng = np.random.default_rng(571)
n_participants = 48
time = np.linspace(-0.5, 2.0, 51)
condition = np.repeat(np.array([-0.5, 0.5]), n_participants // 2)
baseline = 3.2 + 0.12 * np.exp(-((time - 0.1) / 0.35) ** 2)
condition_effect = 0.28 * np.exp(-((time - 0.9) / 0.42) ** 2)
participant_offsets = rng.normal(0.0, 0.10, size=n_participants)
values = (
    baseline[None, :]
    + condition[:, None] * condition_effect[None, :]
    + participant_offsets[:, None]
    + rng.normal(0.0, 0.045, size=(n_participants, time.size))
)

trajectories = TrajectorySet(
    time=time,
    values=values[:, :, None],
    curve_ids=tuple(f"P{i:03d}" for i in range(n_participants)),
    dimension_names=("pupil_mm",),
    metadata=pd.DataFrame(
        {
            "participant_id": [f"P{i:03d}" for i in range(n_participants)],
            "condition": condition,
        }
    ),
    coordinate_system="unknown",
    time_unit="s",
    provenance={
        "example": "canonical_experimental_functional_regression",
        "response": "stimulus-locked pupil diameter",
    },
)
design = pd.DataFrame(
    {
        "curve_id": trajectories.curve_ids,
        "condition": condition,
    }
)

fit = fit_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
    dimensions=("pupil_mm",),
    unit="curve",
)
bootstrap = bootstrap_function_on_scalar_coefficients(
    fit,
    n_bootstrap=100,
    random_state=571,
)
band = function_on_scalar_simultaneous_bands(
    bootstrap,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
print(function_on_scalar_reporting_text(fit, band=band))
print(
    "Interpretation: the condition coefficient is a time-varying difference "
    "under the declared coding; the band is simultaneous over the observed grid."
)
