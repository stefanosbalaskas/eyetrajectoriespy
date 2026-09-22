"""Finite-B precision diagnostics for fixed-family FPCR wild-bootstrap tests."""

import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_precision,
    fpca_wild_bootstrap_monte_carlo_precision_frame,
    fpca_wild_bootstrap_monte_carlo_precision_reporting_text,
    fpca_wild_bootstrap_projection_family_test,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)

gaze = simulate_planar_trajectories(
    n_participants=36,
    trials_per_participant=1,
    n_time=31,
    random_state=320,
)
fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
rng = np.random.default_rng(320)
score1 = fpca.scores[:, 0]
score2 = fpca.scores[:, 1]
scale = 0.20 + 0.20 * np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
outcome = 0.4 + 0.9 * score1 - 0.25 * score2 + rng.normal(0.0, scale)

base = wild_bootstrap_fpca_projection(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2]),
    n_bootstrap=49,
    residual_components=2,
    inference_components=3,
    scaling="dimension_sd",
    multiplier="normal",
    random_state=320,
)
family = fpca_wild_bootstrap_projection_family_test(
    base,
    significance_level=0.05,
)
precision = fpca_wild_bootstrap_family_test_monte_carlo_precision(
    family,
    confidence_level=0.95,
)

print(fpca_wild_bootstrap_monte_carlo_precision_frame(precision))
print(fpca_wild_bootstrap_monte_carlo_precision_reporting_text(precision))
