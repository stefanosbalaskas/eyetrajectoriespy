"""Contracts for a B6 calibration runner, not tests of nominal coverage."""
from __future__ import annotations

import numpy as np
import pytest

from pathlib import Path
import sys

# Gallery generation invokes the pytest console script, not 'python -m pytest'.
# Explicitly add the repository root for research-only scripts imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_b6_population_calibration_grid import (
    SCENARIOS, _known_truth, _mixture_quantile, _projector, run_one,
)


def test_matched_prior_and_adversarial_designs_explicit():
    assert SCENARIOS["matched_rank1"]["rank"] == 1
    assert SCENARIOS["matched_rank2"]["rank"] == 2
    assert SCENARIOS["unequal_sparse_rank2"]["sparse"]
    assert SCENARIOS["nearly_tied_rank2"]["mode"] == "near_tie"
    assert (SCENARIOS["noise_misspecified_rank2"]["generated_noise"] !=
            SCENARIOS["noise_misspecified_rank2"]["fitted_noise"])
    assert (SCENARIOS["prior_misspecified_rank2"]["generating_loading_prior"] !=
            SCENARIOS["prior_misspecified_rank2"]["fitted_loading_prior"])


def test_near_tie_is_exact_on_grid_and_rotation_invariant():
    gaze, true_mean, true_cov, indices, holdout = _known_truth(
        581, "nearly_tied_rank2")
    eigenvalues = np.linalg.eigvalsh(true_cov)
    nonzero = eigenvalues[-2:]
    np.testing.assert_allclose(nonzero[0], nonzero[1], rtol=1e-10)
    assert len(gaze.time) == 24 and len(indices) == len(holdout) == 5
    assert len(set(gaze.metadata.participant_id)) == gaze.n_curves
    rng = np.random.default_rng(19)
    factor = rng.normal(size=(9, 2))
    theta = .6
    rot = np.array([[np.cos(theta), -np.sin(theta)],
                    [np.sin(theta), np.cos(theta)]])
    np.testing.assert_allclose(_projector(factor @ factor.T, 2),
                               _projector((factor @ rot) @ (factor @ rot).T, 2),
                               atol=1e-10)


def test_deterministic_predictive_mixture_quantile():
    from scipy.stats import norm
    mean = np.array([.35, .35])
    sd = np.array([.4, .4])
    np.testing.assert_allclose(
        _mixture_quantile(mean, sd, .05), norm.ppf(.05, loc=.35, scale=.4),
        atol=1e-11)
    np.testing.assert_allclose(
        _mixture_quantile(mean, sd, .95), norm.ppf(.95, loc=.35, scale=.4),
        atol=1e-11)
    with pytest.raises(ValueError):
        _mixture_quantile(mean, np.array([0., .4]), .5)


def test_one_actual_rank2_refit_and_heldout_participant():
    row = run_one(10331, "matched_rank2", draws=20, warmup=25)
    assert row["n_components"] == 2
    assert row["n_chains"] == 2
    assert row["n_independent_train_units"] == 22
    assert row["holdout_marginal_n"] == 5
    assert 0 <= row["holdout_marginal_90_included"] <= 5
    assert np.isfinite(row["rotation_invariant_subspace_projector_error"])
    assert row["rotation_invariant_subspace_projector_error"] >= 0
    assert isinstance(row["population_mean_mid_90_included"], bool)
    assert isinstance(row["population_covariance_mid_90_included"], bool)
