import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCARegressionPredictionIntervalResult,
    bootstrap_fpca_regression_uncertainty,
    fit_mfpca,
    fpca_regression_future_prediction_frame,
    fpca_regression_future_prediction_interval,
    fpca_regression_future_prediction_reporting_text,
    plot_fpca_regression_future_prediction_interval,
    simulate_planar_trajectories,
)


def sample():
    gaze = simulate_planar_trajectories(
        n_participants=18,
        trials_per_participant=2,
        n_time=31,
        random_state=91,
    )
    fpca = fit_mfpca(gaze, n_components=2, scaling="dimension_sd")
    rng = np.random.default_rng(91)
    outcome = (
        1.0
        + 1.2 * fpca.scores[:, 0]
        - 0.55 * fpca.scores[:, 1]
        + rng.normal(0.0, 0.7, size=gaze.n_curves)
    )
    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 2, 4, 6]),
        n_bootstrap=24,
        n_components=2,
        scaling="dimension_sd",
        random_state=23,
    )
    return gaze, outcome, result


def test_prediction_interval_reproducible_and_auditable():
    _, outcome, regression = sample()
    first = fpca_regression_future_prediction_interval(
        regression,
        outcome,
        confidence_level=0.95,
        random_state=5,
    )
    second = fpca_regression_future_prediction_interval(
        regression,
        outcome,
        confidence_level=0.95,
        random_state=5,
    )
    assert isinstance(first, FPCARegressionPredictionIntervalResult)
    assert first.predictive_draws.shape == (
        regression.n_bootstrap,
        len(regression.target_curve_ids),
    )
    assert first.sampled_residuals.shape == first.predictive_draws.shape
    assert first.n_bootstrap == regression.n_bootstrap
    assert first.n_targets == len(regression.target_curve_ids)
    assert np.allclose(
        first.predictive_draws,
        regression.bootstrap_mean_predictions + first.sampled_residuals,
    )
    assert np.isclose(first.centered_residuals.mean(), 0.0, atol=1e-12)
    assert np.all(first.lower <= first.median)
    assert np.all(first.median <= first.upper)
    assert np.all(first.predictive_se >= 0)
    assert np.allclose(first.predictive_draws, second.predictive_draws)
    assert (
        first.provenance["fpca_regression_future_prediction_interval"][
            "heteroscedasticity_robust"
        ]
        is False
    )


def test_higher_confidence_is_no_narrower_under_same_draws():
    _, outcome, regression = sample()
    low = fpca_regression_future_prediction_interval(
        regression,
        outcome,
        confidence_level=0.80,
        random_state=17,
    )
    high = fpca_regression_future_prediction_interval(
        regression,
        outcome,
        confidence_level=0.99,
        random_state=17,
    )
    assert np.allclose(low.predictive_draws, high.predictive_draws)
    assert np.all(
        (high.upper - high.lower)
        >= (low.upper - low.lower) - 1e-12
    )


def test_future_interval_adds_response_noise_to_mean_distribution():
    _, outcome, regression = sample()
    prediction = fpca_regression_future_prediction_interval(
        regression,
        outcome,
        random_state=13,
    )
    mean_width = regression.prediction_upper - regression.prediction_lower
    future_width = prediction.upper - prediction.lower
    assert float(np.median(future_width)) > float(np.median(mean_width))
    assert np.std(prediction.centered_residuals, ddof=1) > 0


def test_validation_frame_plot_and_reporting():
    _, outcome, regression = sample()
    with pytest.raises(TypeError):
        fpca_regression_future_prediction_interval(object(), outcome)
    with pytest.raises(ValueError):
        fpca_regression_future_prediction_interval(
            regression, outcome[:-1]
        )
    bad = outcome.copy()
    bad[0] = np.inf
    with pytest.raises(ValueError, match="finite"):
        fpca_regression_future_prediction_interval(regression, bad)
    with pytest.raises(ValueError):
        fpca_regression_future_prediction_interval(
            regression, outcome, confidence_level=1.0
        )
    with pytest.raises(ValueError):
        fpca_regression_future_prediction_interval(
            regression, outcome, residual_method="wild"
        )

    prediction = fpca_regression_future_prediction_interval(
        regression,
        outcome,
        random_state=29,
    )
    frame = fpca_regression_future_prediction_frame(prediction)
    assert len(frame) == prediction.n_targets
    assert {
        "curve_id",
        "reference_mean_prediction",
        "mean_response_lower",
        "mean_response_upper",
        "future_prediction_median",
        "future_prediction_se",
        "future_prediction_lower",
        "future_prediction_upper",
    } == set(frame.columns)

    text = fpca_regression_future_prediction_reporting_text(prediction)
    assert "future" in text.lower()
    assert "not heteroscedasticity-robust" in text
    assert "not simultaneous or joint" in text

    assert plot_fpca_regression_future_prediction_interval(
        prediction, max_targets=3
    ) is not None
    with pytest.raises(TypeError):
        plot_fpca_regression_future_prediction_interval(
            prediction, max_targets=True
        )
    with pytest.raises(ValueError):
        plot_fpca_regression_future_prediction_interval(
            prediction, max_targets=0
        )
    plt.close("all")
