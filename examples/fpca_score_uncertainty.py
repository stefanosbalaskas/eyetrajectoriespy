"""Worked example: basis-resampling uncertainty for FPC scores."""

from eyetrajectoriespy import (
    bootstrap_fpca_score_uncertainty,
    fpca_score_uncertainty_frame,
    fpca_score_uncertainty_reporting_text,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=2,
    n_time=41,
    random_state=2026,
)

targets = gaze.subset([0, 1, 2, 3, 4, 5])

uncertainty = bootstrap_fpca_score_uncertainty(
    gaze,
    targets=targets,
    n_bootstrap=100,
    n_components=2,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    level=0.95,
    random_state=2026,
)

print(fpca_score_uncertainty_frame(uncertainty))
print(fpca_score_uncertainty_reporting_text(uncertainty))
