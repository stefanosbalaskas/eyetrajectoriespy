"""Canonical FPCA workflow: continuous two-dimensional gaze exploration."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    fit_mfpca,
    fpca_reporting_text,
)


rng = np.random.default_rng(570)
n_participants = 24
trials_per_participant = 2
time = np.linspace(0.0, 2.0, 61)
participants = np.repeat(
    [f"P{i:02d}" for i in range(n_participants)],
    trials_per_participant,
)
conditions = np.tile(np.array(["baseline", "visual-search"]), n_participants)

values = []
for participant_index in range(n_participants):
    participant_shift = rng.normal(0.0, 0.08, size=2)
    for condition in ("baseline", "visual-search"):
        search = float(condition == "visual-search")
        x = (
            0.50
            + participant_shift[0]
            + 0.16 * np.sin(np.pi * time)
            + search * 0.08 * np.sin(2.0 * np.pi * time)
            + rng.normal(0.0, 0.018, size=time.size)
        )
        y = (
            0.48
            + participant_shift[1]
            + 0.12 * np.cos(np.pi * time)
            - search * 0.06 * np.sin(2.0 * np.pi * time)
            + rng.normal(0.0, 0.018, size=time.size)
        )
        values.append(np.column_stack((x, y)))

trajectories = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(f"G{i:03d}" for i in range(len(values))),
    dimension_names=("x_norm", "y_norm"),
    metadata=pd.DataFrame(
        {
            "participant_id": participants,
            "condition": conditions,
        }
    ),
    coordinate_system="normalized",
    time_unit="s",
    provenance={
        "example": "canonical_fpca",
        "interpolation": False,
        "smoothing": False,
    },
)

fit = fit_mfpca(
    trajectories,
    n_components=0.90,
    scaling="dimension_sd",
)
print(fpca_reporting_text(fit))
print(
    "Interpretation: retained components summarize dominant continuous gaze "
    "variation; component signs are arbitrary and are not substantive."
)
