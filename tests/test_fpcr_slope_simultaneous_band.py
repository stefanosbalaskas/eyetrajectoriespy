from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCARegressionSlopeBandResult,
    bootstrap_fpca_regression_uncertainty,
    fit_mfpca,
    fpca_regression_slope_band_frame,
    fpca_regression_slope_band_reporting_text,
    fpca_regression_slope_simultaneous_band,
    plot_fpca_regression_slope_band,
    simulate_planar_trajectories,
)


def bootstrap_result():
    gaze = simulate_planar_trajectories(
        n_participants=14,
        trials_per_participant=2,
        n_time=31,
        random_state=81,
    )
    fpca = fit_mfpca(gaze, n_components=2, scaling="dimension_sd")
    outcome = 0.75 + 1.25 * fpca.scores[:, 0] - 0.5 * fpca.scores[:, 1]
    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        n_bootstrap=24,
        n_components=2,
        scaling="dimension_sd",
        random_state=19,
    )
    return gaze, result


def test_global_band_contains_reference_and_contract_shapes():
    gaze, regression = bootstrap_result()
    band = fpca_regression_slope_simultaneous_band(
        regression,
        confidence_level=0.95,
        simultaneous_scope="global",
    )
    assert isinstance(band, FPCARegressionSlopeBandResult)
    assert band.lower.shape == regression.reference_slope.shape
    assert band.upper.shape == regression.reference_slope.shape
    assert band.pointwise_se.shape == regression.reference_slope.shape
    assert band.critical_values.shape == (gaze.n_dimensions,)
    assert band.max_statistics.shape == (regression.n_bootstrap,)
    assert band.n_bootstrap == regression.n_bootstrap
    assert band.n_time == gaze.n_time
    assert band.n_dimensions == gaze.n_dimensions
    assert np.all(band.lower <= regression.reference_slope)
    assert np.all(regression.reference_slope <= band.upper)
    assert np.allclose(band.critical_values, band.critical_values[0])
    assert (
        band.provenance["fpca_regression_slope_band"][
            "continuous_between_grid_points"
        ]
        is False
    )


def test_global_scope_is_no_narrower_than_dimension_scope():
    _, regression = bootstrap_result()
    dimension = fpca_regression_slope_simultaneous_band(
        regression,
        confidence_level=0.95,
        simultaneous_scope="dimension",
    )
    global_band = fpca_regression_slope_simultaneous_band(
        regression,
        confidence_level=0.95,
        simultaneous_scope="global",
    )
    assert dimension.max_statistics.shape == (
        regression.n_bootstrap,
        regression.reference_slope.shape[1],
    )
    assert np.all(global_band.critical_values >= dimension.critical_values - 1e-12)
    assert np.all(
        (global_band.upper - global_band.lower)
        >= (dimension.upper - dimension.lower) - 1e-12
    )


def test_higher_confidence_is_no_narrower_under_same_bootstrap():
    _, regression = bootstrap_result()
    low = fpca_regression_slope_simultaneous_band(
        regression,
        confidence_level=0.80,
        simultaneous_scope="global",
    )
    high = fpca_regression_slope_simultaneous_band(
        regression,
        confidence_level=0.99,
        simultaneous_scope="global",
    )
    assert np.all(
        (high.upper - high.lower)
        >= (low.upper - low.lower) - 1e-12
    )


def test_zero_variance_cells_and_degenerate_cells_are_explicit():
    _, regression = bootstrap_result()
    identical = np.broadcast_to(
        regression.reference_slope,
        regression.bootstrap_slopes.shape,
    ).copy()
    zero = replace(regression, bootstrap_slopes=identical)
    band = fpca_regression_slope_simultaneous_band(zero)
    assert np.allclose(band.pointwise_se, 0.0)
    assert np.allclose(band.lower, regression.reference_slope)
    assert np.allclose(band.upper, regression.reference_slope)

    shifted = identical.copy()
    shifted[:, 0, 0] += 1.0
    degenerate = replace(regression, bootstrap_slopes=shifted)
    with pytest.raises(RuntimeError, match="degenerate"):
        fpca_regression_slope_simultaneous_band(degenerate)


def test_band_validation_frame_plot_and_reporting():
    _, regression = bootstrap_result()
    with pytest.raises(TypeError):
        fpca_regression_slope_simultaneous_band(object())
    with pytest.raises(ValueError):
        fpca_regression_slope_simultaneous_band(
            regression, confidence_level=1.0
        )
    with pytest.raises(ValueError):
        fpca_regression_slope_simultaneous_band(
            regression, simultaneous_scope="component"
        )

    band = fpca_regression_slope_simultaneous_band(
        regression,
        simultaneous_scope="dimension",
    )
    frame = fpca_regression_slope_band_frame(band)
    assert len(frame) == regression.reference_slope.size
    assert {
        "time",
        "dimension",
        "reference_slope",
        "pointwise_se",
        "critical_value",
        "lower",
        "upper",
    } == set(frame.columns)

    text = fpca_regression_slope_band_reporting_text(band)
    assert "observed-grid simultaneous" in text
    assert "does not claim coverage between grid points" in text
    assert "not the operator-scaled FPCR significance test" in text

    assert plot_fpca_regression_slope_band(band, dimension="x") is not None
    with pytest.raises(KeyError):
        plot_fpca_regression_slope_band(band, dimension="missing")
    plt.close("all")
