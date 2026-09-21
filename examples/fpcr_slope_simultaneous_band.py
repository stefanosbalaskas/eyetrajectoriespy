"""Worked example: observed-grid simultaneous Gaussian FPCR slope band."""

import numpy as np

from eyetrajectoriespy import (
    bootstrap_fpca_regression_uncertainty,
    fit_mfpca,
    fpca_regression_slope_band_frame,
    fpca_regression_slope_band_reporting_text,
    fpca_regression_slope_simultaneous_band,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=24,
    trials_per_participant=2,
    n_time=41,
    random_state=2026,
)
reference = fit_mfpca(gaze, n_components=2, scaling="dimension_sd")
generator = np.random.default_rng(2026)
outcome = (
    1.0
    + 1.4 * reference.scores[:, 0]
    - 0.6 * reference.scores[:, 1]
    + generator.normal(0.0, 0.35, size=gaze.n_curves)
)

paired = bootstrap_fpca_regression_uncertainty(
    gaze,
    outcome,
    n_bootstrap=100,
    n_components=2,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    random_state=2026,
)

band = fpca_regression_slope_simultaneous_band(
    paired,
    confidence_level=0.95,
    simultaneous_scope="global",
)

print(fpca_regression_slope_band_frame(band).head())
print(fpca_regression_slope_band_reporting_text(band))
