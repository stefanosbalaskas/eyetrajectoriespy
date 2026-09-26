"""Canonical nonlinear/recurrence workflow."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    recurrence_matrix,
    rqa_metrics,
    rqa_parameter_sensitivity,
    rqa_reporting_text,
)


time = np.arange(400, dtype=float)
signal = (
    np.sin(np.linspace(0.0, 18.0 * np.pi, time.size))
    + 0.18 * np.sin(np.linspace(0.0, 55.0 * np.pi, time.size))
)
trajectories = TrajectorySet(
    time=time,
    values=signal[None, :, None],
    curve_ids=("participant-01",),
    dimension_names=("gaze_speed_state",),
    coordinate_system="unknown",
    time_unit="samples",
    provenance={
        "example": "canonical_nonlinear_recurrence",
        "state": "derived scalar gaze-speed state",
    },
)

recurrence = recurrence_matrix(
    trajectories,
    curve=0,
    radius=0.22,
    theiler_window=2,
    dimensions=("gaze_speed_state",),
)
metrics = rqa_metrics(
    recurrence,
    min_diagonal_length=2,
    min_vertical_length=2,
)
print(rqa_reporting_text(recurrence, metrics))

sensitivity = rqa_parameter_sensitivity(
    trajectories,
    curve=0,
    dimensions=("gaze_speed_state",),
    embedding_dimensions=(2, 3),
    delays=(1, 2),
    theiler_windows=(1,),
    min_diagonal_lengths=(2,),
    min_vertical_lengths=(2,),
    radii=(0.18, 0.24),
)
print(f"Declared sensitivity specifications: {len(sensitivity.table)}")
print(
    "Interpretation: sensitivity exposes consequences of defensible recurrence "
    "specifications; it does not select the specification that looks best."
)
