"""Worked example: bootstrap-calibrated simultaneous FPC bands."""

from eyetrajectoriespy import (
    bootstrap_fpca_component_bands,
    fpca_component_band_frame,
    fpca_component_band_reporting_text,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=2,
    n_time=41,
    random_state=2026,
)

bands = bootstrap_fpca_component_bands(
    gaze,
    n_bootstrap=100,
    n_components=2,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    confidence_level=0.95,
    simultaneous_scope="component",
    random_state=2026,
)

print(fpca_component_band_frame(bands).head())
print(fpca_component_band_reporting_text(bands))
