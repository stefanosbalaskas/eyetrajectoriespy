"""Worked example: fixed-family FPCR wild-bootstrap hypothesis tests."""

import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_family_test_frame,
    fpca_wild_bootstrap_family_test_reporting_text,
    fpca_wild_bootstrap_projection_family_test,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)

gaze = simulate_planar_trajectories(
    n_participants=60,
    trials_per_participant=1,
    n_time=41,
    random_state=2029,
)
reference = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
rng = np.random.default_rng(2029)

score1 = reference.scores[:, 0]
score2 = reference.scores[:, 1]
noise_sd = 0.25 + 0.30 * (
    np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
)
outcome = 1.0 + 1.2 * score1 - 0.5 * score2 + rng.normal(0.0, noise_sd)

base = wild_bootstrap_fpca_projection(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2, 3]),
    n_bootstrap=100,
    residual_components=2,
    inference_components=3,
    scaling="dimension_sd",
    multiplier="normal",
    independent_unit_column="participant_id",
    random_state=2029,
)

tests = fpca_wild_bootstrap_projection_family_test(
    base,
    null_values=0.0,
    significance_level=0.05,
    pvalue_correction="plus_one",
)

print(fpca_wild_bootstrap_family_test_frame(tests))
print(fpca_wild_bootstrap_family_test_reporting_text(tests))
