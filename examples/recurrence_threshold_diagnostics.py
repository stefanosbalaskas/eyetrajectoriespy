"""Inspect the exact recurrence-rate curve over a declared radius grid."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    recurrence_matrix,
    recurrence_radius_profile,
    recurrence_radius_profile_reporting_text,
)


time = np.arange(240, dtype=float) * 0.01
x = np.sin(2.0 * np.pi * 1.2 * time)
y = 0.7 * np.cos(2.0 * np.pi * 0.8 * time + 0.3)

gaze = TrajectorySet(
    time=time,
    values=np.column_stack([x, y])[None, :, :],
    curve_ids=("synthetic",),
    dimension_names=("x", "y"),
    time_unit="s",
    coordinate_system="normalized",
    provenance={"example": "recurrence threshold diagnostics"},
)

profile = recurrence_radius_profile(
    gaze,
    curve="synthetic",
    dimensions=("x", "y"),
    radii=(0.02, 0.04, 0.06, 0.08, 0.12, 0.20),
    metric="euclidean",
    theiler_window=0.05,
    theiler_window_units="seconds",
)

print(
    profile.table[
        [
            "previous_radius",
            "radius",
            "shell_pair_count",
            "shell_pair_fraction",
            "recurrence_rate",
        ]
    ]
)
print(recurrence_radius_profile_reporting_text(profile))

fixed = recurrence_matrix(
    gaze,
    curve="synthetic",
    dimensions=("x", "y"),
    radius=0.08,
    metric="euclidean",
    theiler_window=0.05,
    theiler_window_units="seconds",
)

profile_rr = float(
    profile.table.loc[
        profile.table["radius"] == 0.08,
        "recurrence_rate",
    ].iloc[0]
)

if profile_rr != fixed.achieved_recurrence_rate:
    raise RuntimeError("radius profile and base recurrence estimator disagree")

print("primary radius RR:", fixed.achieved_recurrence_rate)
