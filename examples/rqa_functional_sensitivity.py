"""Window/step sensitivity and participant-level functional RQA inference."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    windowed_rqa_functional_mean_band,
    windowed_rqa_mean_band_reporting_text,
    windowed_rqa_sensitivity,
    windowed_rqa_sensitivity_reporting_text,
)


time = np.arange(180, dtype=float) * 0.01
values = []
participants = []
curve_ids = []
for participant_index in range(6):
    participant_id = f"P{participant_index + 1:02d}"
    for trial in range(2):
        phase = 0.18 * participant_index + 0.08 * trial
        signal = (
            np.sin(2.0 * np.pi * 1.7 * time + phase)
            + 0.12 * np.sin(2.0 * np.pi * 0.55 * time + 0.4 * phase)
        )
        values.append(signal)
        participants.append(participant_id)
        curve_ids.append(f"{participant_id}_T{trial + 1}")

gaze = TrajectorySet(
    time=time,
    values=np.asarray(values, dtype=float)[:, :, None],
    curve_ids=tuple(curve_ids),
    dimension_names=("x",),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="normalized",
    time_unit="s",
    provenance={"example": "functional RQA sensitivity"},
)

sensitivity = windowed_rqa_sensitivity(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window_step_pairs=((40, 20), (40, 10), (60, 20)),
    radius=0.35,
    theiler_window=2,
    dimensions=("x",),
)

print(
    sensitivity.design_table[
        [
            "specification_id",
            "window_samples",
            "step_samples",
            "overlap_fraction",
            "profile_grid_spacing_time",
            "fraction_analyzed_samples_reused",
            "max_window_memberships",
        ]
    ]
)
print(windowed_rqa_sensitivity_reporting_text(sensitivity))

band = windowed_rqa_functional_mean_band(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window=40,
    step=20,
    unit="participant",
    participant_column="participant_id",
    radius=0.35,
    theiler_window=2,
    dimensions=("x",),
    confidence_level=0.95,
    n_multiplier=100,
    random_state=20260923,
)

print(windowed_rqa_mean_band_reporting_text(band))
print(band.band.mean.shape, band.band.n_units)
