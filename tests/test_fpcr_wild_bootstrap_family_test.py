from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy.types import FPCAWildBootstrapFamilyTestResult
from eyetrajectoriespy.wild_testing import (
    fpca_wild_bootstrap_family_test_frame,
    fpca_wild_bootstrap_projection_family_test,
)
from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_family_test_reporting_text,
    plot_fpca_wild_bootstrap_family_test,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)


def sample_result(*, n_targets=3):
    gaze = simulate_planar_trajectories(n_participants=36, trials_per_participant=1, n_time=31, random_state=191)
    fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    rng = np.random.default_rng(191)
    score1 = fpca.scores[:, 0]
    score2 = fpca.scores[:, 1]
    scale = 0.20 + 0.25 * (np.abs(score1) / max(np.std(score1, ddof=1), 1e-8))
    outcome = 0.7 + 1.0 * score1 - 0.30 * score2 + rng.normal(0.0, scale)
    return wild_bootstrap_fpca_projection(
        gaze, outcome, targets=gaze.subset(list(range(n_targets))),
        n_bootstrap=24, residual_components=2, inference_components=3,
        scaling="dimension_sd", multiplier="normal", random_state=79,
    )


def test_hand_constructed_tail_probabilities_and_global_test():
    base = sample_result(n_targets=2)
    roots = np.array([[0.5, 0.2], [1.0, 1.5], [2.0, 0.5], [0.1, 2.5]], dtype=float)
    manual = replace(
        base, studentized_roots=roots, reference_projection=np.array([1.0, 2.0]),
        reference_se=np.array([1.0, 1.0]), bootstrap_projections=np.zeros((4, 2)),
        bootstrap_se=np.ones((4, 2)),
    )
    result = fpca_wild_bootstrap_projection_family_test(manual)
    assert isinstance(result, FPCAWildBootstrapFamilyTestResult)
    assert np.allclose(result.observed_statistics, [1.0, 2.0])
    assert np.allclose(result.max_statistics, [0.5, 1.5, 2.0, 2.5])
    assert np.allclose(result.targetwise_p_values, [0.6, 0.4])
    assert np.allclose(result.adjusted_p_values, [0.8, 0.6])
    assert result.global_statistic == pytest.approx(2.0)
    assert result.global_p_value == pytest.approx(0.6)
    assert result.global_p_value == pytest.approx(np.min(result.adjusted_p_values))
    assert np.all(result.adjusted_p_values >= result.targetwise_p_values)
    assert result.minimum_attainable_p == pytest.approx(0.2)


def test_one_target_adjusted_equals_targetwise_and_global():
    result = fpca_wild_bootstrap_projection_family_test(sample_result(n_targets=1))
    assert result.adjusted_p_values[0] == pytest.approx(result.targetwise_p_values[0])
    assert result.global_p_value == pytest.approx(result.adjusted_p_values[0])


def test_vector_null_and_alpha_only_change_decisions():
    base = sample_result(n_targets=3)
    null = np.asarray(base.reference_projection) - 0.5 * np.asarray(base.reference_se)
    low = fpca_wild_bootstrap_projection_family_test(base, null_values=null, significance_level=0.01)
    high = fpca_wild_bootstrap_projection_family_test(base, null_values=null, significance_level=0.50)
    assert np.allclose(low.observed_statistics, 0.5)
    assert np.allclose(low.targetwise_p_values, high.targetwise_p_values)
    assert np.allclose(low.adjusted_p_values, high.adjusted_p_values)
    assert low.global_p_value == pytest.approx(high.global_p_value)
    assert np.sum(high.reject_familywise) >= np.sum(low.reject_familywise)


def test_zero_se_and_validation_contracts():
    base = sample_result(n_targets=2)
    zero = replace(base, reference_se=np.array([0.0, base.reference_se[1]]))
    ok = fpca_wild_bootstrap_projection_family_test(
        zero, null_values=np.array([base.reference_projection[0], 0.0])
    )
    assert ok.observed_statistics[0] == 0.0
    with pytest.raises(RuntimeError, match="zero reference standard error"):
        fpca_wild_bootstrap_projection_family_test(zero, null_values=0.0)
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_projection_family_test(object())
    with pytest.raises(TypeError, match="significance_level"):
        fpca_wild_bootstrap_projection_family_test(base, significance_level=True)
    with pytest.raises(ValueError, match="significance_level"):
        fpca_wild_bootstrap_projection_family_test(base, significance_level=1.0)
    with pytest.raises(ValueError, match="pvalue_correction"):
        fpca_wild_bootstrap_projection_family_test(base, pvalue_correction="bad")
    with pytest.raises(TypeError, match="null_values"):
        fpca_wild_bootstrap_projection_family_test(base, null_values=True)
    with pytest.raises(ValueError, match="one value per target"):
        fpca_wild_bootstrap_projection_family_test(base, null_values=[0.0])


def test_frame_and_empirical_option():
    base = sample_result(n_targets=3)
    result = fpca_wild_bootstrap_projection_family_test(base, pvalue_correction="none")
    assert result.minimum_attainable_p == 0.0
    frame = fpca_wild_bootstrap_family_test_frame(result)
    assert len(frame) == 3
    assert "adjusted_p_value" in frame.columns
    settings = result.provenance["fpca_wild_bootstrap_family_test"]
    assert settings["bootstrap_roots_reused"] is True
    assert settings["bootstrap_rerun"] is False
    assert settings["null_enforced_bootstrap"] is False
    assert settings["strong_fwer_for_arbitrary_subset_nulls_claimed"] is False
    text = fpca_wild_bootstrap_family_test_reporting_text(result)
    assert "single-step max-|t| adjusted" in text
    assert "No second bootstrap was run" in text
    assert "subset-pivotality" in text
    assert plot_fpca_wild_bootstrap_family_test(result, max_targets=3) is not None
    assert plot_fpca_wild_bootstrap_family_test(result, max_targets=3, show_targetwise=False) is not None
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_family_test_frame(object())
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_family_test_reporting_text(object())
    with pytest.raises(TypeError):
        plot_fpca_wild_bootstrap_family_test(result, max_targets=True)
    with pytest.raises(TypeError):
        plot_fpca_wild_bootstrap_family_test(result, show_targetwise=1)
    plt.close("all")
