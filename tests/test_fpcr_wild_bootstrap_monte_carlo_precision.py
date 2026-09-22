from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy.stats import beta

from eyetrajectoriespy import (
    FPCAWildBootstrapMonteCarloPrecisionResult,
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_precision,
    fpca_wild_bootstrap_monte_carlo_precision_frame,
    fpca_wild_bootstrap_monte_carlo_precision_reporting_text,
    fpca_wild_bootstrap_projection_family_test,
    plot_fpca_wild_bootstrap_monte_carlo_precision,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)


def sample_result(*, n_targets=2):
    gaze = simulate_planar_trajectories(
        n_participants=36,
        trials_per_participant=1,
        n_time=31,
        random_state=202,
    )
    fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    rng = np.random.default_rng(202)
    score1 = fpca.scores[:, 0]
    score2 = fpca.scores[:, 1]
    scale = 0.20 + 0.25 * (
        np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
    )
    outcome = 0.5 + 0.9 * score1 - 0.25 * score2 + rng.normal(0.0, scale)
    return wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset(list(range(n_targets))),
        n_bootstrap=24,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        random_state=83,
    )


def manual_family_test():
    base = sample_result(n_targets=2)
    roots = np.array(
        [[0.5, 0.2], [1.0, 1.5], [2.0, 0.5], [0.1, 2.5]],
        dtype=float,
    )
    manual = replace(
        base,
        studentized_roots=roots,
        reference_projection=np.array([1.0, 2.0]),
        reference_se=np.array([1.0, 1.0]),
        bootstrap_projections=np.zeros((4, 2)),
        bootstrap_se=np.ones((4, 2)),
    )
    return fpca_wild_bootstrap_projection_family_test(manual)


def test_hand_constructed_counts_probabilities_mcse_and_exact_intervals():
    family = manual_family_test()
    target_p_before = family.targetwise_p_values.copy()
    adjusted_p_before = family.adjusted_p_values.copy()
    global_p_before = family.global_p_value

    result = fpca_wild_bootstrap_family_test_monte_carlo_precision(family)

    assert isinstance(result, FPCAWildBootstrapMonteCarloPrecisionResult)
    assert np.array_equal(result.targetwise_exceedances, [2, 1])
    assert np.array_equal(result.adjusted_exceedances, [3, 2])
    assert result.global_exceedances == 2
    assert np.allclose(result.targetwise_tail_probabilities, [0.5, 0.25])
    assert np.allclose(result.adjusted_tail_probabilities, [0.75, 0.5])
    assert result.global_tail_probability == pytest.approx(0.5)
    assert np.allclose(
        result.targetwise_mcse,
        [0.25, np.sqrt(0.25 * 0.75 / 4.0)],
    )
    assert result.global_mcse == pytest.approx(0.25)

    expected_lower_first = beta.ppf(0.025, 2, 3)
    expected_upper_first = beta.ppf(0.975, 3, 2)
    assert result.targetwise_ci_lower[0] == pytest.approx(expected_lower_first)
    assert result.targetwise_ci_upper[0] == pytest.approx(expected_upper_first)

    assert np.array_equal(family.targetwise_p_values, target_p_before)
    assert np.array_equal(family.adjusted_p_values, adjusted_p_before)
    assert family.global_p_value == global_p_before
    assert result.pvalue_grid_step == pytest.approx(0.2)
    assert result.alpha_resolvable is False


def test_boundary_counts_have_exact_non_degenerate_intervals():
    family = manual_family_test()
    extreme = replace(
        family,
        observed_statistics=np.array([10.0, 10.0]),
        global_statistic=10.0,
    )
    low = fpca_wild_bootstrap_family_test_monte_carlo_precision(extreme)
    assert np.array_equal(low.targetwise_exceedances, [0, 0])
    assert np.all(low.targetwise_ci_lower == 0.0)
    assert np.all(low.targetwise_ci_upper > 0.0)
    assert np.all(low.targetwise_mcse == 0.0)
    assert all(x == "overlaps_alpha" for x in low.targetwise_alpha_relation)

    base = family.projection_result
    zero = fpca_wild_bootstrap_projection_family_test(
        base,
        null_values=base.reference_projection,
    )
    high = fpca_wild_bootstrap_family_test_monte_carlo_precision(zero)
    assert np.array_equal(high.targetwise_exceedances, [4, 4])
    assert np.all(high.targetwise_ci_upper == 1.0)
    assert np.all(high.targetwise_ci_lower > 0.0)
    assert all(x == "above_alpha" for x in high.targetwise_alpha_relation)


def test_alpha_relation_and_resolution_follow_declared_test_alpha():
    family = manual_family_test()
    result = fpca_wild_bootstrap_family_test_monte_carlo_precision(family)
    assert result.targetwise_alpha_relation == ("above_alpha", "overlaps_alpha")
    assert result.adjusted_alpha_relation == ("above_alpha", "above_alpha")
    assert result.global_alpha_relation == "above_alpha"

    alpha_25 = replace(
        family,
        significance_level=0.25,
        reject_targetwise=np.asarray(family.targetwise_p_values <= 0.25),
        reject_familywise=np.asarray(family.adjusted_p_values <= 0.25),
        reject_global=bool(family.global_p_value <= 0.25),
    )
    looser = fpca_wild_bootstrap_family_test_monte_carlo_precision(alpha_25)
    assert looser.alpha_resolvable is True
    assert looser.pvalue_grid_step == pytest.approx(0.2)


def test_frame_reporting_plot_and_provenance_contracts():
    family = manual_family_test()
    result = fpca_wild_bootstrap_family_test_monte_carlo_precision(
        family,
        confidence_level=0.90,
    )
    frame = fpca_wild_bootstrap_monte_carlo_precision_frame(result)
    assert len(frame) == 2
    assert {
        "targetwise_exceedances",
        "adjusted_exceedances",
        "adjusted_ci_lower",
        "adjusted_ci_upper",
        "adjusted_alpha_relation",
        "global_alpha_relation",
    } <= set(frame.columns)

    settings = result.provenance["fpca_wild_bootstrap_monte_carlo_precision"]
    assert settings["interval_method"] == "clopper_pearson_exact_binomial"
    assert settings["reported_p_values_changed"] is False
    assert settings["bootstrap_roots_reused"] is True
    assert settings["bootstrap_rerun"] is False
    assert settings["alpha_relation_is_diagnostic_only"] is True
    assert settings["additional_familywise_error_guarantee"] is False

    text = fpca_wild_bootstrap_monte_carlo_precision_reporting_text(result)
    assert "Clopper-Pearson" in text
    assert "do not change the reported p-values" in text
    assert "simulation uncertainty" in text

    assert plot_fpca_wild_bootstrap_monte_carlo_precision(result) is not None
    assert (
        plot_fpca_wild_bootstrap_monte_carlo_precision(
            result,
            probability="targetwise",
        )
        is not None
    )
    plt.close("all")


def test_validation_contracts():
    family = manual_family_test()
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_family_test_monte_carlo_precision(object())
    with pytest.raises(TypeError, match="confidence_level"):
        fpca_wild_bootstrap_family_test_monte_carlo_precision(
            family,
            confidence_level=True,
        )
    with pytest.raises(ValueError, match="confidence_level"):
        fpca_wild_bootstrap_family_test_monte_carlo_precision(
            family,
            confidence_level=1.0,
        )

    bad_roots = replace(
        family.projection_result,
        studentized_roots=np.ones((3, 2)),
    )
    with pytest.raises(ValueError, match="studentized_roots shape"):
        fpca_wild_bootstrap_family_test_monte_carlo_precision(
            replace(family, projection_result=bad_roots)
        )

    bad_observed = replace(family, observed_statistics=np.array([np.nan, 1.0]))
    with pytest.raises(ValueError, match="observed_statistics"):
        fpca_wild_bootstrap_family_test_monte_carlo_precision(bad_observed)

    result = fpca_wild_bootstrap_family_test_monte_carlo_precision(family)
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_monte_carlo_precision_frame(object())
    with pytest.raises(TypeError):
        fpca_wild_bootstrap_monte_carlo_precision_reporting_text(object())
    with pytest.raises(TypeError):
        plot_fpca_wild_bootstrap_monte_carlo_precision(object())
    with pytest.raises(TypeError, match="max_targets"):
        plot_fpca_wild_bootstrap_monte_carlo_precision(result, max_targets=True)
    with pytest.raises(ValueError, match="max_targets"):
        plot_fpca_wild_bootstrap_monte_carlo_precision(result, max_targets=0)
    with pytest.raises(ValueError, match="probability"):
        plot_fpca_wild_bootstrap_monte_carlo_precision(
            result,
            probability="bad",
        )
