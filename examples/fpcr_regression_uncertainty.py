"""Worked example: paired-bootstrap Gaussian FPCR uncertainty."""

import numpy as np

from eyetrajectoriespy import (
    bootstrap_fpca_regression_uncertainty,
    fit_mfpca,
    fpca_regression_prediction_uncertainty_frame,
    fpca_regression_slope_uncertainty_frame,
    fpca_regression_uncertainty_reporting_text,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=24,
    trials_per_participant=2,
    n_time=41,
    random_state=2026,
)

generator = np.random.default_rng(2026)
reference = fit_mfpca(
    gaze,
    n_components=2,
    scaling="dimension_sd",
)
outcome = (
    1.0
    + 1.4 * reference.scores[:, 0]
    - 0.6 * reference.scores[:, 1]
    + generator.normal(0.0, 0.35, size=gaze.n_curves)
)

uncertainty = bootstrap_fpca_regression_uncertainty(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2, 3, 4, 5]),
    n_bootstrap=100,
    n_components=2,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    level=0.95,
    random_state=2026,
)

print(fpca_regression_slope_uncertainty_frame(uncertainty).head())
print(fpca_regression_prediction_uncertainty_frame(uncertainty))
print(fpca_regression_uncertainty_reporting_text(uncertainty))
