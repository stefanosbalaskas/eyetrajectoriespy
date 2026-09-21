from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCARegressionUncertaintyResult,
    bootstrap_fpca_regression_uncertainty,
    fit_mfpca,
    fpca_regression_prediction_uncertainty_frame,
    fpca_regression_slope_uncertainty_frame,
    fpca_regression_uncertainty_reporting_text,
    plot_fpca_regression_mean_prediction_uncertainty,
    plot_fpca_regression_slope_uncertainty,
    simulate_planar_trajectories,
)


def sample():
    gaze = simulate_planar_trajectories(
        n_participants=14,
        trials_per_participant=2,
        n_time=31,
        random_state=71,
    )
    fpca = fit_mfpca(gaze, n_components=2, scaling="dimension_sd")
    outcome = 1.25 + 1.8 * fpca.scores[:, 0] - 0.65 * fpca.scores[:, 1]
    return gaze, outcome


def test_reference_slope_reconstructs_training_mean_response():
    gaze, outcome = sample()
    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        random_state=7,
    )
    assert isinstance(result, FPCARegressionUncertaintyResult)
    centered = gaze.values - result.reference_fpca.mean[None, :, :]
    contribution = np.sum(
        centered
        * result.reference_slope[None, :, :]
        * result.reference_fpca.weights[None, :, None],
        axis=(1, 2),
    )
    reconstructed = result.reference_intercept + contribution
    assert np.allclose(
        reconstructed,
        result.reference_mean_predictions,
        atol=1e-9,
    )
    assert np.allclose(
        result.reference_mean_predictions,
        outcome,
        atol=1e-9,
    )


def test_regression_bootstrap_is_reproducible_and_ordered():
    gaze, outcome = sample()
    first = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 2, 4]),
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        random_state=11,
    )
    second = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 2, 4]),
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        random_state=11,
    )
    assert first.bootstrap_slopes.shape == (20, gaze.n_time, gaze.n_dimensions)
    assert first.bootstrap_mean_predictions.shape == (20, 3)
    assert first.n_bootstrap == 20
    assert first.n_targets == 3
    assert first.target_source == "external"
    assert np.all(first.slope_lower <= first.slope_median)
    assert np.all(first.slope_median <= first.slope_upper)
    assert np.all(first.prediction_lower <= first.prediction_median)
    assert np.all(first.prediction_median <= first.prediction_upper)
    assert np.all(first.slope_se >= 0)
    assert np.all(first.prediction_se >= 0)
    assert np.allclose(first.bootstrap_slopes, second.bootstrap_slopes)
    assert np.allclose(
        first.bootstrap_mean_predictions,
        second.bootstrap_mean_predictions,
    )


def test_higher_level_is_no_narrower_under_identical_draws():
    gaze, outcome = sample()
    low = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2]),
        n_bootstrap=24,
        n_components=2,
        level=0.80,
        random_state=5,
    )
    high = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2]),
        n_bootstrap=24,
        n_components=2,
        level=0.95,
        random_state=5,
    )
    assert np.all(
        (high.slope_upper - high.slope_lower)
        >= (low.slope_upper - low.slope_lower) - 1e-12
    )
    assert np.all(
        (high.prediction_upper - high.prediction_lower)
        >= (low.prediction_upper - low.prediction_lower) - 1e-12
    )


def test_participant_paired_bootstrap_and_frames():
    gaze, outcome = sample()
    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=13,
    )
    assert result.resampling_unit == "participant"
    assert result.participant_column == "participant_id"
    assert (
        result.provenance["fpca_regression_uncertainty"][
            "future_outcome_prediction_interval"
        ]
        is False
    )
    assert (
        result.provenance["fpca_regression_uncertainty"][
            "component_selection_uncertainty_included"
        ]
        is False
    )
    slope = fpca_regression_slope_uncertainty_frame(result)
    prediction = fpca_regression_prediction_uncertainty_frame(result)
    assert len(slope) == gaze.n_time * gaze.n_dimensions
    assert len(prediction) == 4
    assert {
        "time",
        "dimension",
        "reference_slope",
        "bootstrap_median",
        "bootstrap_se",
        "lower",
        "upper",
    } == set(slope.columns)
    assert {
        "curve_id",
        "reference_mean_prediction",
        "bootstrap_median",
        "bootstrap_se",
        "lower",
        "upper",
    } == set(prediction.columns)


def test_invalid_inputs_and_target_representation_fail_explicitly():
    gaze, outcome = sample()
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome[:-1], n_bootstrap=20, n_components=2
        )
    bad_outcome = outcome.copy()
    bad_outcome[0] = np.inf
    with pytest.raises(ValueError, match="outcome must contain only finite"):
        bootstrap_fpca_regression_uncertainty(
            gaze, bad_outcome, n_bootstrap=20, n_components=2
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome, n_bootstrap=19, n_components=2
        )
    with pytest.raises(TypeError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome, n_bootstrap=True, n_components=2
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome, n_bootstrap=20, n_components=0
        )
    with pytest.raises(TypeError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome, n_bootstrap=20, n_components=True
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome, n_bootstrap=20, n_components=2, scaling="bad"
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze, outcome, n_bootstrap=20, n_components=2, level=1.0
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze,
            outcome,
            n_bootstrap=20,
            n_components=2,
            resample_unit="participant",
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_regression_uncertainty(
            gaze,
            outcome,
            n_bootstrap=20,
            n_components=2,
            resample_unit="curve",
            participant_column="participant_id",
        )

    targets = gaze.subset([0, 1])
    with pytest.raises(ValueError, match="time grid"):
        bootstrap_fpca_regression_uncertainty(
            gaze,
            outcome,
            targets=replace(targets, time=targets.time + 0.001),
            n_bootstrap=20,
            n_components=2,
        )
    infinite_values = targets.values.copy()
    infinite_values[0, 0, 0] = np.inf
    with pytest.raises(ValueError, match="targets must contain only finite"):
        bootstrap_fpca_regression_uncertainty(
            gaze,
            outcome,
            targets=replace(targets, values=infinite_values),
            n_bootstrap=20,
            n_components=2,
        )


def test_reporting_and_plots_state_inferential_boundaries():
    gaze, outcome = sample()
    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2]),
        n_bootstrap=20,
        n_components=2,
        random_state=17,
    )
    text = fpca_regression_uncertainty_reporting_text(result)
    assert "paired curve-level bootstrap refits" in text
    assert "conditional mean" in text
    assert "not prediction intervals for future noisy outcomes" in text
    assert "not reselected" in text

    assert plot_fpca_regression_slope_uncertainty(result, dimension="x") is not None
    assert plot_fpca_regression_mean_prediction_uncertainty(
        result, max_targets=3
    ) is not None
    with pytest.raises(KeyError):
        plot_fpca_regression_slope_uncertainty(result, dimension="missing")
    with pytest.raises(TypeError):
        plot_fpca_regression_mean_prediction_uncertainty(
            result, max_targets=True
        )
    with pytest.raises(ValueError):
        plot_fpca_regression_mean_prediction_uncertainty(
            result, max_targets=0
        )
    plt.close("all")
