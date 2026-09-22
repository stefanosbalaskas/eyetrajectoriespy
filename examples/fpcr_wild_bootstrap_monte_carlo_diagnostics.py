"""Worked example: finite-bootstrap Monte Carlo precision diagnostics."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_diagnostics,
    fpca_wild_bootstrap_monte_carlo_diagnostic_frame,
    fpca_wild_bootstrap_monte_carlo_reporting_text,
    fpca_wild_bootstrap_projection_family_test,
    plot_fpca_wild_bootstrap_monte_carlo_diagnostics,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)

gaze = simulate_planar_trajectories(
    n_participants=48,
    trials_per_participant=1,
    n_time=31,
    random_state=2030,
)
reference = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
rng = np.random.default_rng(2030)

score1 = reference.scores[:, 0]
score2 = reference.scores[:, 1]
noise_sd = 0.25 + 0.30 * (
    np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
)
outcome = 1.0 + 1.1 * score1 - 0.4 * score2 + rng.normal(0.0, noise_sd)

base = wild_bootstrap_fpca_projection(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2]),
    n_bootstrap=100,
    residual_components=2,
    inference_components=3,
    scaling="dimension_sd",
    multiplier="normal",
    independent_unit_column="participant_id",
    random_state=2030,
)
family_test = fpca_wild_bootstrap_projection_family_test(
    base,
    null_values=0.0,
    significance_level=0.05,
    pvalue_correction="plus_one",
)
diagnostics = fpca_wild_bootstrap_family_test_monte_carlo_diagnostics(
    family_test,
    confidence_level=0.95,
)

print(fpca_wild_bootstrap_monte_carlo_diagnostic_frame(diagnostics))
print(fpca_wild_bootstrap_monte_carlo_reporting_text(diagnostics))

plot_fpca_wild_bootstrap_monte_carlo_diagnostics(
    diagnostics,
    show_targetwise=True,
)
plt.close("all")
