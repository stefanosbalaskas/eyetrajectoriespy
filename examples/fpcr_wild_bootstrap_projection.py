"""Worked example: heteroscedastic Gaussian FPCR wild-bootstrap projections."""

import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_projection_frame,
    fpca_wild_bootstrap_projection_reporting_text,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)

gaze = simulate_planar_trajectories(
    n_participants=60,
    trials_per_participant=1,
    n_time=41,
    random_state=2026,
)
reference = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
generator = np.random.default_rng(2026)

score1 = reference.scores[:, 0]
score2 = reference.scores[:, 1]
noise_sd = 0.25 + 0.30 * (
    np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
)
outcome = (
    1.0
    + 1.2 * score1
    - 0.5 * score2
    + generator.normal(0.0, noise_sd)
)

result = wild_bootstrap_fpca_projection(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2, 3]),
    n_bootstrap=100,
    residual_components=2,
    inference_components=3,
    scaling="dimension_sd",
    multiplier="normal",
    confidence_level=0.95,
    independent_unit_column="participant_id",
    random_state=2026,
)

print(fpca_wild_bootstrap_projection_frame(result))
print(fpca_wild_bootstrap_projection_reporting_text(result))
