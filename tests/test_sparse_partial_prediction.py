import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_partial_prediction import (
    SparseFPCAPartialPredictionResult,
    sparse_fpca_partial_prediction_frame,
    sparse_fpca_partial_prediction_reporting_text,
    sparse_fpca_partial_trajectory_prediction,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseFPCAResult


def _fit(
    *,
    grid=(0.0, 0.5, 1.0),
    mean=None,
    covariance=None,
    noise_variance=1.0,
    score_ridge=0.0,
    score_condition_limit=1e12,
):
    grid = np.asarray(grid, dtype=float)
    if mean is None:
        mean = np.zeros(grid.size, dtype=float)
    if covariance is None:
        covariance = 2.0 * np.ones((grid.size, grid.size), dtype=float)
    return SparseFPCAResult(
        scores=np.zeros((3, 1), dtype=float),
        eigenvalues=np.asarray([0.25], dtype=float),
        dimension="x",
        curve_ids=("train1", "train2", "train3"),
        metadata=pd.DataFrame(index=range(3)),
        coordinate_system="normalized",
        time_unit="s",
        n_components=1,
        fit_method="native_covariance",
        fit_smoothing="local_linear_epanechnikov",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-10,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "backend": "native",
                "score_ridge": float(score_ridge),
                "score_condition_limit": float(score_condition_limit),
                "min_score_samples": 2,
            }
        },
        evaluation_grid=grid,
        mean=np.asarray(mean, dtype=float),
        covariance=np.asarray(covariance, dtype=float),
        eigenfunctions=np.ones((1, grid.size), dtype=float),
        noise_variance=float(noise_variance),
        quadrature_weights=np.ones(grid.size, dtype=float),
        score_diagnostics=pd.DataFrame(),
        covariance_diagnostics={},
        mean_support_counts=np.ones(grid.size, dtype=int),
        covariance_support_counts=np.ones((grid.size, grid.size), dtype=int),
    )


def _trajectory(
    values=(1.0, 1.0, 999.0),
    *,
    times=(0.0, 0.25, 0.75),
    curve_id="target",
    coordinate_system="normalized",
    time_unit="s",
):
    time = np.asarray(times, dtype=float)
    value = np.asarray(values, dtype=float)
    return IrregularTrajectorySet(
        time=(time,),
        values=(value[:, None],),
        curve_ids=(curve_id,),
        dimension_names=("x",),
        coordinate_system=coordinate_system,
        time_unit=time_unit,
    )


def test_constant_covariance_matches_analytic_conditional_moments():
    fit = _fit(noise_variance=1.0)
    target = _trajectory()

    result = sparse_fpca_partial_trajectory_prediction(
        fit,
        target,
        history_cutoff=0.25,
        prediction_grid=np.asarray([1.0]),
    )

    assert isinstance(result, SparseFPCAPartialPredictionResult)
    assert result.conditional_mean[0] == pytest.approx(0.8)
    assert result.latent_covariance[0, 0] == pytest.approx(0.4)
    assert result.latent_standard_errors[0] == pytest.approx(np.sqrt(0.4))
    assert result.observed_predictive_covariance[0, 0] == pytest.approx(1.4)
    assert result.observed_predictive_standard_errors[0] == pytest.approx(
        np.sqrt(1.4)
    )
    assert result.diagnostics.loc[0, "future_rows_ignored"] == 1
    assert result.provenance["rank_k_covariance_used_for_prediction"] is False
    assert result.provenance["conformal_calibration_applied"] is False


def test_direct_matrix_calculation_matches_nonconstant_covariance():
    covariance = np.asarray(
        [
            [2.0, 1.0, 0.5],
            [1.0, 3.0, 1.5],
            [0.5, 1.5, 4.0],
        ]
    )
    fit = _fit(covariance=covariance, noise_variance=0.5)
    target = _trajectory(
        values=(1.0, -1.0, 50.0),
        times=(0.0, 0.5, 0.75),
    )

    result = sparse_fpca_partial_trajectory_prediction(
        fit,
        target,
        history_cutoff=0.5,
        prediction_grid=np.asarray([1.0]),
    )

    sigma = covariance[:2, :2] + 0.5 * np.eye(2)
    c_fo = covariance[2:3, :2]
    expected_mean = c_fo @ np.linalg.solve(sigma, np.asarray([1.0, -1.0]))
    expected_covariance = covariance[2:3, 2:3] - c_fo @ np.linalg.solve(
        sigma, covariance[:2, 2:3]
    )
    assert result.conditional_mean == pytest.approx(expected_mean)
    assert result.latent_covariance == pytest.approx(expected_covariance)


def test_future_values_after_cutoff_never_enter_prediction():
    fit = _fit()
    first = _trajectory(values=(1.0, 1.0, 999.0))
    second = _trajectory(values=(1.0, 1.0, -1.0e12))

    result_a = sparse_fpca_partial_trajectory_prediction(
        fit,
        first,
        history_cutoff=0.25,
        prediction_grid=np.asarray([0.75, 1.0]),
    )
    result_b = sparse_fpca_partial_trajectory_prediction(
        fit,
        second,
        history_cutoff=0.25,
        prediction_grid=np.asarray([0.75, 1.0]),
    )

    assert result_a.conditional_mean == pytest.approx(result_b.conditional_mean)
    assert result_a.latent_covariance == pytest.approx(result_b.latent_covariance)
    assert result_a.provenance["future_observations_after_cutoff_used"] is False


def test_nested_history_reduces_conditional_variance():
    fit = _fit(noise_variance=1.0)
    target = _trajectory(values=(1.0, 1.0, 1.0))

    one = sparse_fpca_partial_trajectory_prediction(
        fit,
        target,
        history_cutoff=0.0,
        prediction_grid=np.asarray([1.0]),
        min_history_observations=1,
    )
    two = sparse_fpca_partial_trajectory_prediction(
        fit,
        target,
        history_cutoff=0.25,
        prediction_grid=np.asarray([1.0]),
        min_history_observations=1,
    )

    assert one.latent_covariance[0, 0] == pytest.approx(2.0 / 3.0)
    assert two.latent_covariance[0, 0] == pytest.approx(0.4)
    assert two.latent_covariance[0, 0] < one.latent_covariance[0, 0]


def test_zero_and_high_noise_limits_behave_as_expected():
    target = _trajectory(values=(1.0, 1.0, 1.0))
    zero = sparse_fpca_partial_trajectory_prediction(
        _fit(noise_variance=0.0),
        target,
        history_cutoff=0.0,
        prediction_grid=np.asarray([1.0]),
        min_history_observations=1,
    )
    high = sparse_fpca_partial_trajectory_prediction(
        _fit(noise_variance=10.0),
        target,
        history_cutoff=0.0,
        prediction_grid=np.asarray([1.0]),
        min_history_observations=1,
    )

    assert zero.latent_covariance[0, 0] == pytest.approx(0.0, abs=1e-12)
    assert high.latent_covariance[0, 0] == pytest.approx(5.0 / 3.0)
    assert high.latent_covariance[0, 0] > zero.latent_covariance[0, 0]


def test_history_ridge_is_not_added_to_future_measurement_noise():
    fit = _fit(noise_variance=1.0, score_ridge=3.0)
    result = sparse_fpca_partial_trajectory_prediction(
        fit,
        _trajectory(values=(1.0, 1.0, 1.0)),
        history_cutoff=0.25,
        prediction_grid=np.asarray([1.0]),
    )

    assert result.provenance["history_ridge"] == pytest.approx(3.0)
    assert result.provenance["history_ridge_in_observed_future_noise"] is False
    assert result.observed_predictive_covariance[0, 0] == pytest.approx(
        result.latent_covariance[0, 0] + 1.0
    )


def test_frame_and_reporting_state_conditional_scope():
    result = sparse_fpca_partial_trajectory_prediction(
        _fit(),
        _trajectory(),
        history_cutoff=0.25,
        prediction_grid=np.asarray([0.75, 1.0]),
    )
    frame = sparse_fpca_partial_prediction_frame(result)
    text = sparse_fpca_partial_prediction_reporting_text(result)

    assert list(frame.columns) == [
        "curve_id",
        "dimension",
        "time",
        "conditional_mean",
        "latent_standard_error",
        "observed_predictive_standard_error",
    ]
    assert frame.shape[0] == 2
    assert "full fitted/repaired sparse-FPCA covariance" in text
    assert "No conformal calibration" in text
    assert "conditional on fitted population objects" in text


def test_prediction_grid_and_support_fail_closed():
    fit = _fit()
    target = _trajectory()

    with pytest.raises(SparseNativeError) as exc:
        sparse_fpca_partial_trajectory_prediction(
            fit,
            target,
            history_cutoff=0.25,
            prediction_grid=np.asarray([0.25, 1.0]),
        )
    assert exc.value.code == "prediction_grid_not_strictly_future"

    with pytest.raises(SparseNativeError) as exc:
        sparse_fpca_partial_trajectory_prediction(
            fit,
            target,
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.1]),
        )
    assert exc.value.code == "prediction_grid_outside_fitted_support"

    with pytest.raises(SparseNativeError) as exc:
        sparse_fpca_partial_trajectory_prediction(
            fit,
            target,
            history_cutoff=-0.1,
            prediction_grid=np.asarray([0.5]),
        )
    assert exc.value.code == "history_cutoff_outside_fitted_support"


def test_insufficient_nonfinite_and_unit_contracts_fail():
    fit = _fit()
    target = _trajectory()

    with pytest.raises(SparseNativeError) as exc:
        sparse_fpca_partial_trajectory_prediction(
            fit,
            target,
            history_cutoff=0.0,
            prediction_grid=np.asarray([1.0]),
            min_history_observations=2,
        )
    assert exc.value.code == "insufficient_history_observations"

    nonfinite = _trajectory(values=(np.nan, 1.0, 2.0))
    with pytest.raises(SparseNativeError) as exc:
        sparse_fpca_partial_trajectory_prediction(
            fit,
            nonfinite,
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
        )
    assert exc.value.code == "nonfinite_history_observation"

    with pytest.raises(ValueError, match="time_unit"):
        sparse_fpca_partial_trajectory_prediction(
            fit,
            _trajectory(time_unit="ms"),
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
        )


def test_singular_history_system_fails_without_ridge_and_can_be_regularized():
    fit = _fit(noise_variance=0.0, score_ridge=0.0)
    target = _trajectory(values=(1.0, 1.0, 1.0))

    with pytest.raises(SparseNativeError) as exc:
        sparse_fpca_partial_trajectory_prediction(
            fit,
            target,
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
        )
    assert exc.value.code == "history_covariance_not_positive_definite"

    regularized = sparse_fpca_partial_trajectory_prediction(
        fit,
        target,
        history_cutoff=0.25,
        prediction_grid=np.asarray([1.0]),
        history_ridge=1e-3,
    )
    assert regularized.diagnostics.loc[0, "status_code"] == "ok"
    assert regularized.provenance["history_ridge_source"] == "explicit_override"


def test_invalid_inputs_and_result_helpers_fail_cleanly():
    fit = _fit()
    with pytest.raises(TypeError):
        sparse_fpca_partial_trajectory_prediction(
            fit,
            object(),
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
        )
    with pytest.raises(ValueError, match="exactly one"):
        two = IrregularTrajectorySet(
            time=(np.asarray([0.0, 0.25]), np.asarray([0.0, 0.25])),
            values=(np.ones((2, 1)), np.ones((2, 1))),
            curve_ids=("a", "b"),
            dimension_names=("x",),
            coordinate_system="normalized",
            time_unit="s",
        )
        sparse_fpca_partial_trajectory_prediction(
            fit,
            two,
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
        )
    with pytest.raises(ValueError, match="condition_limit"):
        sparse_fpca_partial_trajectory_prediction(
            fit,
            _trajectory(),
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
            condition_limit=1.0,
        )
    with pytest.raises(ValueError, match="history_ridge"):
        sparse_fpca_partial_trajectory_prediction(
            fit,
            _trajectory(),
            history_cutoff=0.25,
            prediction_grid=np.asarray([1.0]),
            history_ridge=-1.0,
        )
    with pytest.raises(TypeError):
        sparse_fpca_partial_prediction_frame(object())
    with pytest.raises(TypeError):
        sparse_fpca_partial_prediction_reporting_text(object())
