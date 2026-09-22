from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCAWildBootstrapProjectionResult,
    fit_mfpca,
    fpca_wild_bootstrap_projection_frame,
    fpca_wild_bootstrap_projection_reporting_text,
    plot_fpca_wild_bootstrap_projection,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)


def sample(*, trials_per_participant=1):
    gaze = simulate_planar_trajectories(
        n_participants=36,
        trials_per_participant=trials_per_participant,
        n_time=31,
        random_state=101,
    )
    fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    rng = np.random.default_rng(101)
    score1 = fpca.scores[:, 0]
    score2 = fpca.scores[:, 1]
    scale = 0.25 + 0.35 * (
        np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
    )
    outcome = (
        1.0
        + 1.1 * score1
        - 0.45 * score2
        + rng.normal(0.0, scale)
    )
    return gaze, outcome


def test_wild_projection_contract_and_reproducibility():
    gaze, outcome = sample()
    targets = gaze.subset([0, 2, 4, 6])
    first = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=targets,
        n_bootstrap=24,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        random_state=17,
    )
    second = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=targets,
        n_bootstrap=24,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        random_state=17,
    )
    assert isinstance(first, FPCAWildBootstrapProjectionResult)
    assert first.bootstrap_projections.shape == (24, 4)
    assert first.bootstrap_se.shape == (24, 4)
    assert first.studentized_roots.shape == (24, 4)
    assert first.n_bootstrap == 24
    assert first.n_targets == 4
    assert np.all(first.reference_se >= 0)
    assert np.all(first.lower <= first.reference_projection)
    assert np.all(first.reference_projection <= first.upper)
    assert np.all(np.isfinite(first.studentized_roots))
    assert np.allclose(first.bootstrap_projections, second.bootstrap_projections)
    assert np.allclose(first.bootstrap_se, second.bootstrap_se)
    assert np.allclose(first.studentized_roots, second.studentized_roots)
    settings = first.provenance["fpca_wild_bootstrap_projection"]
    assert settings["g_equals_k"] is True
    assert settings["fpca_basis_refit_in_bootstrap"] is False
    assert settings["studentization"] == (
        "bootstrap_level_heteroscedastic_score_covariance"
    )


def test_higher_confidence_is_no_narrower_with_same_bootstrap_draws():
    gaze, outcome = sample()
    low = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2]),
        n_bootstrap=24,
        residual_components=2,
        inference_components=3,
        multiplier="normal",
        confidence_level=0.80,
        random_state=29,
    )
    high = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2]),
        n_bootstrap=24,
        residual_components=2,
        inference_components=3,
        multiplier="normal",
        confidence_level=0.99,
        random_state=29,
    )
    assert np.allclose(low.studentized_roots, high.studentized_roots)
    assert np.all(
        (high.upper - high.lower)
        >= (low.upper - low.lower) - 1e-12
    )


def test_mammen_multiplier_is_supported_and_finite():
    gaze, outcome = sample()
    result = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1]),
        n_bootstrap=24,
        residual_components=2,
        inference_components=2,
        multiplier="mammen",
        random_state=31,
    )
    contract = result.provenance["fpca_wild_bootstrap_projection"][
        "multiplier_contract"
    ]
    assert result.multiplier == "mammen"
    assert contract["mean"] == 0.0
    assert contract["variance"] == 1.0
    assert contract["negative_probability"] > 0.5
    assert np.all(np.isfinite(result.studentized_roots))


def test_declared_repeated_units_are_rejected():
    gaze, outcome = sample(trials_per_participant=2)
    with pytest.raises(ValueError, match="repeated/clustered"):
        wild_bootstrap_fpca_projection(
            gaze,
            outcome,
            n_bootstrap=20,
            residual_components=2,
            inference_components=3,
            independent_unit_column="participant_id",
        )


def test_validation_target_contracts_frame_plot_and_reporting():
    gaze, outcome = sample()
    targets = gaze.subset([0, 1, 2])
    with pytest.raises(ValueError):
        wild_bootstrap_fpca_projection(
            gaze,
            outcome[:-1],
            n_bootstrap=20,
            residual_components=2,
            inference_components=3,
        )
    bad_y = outcome.copy()
    bad_y[0] = np.inf
    with pytest.raises(ValueError, match="finite"):
        wild_bootstrap_fpca_projection(
            gaze,
            bad_y,
            n_bootstrap=20,
            residual_components=2,
            inference_components=3,
        )
    with pytest.raises(ValueError, match="greater than or equal"):
        wild_bootstrap_fpca_projection(
            gaze,
            outcome,
            n_bootstrap=20,
            residual_components=3,
            inference_components=2,
        )
    with pytest.raises(ValueError, match="multiplier"):
        wild_bootstrap_fpca_projection(
            gaze,
            outcome,
            n_bootstrap=20,
            residual_components=2,
            inference_components=3,
            multiplier="rademacher",
        )
    with pytest.raises(ValueError, match="time grid"):
        wild_bootstrap_fpca_projection(
            gaze,
            outcome,
            targets=replace(targets, time=targets.time + 0.001),
            n_bootstrap=20,
            residual_components=2,
            inference_components=3,
        )

    result = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=targets,
        n_bootstrap=20,
        residual_components=2,
        inference_components=3,
        random_state=41,
    )
    frame = fpca_wild_bootstrap_projection_frame(result)
    assert len(frame) == 3
    assert {
        "curve_id",
        "reference_projection",
        "pseudo_truth_projection",
        "heteroscedastic_se",
        "critical_value",
        "lower",
        "upper",
    } == set(frame.columns)

    text = fpca_wild_bootstrap_projection_reporting_text(result)
    assert "fixed-regressor multiplier wild-bootstrap" in text
    assert "bootstrap-level heteroscedastic" in text
    assert "not future-outcome prediction intervals" in text
    assert "not clustered wild bootstrap intervals" in text

    assert plot_fpca_wild_bootstrap_projection(result, max_targets=3) is not None
    with pytest.raises(TypeError):
        plot_fpca_wild_bootstrap_projection(result, max_targets=True)
    with pytest.raises(ValueError):
        plot_fpca_wild_bootstrap_projection(result, max_targets=0)
    plt.close("all")
