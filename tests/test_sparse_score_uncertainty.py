import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_score_uncertainty import (
    SparseFPCAScoreUncertaintyResult,
    sparse_fpca_score_uncertainty,
    sparse_fpca_score_uncertainty_frame,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseFPCAResult


def _trajectories(
    times,
    *,
    curve_ids=None,
    coordinate_system="normalized",
    time_unit="s",
):
    times = tuple(np.asarray(time, dtype=float) for time in times)
    if curve_ids is None:
        curve_ids = tuple(f"c{i + 1}" for i in range(len(times)))
    values = tuple(
        np.zeros((time.size, 1), dtype=float)
        for time in times
    )
    return IrregularTrajectorySet(
        time=times,
        values=values,
        curve_ids=tuple(curve_ids),
        dimension_names=("x",),
        coordinate_system=coordinate_system,
        time_unit=time_unit,
    )


def _fit(
    *,
    curve_ids=("c1",),
    grid=(0.0, 0.5, 1.0),
    covariance=None,
    eigenvalues=(2.0,),
    eigenfunctions=None,
    noise_variance=1.0,
    score_ridge=0.0,
    score_condition_limit=1e12,
    sample_counts=(2,),
    analysis_support_action="error",
):
    grid = np.asarray(grid, dtype=float)
    eigenvalues = np.asarray(eigenvalues, dtype=float)
    if covariance is None:
        covariance = 2.0 * np.ones((grid.size, grid.size), dtype=float)
    if eigenfunctions is None:
        eigenfunctions = np.ones((eigenvalues.size, grid.size), dtype=float)
    n_components = int(eigenvalues.size)
    return SparseFPCAResult(
        scores=np.zeros((len(curve_ids), n_components), dtype=float),
        eigenvalues=eigenvalues,
        dimension="x",
        curve_ids=tuple(curve_ids),
        metadata=pd.DataFrame(index=range(len(curve_ids))),
        coordinate_system="normalized",
        time_unit="s",
        n_components=n_components,
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
                "sample_counts": list(sample_counts),
                "analysis_support_action": analysis_support_action,
            }
        },
        evaluation_grid=grid,
        mean=np.zeros(grid.size, dtype=float),
        covariance=np.asarray(covariance, dtype=float),
        eigenfunctions=np.asarray(eigenfunctions, dtype=float),
        noise_variance=float(noise_variance),
        quadrature_weights=np.ones(grid.size, dtype=float),
        score_diagnostics=pd.DataFrame(),
        covariance_diagnostics={},
        mean_support_counts=np.ones(grid.size, dtype=int),
        covariance_support_counts=np.ones((grid.size, grid.size), dtype=int),
    )


def test_one_component_matches_analytic_gaussian_posterior():
    trajectories = _trajectories(([0.0, 1.0],))
    fit = _fit()

    result = sparse_fpca_score_uncertainty(fit, trajectories)

    assert isinstance(result, SparseFPCAScoreUncertaintyResult)
    assert result.method == "conditional_gaussian_given_fitted_population"
    assert result.covariance.shape == (1, 1, 1)
    assert result.covariance[0, 0, 0] == pytest.approx(0.4)
    assert result.standard_errors[0, 0] == pytest.approx(np.sqrt(0.4))
    assert result.correlations[0, 0, 0] == pytest.approx(1.0)
    assert result.diagnostics.loc[0, "status_code"] == "ok"
    assert result.provenance["population_estimation_uncertainty_included"] is False
    assert result.provenance["bandwidth_uncertainty_included"] is False


def test_two_component_orthogonal_design_matches_diagonal_solution():
    grid = np.asarray([0.0, 1.0])
    covariance = np.diag([2.0, 3.0])
    eigenfunctions = np.asarray([[1.0, 0.0], [0.0, 1.0]])
    fit = _fit(
        grid=grid,
        covariance=covariance,
        eigenvalues=(2.0, 3.0),
        eigenfunctions=eigenfunctions,
        noise_variance=1.0,
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_fpca_score_uncertainty(fit, trajectories)

    expected = np.diag([2.0 / 3.0, 3.0 / 4.0])
    np.testing.assert_allclose(result.covariance[0], expected, atol=1e-12)
    np.testing.assert_allclose(
        result.standard_errors[0],
        np.sqrt(np.diag(expected)),
        atol=1e-12,
    )


def test_more_nested_observations_do_not_increase_conditional_variance():
    sparse = _trajectories(([0.0, 1.0],))
    denser = _trajectories(([0.0, 0.5, 1.0],))
    sparse_fit = _fit(sample_counts=(2,))
    dense_fit = _fit(sample_counts=(3,))

    sparse_result = sparse_fpca_score_uncertainty(sparse_fit, sparse)
    dense_result = sparse_fpca_score_uncertainty(dense_fit, denser)

    assert dense_result.covariance[0, 0, 0] <= sparse_result.covariance[0, 0, 0]


def test_low_noise_informative_limit_approaches_zero():
    fit = _fit(noise_variance=1e-10)
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_fpca_score_uncertainty(fit, trajectories)

    assert result.covariance[0, 0, 0] >= 0.0
    assert result.covariance[0, 0, 0] < 1e-8


def test_high_noise_limit_approaches_prior_score_variance():
    fit = _fit(noise_variance=1e12)
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_fpca_score_uncertainty(fit, trajectories)

    assert result.covariance[0, 0, 0] == pytest.approx(2.0, rel=1e-10)


def test_curve_ids_and_order_must_match_exactly():
    fit = _fit(curve_ids=("c1", "c2"), sample_counts=(2, 2))
    trajectories = _trajectories(
        ([0.0, 1.0], [0.0, 1.0]),
        curve_ids=("c2", "c1"),
    )

    with pytest.raises(ValueError, match="curve_ids and order"):
        sparse_fpca_score_uncertainty(fit, trajectories)


def test_ill_conditioned_system_fails_closed_by_default():
    fit = _fit(
        covariance=np.zeros((3, 3), dtype=float),
        noise_variance=0.0,
    )
    trajectories = _trajectories(([0.0, 1.0],))

    with pytest.raises(SparseNativeError) as error:
        sparse_fpca_score_uncertainty(fit, trajectories)

    assert error.value.code == "score_covariance_not_positive_definite"


def test_retain_nan_preserves_failed_curve_and_diagnostics():
    fit = _fit(
        covariance=np.zeros((3, 3), dtype=float),
        noise_variance=0.0,
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_fpca_score_uncertainty(
        fit,
        trajectories,
        failure_action="retain_nan",
    )

    assert np.isnan(result.covariance).all()
    assert np.isnan(result.standard_errors).all()
    assert result.diagnostics.loc[0, "status_code"] == (
        "score_covariance_not_positive_definite"
    )
    assert result.diagnostics.loc[0, "solve_status"] == "not_attempted"


def test_explicit_condition_limit_can_fail_otherwise_valid_system():
    fit = _fit(score_condition_limit=1e12)
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_fpca_score_uncertainty(
        fit,
        trajectories,
        condition_limit=4.0,
        failure_action="retain_nan",
    )

    assert result.diagnostics.loc[0, "status_code"] == (
        "score_covariance_ill_conditioned"
    )
    assert result.provenance["condition_limit_source"] == "explicit_override"


def test_frame_is_one_row_per_curve_component():
    grid = np.asarray([0.0, 1.0])
    fit = _fit(
        grid=grid,
        covariance=np.diag([2.0, 3.0]),
        eigenvalues=(2.0, 3.0),
        eigenfunctions=np.asarray([[1.0, 0.0], [0.0, 1.0]]),
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_fpca_score_uncertainty(fit, trajectories)
    frame = sparse_fpca_score_uncertainty_frame(result)

    assert frame.shape[0] == 2
    assert frame["component"].tolist() == [1, 2]
    assert frame["curve_id"].tolist() == ["c1", "c1"]
    assert set(frame["status_code"]) == {"ok"}
    assert set(frame["method"]) == {
        "conditional_gaussian_given_fitted_population"
    }


def test_restrict_support_reuses_effective_fit_sample_counts():
    fit = _fit(
        grid=(0.0, 0.5, 1.0),
        sample_counts=(2,),
        analysis_support_action="restrict",
    )
    trajectories = _trajectories(([-0.5, 0.0, 1.0, 1.5],))

    result = sparse_fpca_score_uncertainty(fit, trajectories)

    assert result.diagnostics.loc[0, "n_samples"] == 2
    assert result.diagnostics.loc[0, "status_code"] == "ok"
