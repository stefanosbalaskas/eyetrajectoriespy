"""Population bootstrap uncertainty for repeated-curve RQA metrics."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_rqa_metric_means,
    rqa_metric_mean_bootstrap_reporting_text,
)


time = np.arange(140, dtype=float) * 0.01
values = []
participants = []
for participant_index in range(8):
    for trial_index in range(2):
        phase = 0.10 * participant_index + 0.05 * trial_index
        signal = np.sin(2.0 * np.pi * 1.8 * time + phase)
        values.append(signal[:, None])
        participants.append(f"P{participant_index + 1:02d}")

gaze = TrajectorySet(
    time=time,
    values=np.asarray(values, dtype=float),
    curve_ids=tuple(f"curve-{index + 1:02d}" for index in range(len(values))),
    dimension_names=("x",),
    metadata=pd.DataFrame({"participant_id": participants}),
    time_unit="s",
    coordinate_system="normalized",
    provenance={"example": "RQA population bootstrap"},
)

result = bootstrap_rqa_metric_means(
    gaze,
    dimensions=("x",),
    metrics=("recurrence_rate", "determinism", "laminarity"),
    radius=0.18,
    theiler_window=2,
    unit="participant",
    participant_column="participant_id",
    confidence_level=0.95,
    n_bootstrap=300,
    random_state=27,
)

print(result.summary_table)
print(result.unit_table)
print(rqa_metric_mean_bootstrap_reporting_text(result))
