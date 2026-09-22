"""Functionalize time-varying RQA and analyze it with the FDA core."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    fit_mfpca,
    windowed_rqa_functional_reporting_text,
    windowed_rqa_trajectory_set,
)


time = np.arange(180, dtype=float) * 0.01
curves = []
for index, phase in enumerate(np.linspace(0.0, 0.7, 6)):
    frequency = 1.7 + 0.08 * index
    curves.append(np.sin(2.0 * np.pi * frequency * time + phase))

gaze = TrajectorySet(
    time=time,
    values=np.asarray(curves)[:, :, None],
    curve_ids=tuple(f"P{index + 1:02d}" for index in range(len(curves))),
    dimension_names=("x",),
    coordinate_system="normalized",
    time_unit="s",
    provenance={"example": "synthetic periodic gaze"},
)

functional_rqa = windowed_rqa_trajectory_set(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window=60,
    step=30,
    radius=0.25,
    theiler_window=2,
    dimensions=("x",),
)

print(windowed_rqa_functional_reporting_text(functional_rqa))
print(functional_rqa.trajectories.values.shape)
print(functional_rqa.trajectories.provenance["overlap_fraction"])

fit = fit_mfpca(
    functional_rqa.trajectories,
    n_components=2,
    scaling="dimension_sd",
)
print(fit.explained_variance_ratio)
