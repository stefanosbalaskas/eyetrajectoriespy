"""Worked example: bootstrap FPCA spectrum uncertainty."""

from eyetrajectoriespy import (
    bootstrap_fpca_spectrum_uncertainty,
    fpca_spectrum_uncertainty_frame,
    fpca_spectrum_uncertainty_reporting_text,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=2,
    n_time=41,
    random_state=2026,
)

spectrum = bootstrap_fpca_spectrum_uncertainty(
    gaze,
    n_bootstrap=100,
    n_components=3,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    confidence_level=0.95,
    simultaneous_scope="component",
    random_state=2026,
)

print(fpca_spectrum_uncertainty_frame(spectrum))
print(fpca_spectrum_uncertainty_reporting_text(spectrum))
