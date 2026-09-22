"""Worked example: stabilized-volatility h selection for FPCR wild bootstrap."""

import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_truncation_reporting_text,
    fpca_wild_bootstrap_truncation_selection_frame,
    scan_wild_bootstrap_fpca_truncations,
    select_fpca_wild_bootstrap_truncation,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=64,
    trials_per_participant=1,
    n_time=41,
    random_state=2027,
)
reference = fit_mfpca(gaze, n_components=6, scaling="dimension_sd")
rng = np.random.default_rng(2027)

score1 = reference.scores[:, 0]
score2 = reference.scores[:, 1]
noise_sd = 0.20 + 0.25 * (
    np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
)
outcome = (
    0.8
    + 1.0 * score1
    - 0.4 * score2
    + rng.normal(0.0, noise_sd)
)

scan = scan_wild_bootstrap_fpca_truncations(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2]),
    candidate_components=(2, 3, 4, 5, 6),
    n_bootstrap=100,
    residual_components=2,
    scaling="dimension_sd",
    multiplier="normal",
    confidence_level=0.95,
    independent_unit_column="participant_id",
    random_state=2027,
)

# These absolute thresholds are deliberately analyst supplied. They are in the
# scalar outcome's units and should be pre-specified or justified for real data.
selection = select_fpca_wild_bootstrap_truncation(
    scan,
    width_threshold=0.15,
    center_threshold=0.10,
    stability_run=1,
    on_failure="warn",
)

print(fpca_wild_bootstrap_truncation_selection_frame(selection))
print(fpca_wild_bootstrap_truncation_reporting_text(selection))
