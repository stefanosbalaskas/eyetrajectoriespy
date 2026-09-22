import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCAWildBootstrapSimultaneousResult,
    fit_mfpca,
    fpca_wild_bootstrap_projection_simultaneous_interval,
    fpca_wild_bootstrap_simultaneous_frame,
    fpca_wild_bootstrap_simultaneous_reporting_text,
    plot_fpca_wild_bootstrap_simultaneous_interval,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)


def sample_result(*, n_targets=4, confidence_level=0.95):
    gaze = simulate_planar_trajectories(
        n_participants=36,
        trials_per_participant=1,
        n_time=31,
        random_state=181,
    )
    fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    rng = np.random.default_rng(181)
    score1 = fpca.scores[:, 0]
    score2 = fpca.scores[:, 1]
    scale = 0.20 + 0.30 * (
        np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
    )
    outcome = 0.8 + 0.9 * score1 - 0.35 * score2 + rng.normal(0.0, scale)
    return wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset(list(range(n_targets))),
        n_bootstrap=24,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=confidence_level,
        random_state=73,
    )


def test_familywise_calibration_contract_and_width_dominance():
    base = sample_result(n_targets=4)
    result = fpca_wild_bootstrap_projection_simultaneous_interval(base)
    assert isinstance(result, FPCAWildBootstrapSimultaneousResult)
    assert result.n_bootstrap == base.n_bootstrap
    assert result.n_targets == base.n_targets
    assert result.max_statistics.shape == (base.n_bootstrap,)
    assert result.targetwise_critical_values.shape == (base.n_targets,)
    assert result.critical_value >= np.max(result.targetwise_critical_values) - 1e-12
    targetwise_width = 2.0 * result.targetwise_critical_values * base.reference_se
    simultaneous_width = result.upper - result.lower
    assert np.all(simultaneous_width >= targetwise_width - 1e-12)
    settings = result.provenance["fpca_wild_bootstrap_simultaneous"]
    assert settings["bootstrap_roots_reused"] is True
    assert settings["bootstrap_rerun"] is False
    assert settings["simultaneous_across_targets"] is True


def test_single_target_exactly_matches_targetwise_calibration():
    base = sample_result(n_targets=1)
    result = fpca_wild_bootstrap_projection_simultaneous_interval(base)
    assert result.critical_value == pytest.approx(result.targetwise_critical_values[0])
    expected_lower = base.reference_projection - result.targetwise_critical_values * base.reference_se
    expected_upper = base.reference_projection + result.targetwise_critical_values * base.reference_se
    assert np.allclose(result.lower, expected_lower)
    assert np.allclose(result.upper, expected_upper)


def test_recalibration_is_monotone_and_does_not_mutate_base_roots():
    base = sample_result(n_targets=3, confidence_level=0.80)
    roots_before = base.studentized_roots.copy()
    low = fpca_wild_bootstrap_projection_simultaneous_interval(base, confidence_level=0.80)
    high = fpca_wild_bootstrap_projection_simultaneous_interval(base, confidence_level=0.99)
    assert high.critical_value >= low.critical_value
    assert np.all((high.upper - high.lower) >= (low.upper - low.lower) - 1e-12)
    assert np.array_equal(base.studentized_roots, roots_before)


def test_frame_plot_reporting_and_validation():
    base = sample_result(n_targets=3)
    result = fpca_wild_bootstrap_projection_simultaneous_interval(base)
    frame = fpca_wild_bootstrap_simultaneous_frame(result)
    assert len(frame) == 3
    assert {
        "curve_id",
        "reference_projection",
        "heteroscedastic_se",
        "targetwise_critical_value",
        "familywise_critical_value",
        "targetwise_lower",
        "targetwise_upper",
        "simultaneous_lower",
        "simultaneous_upper",
    } == set(frame.columns)

    text = fpca_wild_bootstrap_simultaneous_reporting_text(result)
    assert "familywise simultaneous interval" in text
    assert "maximum absolute studentized root" in text
    assert "not future-outcome prediction intervals" in text

    assert plot_fpca_wild_bootstrap_simultaneous_interval(result, max_targets=3) is not None
    assert plot_fpca_wild_bootstrap_simultaneous_interval(
        result, max_targets=3, show_targetwise=False
    ) is not None
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_projection_simultaneous_interval(object())
    with pytest.raises(ValueError, match="confidence_level"):
        fpca_wild_bootstrap_projection_simultaneous_interval(base, confidence_level=1.0)
    with pytest.raises(TypeError):
        plot_fpca_wild_bootstrap_simultaneous_interval(result, max_targets=True)
    with pytest.raises(TypeError):
        plot_fpca_wild_bootstrap_simultaneous_interval(result, show_targetwise=1)
    plt.close("all")
