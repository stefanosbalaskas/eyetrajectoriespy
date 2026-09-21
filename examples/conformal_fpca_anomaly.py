"""Worked example: split-conformal FPCA anomaly review."""

import numpy as np

from eyetrajectoriespy import (
    conformal_fpca_anomaly_frame,
    conformal_fpca_anomaly_reporting_text,
    simulate_planar_trajectories,
    split_conformal_fpca_anomaly,
)

gaze = simulate_planar_trajectories(
    n_participants=42,
    trials_per_participant=1,
    n_time=51,
    random_state=2026,
)

proper = gaze.subset(np.arange(0, 24))
calibration = gaze.subset(np.arange(24, 36))
targets = gaze.subset(np.arange(36, 42))

values = targets.values.copy()
shape = np.where(np.arange(targets.n_time) % 2 == 0, 1.0, -1.0)
values[0, :, 0] += 8.0 * shape
targets = targets.with_values(values)

result = split_conformal_fpca_anomaly(
    proper,
    calibration,
    targets,
    n_components=3,
    scaling="dimension_sd",
    nonconformity="reconstruction_rmse",
    alpha=0.10,
)

print(conformal_fpca_anomaly_frame(result))
print(conformal_fpca_anomaly_reporting_text(result))
