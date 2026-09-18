from dataclasses import replace

import numpy as np
import pytest

from eyetrajectoriespy import (
    bootstrap_fpca_stability,
    component_similarity_matrix,
    fit_mfpca,
    fpca_reconstruction_curve,
    match_fpca_components,
    reconstruction_error_by_curve,
    simulate_planar_trajectories,
    summarise_fpca_stability,
)


def sample():
    return simulate_planar_trajectories(
        n_participants=8,
        trials_per_participant=3,
        n_time=41,
        random_state=14,
    )


def test_identical_components_match_identity():
    x = sample()
    fit = fit_mfpca(x, n_components=3, scaling="dimension_sd")
    matrix = component_similarity_matrix(fit, fit)
    assert np.allclose(matrix, np.eye(3), atol=1e-8)
    assignment, signed = match_fpca_components(fit, fit)
    assert np.array_equal(assignment, np.arange(3))
    assert np.allclose(signed, 1.0)


def test_component_matching_is_sign_invariant():
    x = sample()
    fit = fit_mfpca(x, n_components=3, scaling="dimension_sd")
    flipped = replace(
        fit,
        components=fit.components.copy(),
        scores=fit.scores.copy(),
    )
    flipped.components[0] *= -1
    flipped.scores[:, 0] *= -1
    assignment, signed = match_fpca_components(fit, flipped)
    assert assignment[0] == 0
    assert signed[0] == pytest.approx(-1.0)


def test_curve_bootstrap_stability_is_reproducible():
    x = sample()
    a = bootstrap_fpca_stability(
        x,
        n_bootstrap=8,
        n_components=3,
        scaling="dimension_sd",
        random_state=44,
    )
    b = bootstrap_fpca_stability(
        x,
        n_bootstrap=8,
        n_components=3,
        scaling="dimension_sd",
        random_state=44,
    )
    assert a.similarities.shape == (8, 3)
    assert np.allclose(a.similarities, b.similarities)
    assert np.array_equal(a.assignments, b.assignments)
    assert np.all((a.similarities >= 0) & (a.similarities <= 1))


def test_participant_bootstrap_preserves_clustered_resampling():
    x = sample()
    stability = bootstrap_fpca_stability(
        x,
        n_bootstrap=6,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=8,
    )
    assert stability.resampling_unit == "participant"
    assert np.all(stability.bootstrap_curve_counts > 0)
    summary = summarise_fpca_stability(stability, similarity_threshold=0.7)
    assert len(summary) == 2
    assert "fraction_at_or_above_threshold" in summary.columns


def test_reconstruction_error_improves_with_more_components():
    x = sample()
    fit = fit_mfpca(x, n_components=6, scaling="dimension_sd")
    curve = fpca_reconstruction_curve(fit, x)
    assert curve.iloc[-1]["mean_integrated_rmse"] <= curve.iloc[0]["mean_integrated_rmse"]
    by_curve = reconstruction_error_by_curve(fit, x, n_components=3)
    assert len(by_curve) == x.n_curves
    assert np.all(by_curve["integrated_rmse"] >= 0)


def test_stability_contract_errors():
    x = sample()
    with pytest.raises(ValueError):
        bootstrap_fpca_stability(x, n_bootstrap=1)
    with pytest.raises(ValueError):
        bootstrap_fpca_stability(x, resample_unit="participant")
    with pytest.raises(ValueError):
        bootstrap_fpca_stability(x, resample_unit="bad")
    fit = fit_mfpca(x, n_components=3)
    shifted = replace(fit, time=fit.time + 0.01)
    with pytest.raises(ValueError):
        component_similarity_matrix(fit, shifted)
    with pytest.raises(ValueError):
        summarise_fpca_stability(
            bootstrap_fpca_stability(x, n_bootstrap=3, n_components=2),
            similarity_threshold=1.5,
        )
