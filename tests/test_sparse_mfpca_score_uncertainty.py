import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_multivariate import (
    PlanarCovarianceBlocks,
    build_joint_score_covariance,
    evaluate_planar_covariance,
    stack_planar_eigenfunctions,
)
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_multivariate_score_uncertainty import (
    SparseMFPCAScoreUncertaintyResult,
    sparse_mfpca_score_uncertainty,
    sparse_mfpca_score_uncertainty_frame,
    sparse_mfpca_score_uncertainty_reporting_text,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseMFPCAResult


def _trajectories(
    times,
    *,
    curve_ids=None,
    coordinate_system="normalized",
    time_unit="s",
    dimension_names=("x", "y"),
):
    times = tuple(np.asarray(time, dtype=float) for time in times)
    if curve_ids is None:
        curve_ids = tuple(f"c{i + 1}" for i in range(len(times)))
    values = tuple(np.zeros((time.size, 2), dtype=float) for time in times)
    return IrregularTrajectorySet(
        time=times,
        values=values,
        curve_ids=tuple(curve_ids),
        dimension_names=tuple(dimension_names),
        coordinate_system=coordinate_system,
        time_unit=time_unit,
    )


def _fit(
    *,
    curve_ids=("c1",),
    grid=(0.0, 0.5, 1.0),
    cxx=None,
    cxy=None,
    cyy=None,
    eigenvalues=(2.0,),
    eigenfunctions=None,
    measurement_error_covariance=None,
    score_ridge=0.0,
    score_condition_limit=1e12,
    analysis_sample_counts=(2,),
    analysis_support_action="error",
    dimensions=("x", "y"),
):
    grid = np.asarray(grid, dtype=float)
    eigenvalues = np.asarray(eigenvalues, dtype=float)
    n_components = int(eigenvalues.size)
    if cxx is None:
        cxx = 2.0 * np.ones((grid.size, grid.size), dtype=float)
    if cxy is None:
        cxy = np.zeros((grid.size, grid.size), dtype=float)
    if cyy is None:
        cyy = np.zeros((grid.size, grid.size), dtype=float)
    cxx = np.asarray(cxx, dtype=float)
    cxy = np.asarray(cxy, dtype=float)
    cyy = np.asarray(cyy, dtype=float)
    if eigenfunctions is None:
        eigenfunctions = np.zeros(
            (n_components, grid.size, 2),
            dtype=float,
        )
        eigenfunctions[:, :, 0] = 1.0
    if measurement_error_covariance is None:
        measurement_error_covariance = np.eye(2, dtype=float)
    diagnostics = pd.DataFrame(
        {
            "curve_id": list(curve_ids),
            "status_code": ["ok"] * len(curve_ids),
            "n_time_points": list(analysis_sample_counts),
        }
    )
    provenance = {
        "sparse_mfpca": {
            "backend": "native",
            "fit_method": "direct_sparse_block_covariance",
            "score_method": "joint_PACE",
            "operator_storage_order": "channel_major",
            "score_observation_order": "time_major_interleaved_xy",
            "ordering_permutation_applied": True,
            "score_covariance_source": (
                "full_fitted_joint_covariance_plus_measurement_error"
            ),
            "rank_k_covariance_used_for_scoring": False,
            "score_ridge": float(score_ridge),
            "score_condition_limit": float(score_condition_limit),
            "min_score_time_points": 2,
            "analysis_support_action": analysis_support_action,
            "analysis_sample_counts": list(analysis_sample_counts),
            "raw_sparse_trajectory_interpolation_performed": False,
        }
    }
    support = {
        "cxx": np.ones_like(cxx, dtype=int),
        "cxy": np.ones_like(cxx, dtype=int),
        "cyy": np.ones_like(cxx, dtype=int),
    }
    return SparseMFPCAResult(
        scores=np.zeros((len(curve_ids), n_components), dtype=float),
        eigenvalues=eigenvalues,
        eigenfunctions=np.asarray(eigenfunctions, dtype=float),
        mean=np.zeros((grid.size, 2), dtype=float),
        evaluation_grid=grid,
        dimensions=tuple(dimensions),
        curve_ids=tuple(curve_ids),
        metadata=pd.DataFrame(index=range(len(curve_ids))),
        coordinate_system="normalized",
        time_unit="s",
        n_components=n_components,
        quadrature_weights=np.ones(grid.size, dtype=float),
        smoothed_cxx=cxx.copy(),
        smoothed_cxy=cxy.copy(),
        smoothed_cyx=cxy.T.copy(),
        smoothed_cyy=cyy.copy(),
        covariance_cxx=cxx.copy(),
        covariance_cxy=cxy.copy(),
        covariance_cyx=cxy.T.copy(),
        covariance_cyy=cyy.copy(),
        measurement_error_covariance=np.asarray(
            measurement_error_covariance,
            dtype=float,
        ),
        score_diagnostics=diagnostics,
        mean_support_counts=np.ones((grid.size, 2), dtype=int),
        covariance_support_counts=support,
        covariance_pair_counts={"cxx": 1, "cxy": 1, "cyy": 1},
        covariance_diagnostics={},
        fit_method="direct_sparse_block_covariance",
        score_method="joint_PACE",
        provenance=provenance,
    )


def test_one_component_planar_posterior_matches_analytic_solution():
    trajectories = _trajectories(([0.0, 1.0],))
    fit = _fit()

    result = sparse_mfpca_score_uncertainty(fit, trajectories)

    assert isinstance(result, SparseMFPCAScoreUncertaintyResult)
    assert result.method == "conditional_gaussian_given_fitted_joint_population"
    assert result.covariance.shape == (1, 1, 1)
    assert result.covariance[0, 0, 0] == pytest.approx(0.4)
    assert result.standard_errors[0, 0] == pytest.approx(np.sqrt(0.4))
    assert result.correlations[0, 0, 0] == pytest.approx(1.0)
    assert result.diagnostics.loc[0, "status_code"] == "ok"
    assert result.provenance["rank_k_covariance_used_for_uncertainty"] is False
    assert result.provenance["population_estimation_uncertainty_included"] is False
    assert result.provenance["bandwidth_uncertainty_included"] is False


def test_two_component_orthogonal_planar_case_matches_known_posterior():
    grid = np.asarray([0.0, 1.0])
    cxx = np.diag([2.0, 0.0])
    cyy = np.diag([0.0, 3.0])
    eigenfunctions = np.zeros((2, 2, 2), dtype=float)
    eigenfunctions[0, 0, 0] = 1.0
    eigenfunctions[1, 1, 1] = 1.0
    fit = _fit(
        grid=grid,
        cxx=cxx,
        cyy=cyy,
        eigenvalues=(2.0, 3.0),
        eigenfunctions=eigenfunctions,
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_mfpca_score_uncertainty(fit, trajectories)

    expected = np.diag([2.0 / 3.0, 3.0 / 4.0])
    np.testing.assert_allclose(result.covariance[0], expected, atol=1e-12)
    np.testing.assert_allclose(
        result.standard_errors[0],
        np.sqrt(np.diag(expected)),
        atol=1e-12,
    )


def test_exact_manual_joint_score_system_equivalence_with_correlated_noise():
    grid = np.asarray([0.0, 0.5, 1.0])
    cxx = np.asarray(
        [[1.2, 0.7, 0.3], [0.7, 1.0, 0.6], [0.3, 0.6, 0.9]]
    )
    cxy = np.asarray(
        [[0.2, 0.1, 0.05], [0.15, 0.25, 0.1], [0.03, 0.12, 0.2]]
    )
    cyy = np.asarray(
        [[0.8, 0.4, 0.2], [0.4, 0.7, 0.35], [0.2, 0.35, 0.75]]
    )
    eigenfunctions = np.asarray(
        [
            [[1.0, 0.8], [0.9, 0.7], [0.6, 0.5]],
            [[0.3, -0.7], [0.1, -0.5], [-0.2, -0.4]],
        ]
    )
    error = np.asarray([[0.4, 0.1], [0.1, 0.6]])
    fit = _fit(
        grid=grid,
        cxx=cxx,
        cxy=cxy,
        cyy=cyy,
        eigenvalues=(0.9, 0.35),
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=error,
        score_ridge=0.05,
        analysis_sample_counts=(2,),
    )
    times = np.asarray([0.0, 1.0])
    trajectories = _trajectories((times,))

    result = sparse_mfpca_score_uncertainty(fit, trajectories)

    blocks = PlanarCovarianceBlocks(
        cxx=cxx,
        cxy=cxy,
        cyx=cxy.T,
        cyy=cyy,
    )
    native_covariance = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="time_major",
    )
    sigma = build_joint_score_covariance(
        native_covariance,
        error,
        score_ridge=0.05,
    )
    phi = stack_planar_eigenfunctions(
        grid,
        np.transpose(eigenfunctions, (0, 2, 1)),
        times,
        n_components=2,
    )
    prior = np.diag([0.9, 0.35])
    rhs = phi @ prior
    expected = prior - rhs.T @ np.linalg.solve(sigma, rhs)
    expected = 0.5 * (expected + expected.T)

    np.testing.assert_allclose(result.covariance[0], expected, atol=1e-12)
    assert result.diagnostics.loc[0, "observation_order"] == (
        "time_major_interleaved_xy"
    )
    assert result.provenance["operator_storage_order"] == "channel_major"


def test_more_nested_native_times_do_not_increase_conditional_variance():
    sparse = _trajectories(([0.0, 1.0],))
    denser = _trajectories(([0.0, 0.5, 1.0],))
    sparse_fit = _fit(analysis_sample_counts=(2,))
    dense_fit = _fit(analysis_sample_counts=(3,))

    sparse_result = sparse_mfpca_score_uncertainty(sparse_fit, sparse)
    dense_result = sparse_mfpca_score_uncertainty(dense_fit, denser)

    assert dense_result.covariance[0, 0, 0] <= sparse_result.covariance[0, 0, 0]


def test_low_noise_informative_limit_approaches_zero():
    fit = _fit(
        measurement_error_covariance=np.diag([1e-10, 1e-10]),
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_mfpca_score_uncertainty(fit, trajectories)

    assert result.covariance[0, 0, 0] >= 0.0
    assert result.covariance[0, 0, 0] < 1e-8


def test_high_noise_limit_approaches_prior_joint_score_variance():
    fit = _fit(
        measurement_error_covariance=np.diag([1e12, 1e12]),
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_mfpca_score_uncertainty(fit, trajectories)

    assert result.covariance[0, 0, 0] == pytest.approx(2.0, rel=1e-10)


def test_curve_ids_and_order_must_match_exactly():
    fit = _fit(
        curve_ids=("c1", "c2"),
        analysis_sample_counts=(2, 2),
    )
    trajectories = _trajectories(
        ([0.0, 1.0], [0.0, 1.0]),
        curve_ids=("c2", "c1"),
    )

    with pytest.raises(ValueError, match="curve_ids and order"):
        sparse_mfpca_score_uncertainty(fit, trajectories)


def test_coordinate_system_and_time_unit_must_match_fit():
    fit = _fit()
    wrong_coordinates = _trajectories(
        ([0.0, 1.0],),
        coordinate_system="pixels",
    )
    wrong_time = _trajectories(([0.0, 1.0],), time_unit="ms")

    with pytest.raises(ValueError, match="coordinate_system"):
        sparse_mfpca_score_uncertainty(fit, wrong_coordinates)
    with pytest.raises(ValueError, match="time_unit"):
        sparse_mfpca_score_uncertainty(fit, wrong_time)


def test_ill_conditioned_joint_system_fails_closed_by_default():
    fit = _fit(
        cxx=np.zeros((3, 3), dtype=float),
        measurement_error_covariance=np.zeros((2, 2), dtype=float),
    )
    trajectories = _trajectories(([0.0, 1.0],))

    with pytest.raises(SparseNativeError) as error:
        sparse_mfpca_score_uncertainty(fit, trajectories)

    assert error.value.code == "joint_score_covariance_not_positive_definite"


def test_retain_nan_preserves_failed_curve_and_joint_diagnostics():
    fit = _fit(
        cxx=np.zeros((3, 3), dtype=float),
        measurement_error_covariance=np.zeros((2, 2), dtype=float),
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_mfpca_score_uncertainty(
        fit,
        trajectories,
        failure_action="retain_nan",
    )

    assert np.isnan(result.covariance).all()
    assert np.isnan(result.standard_errors).all()
    assert result.diagnostics.loc[0, "status_code"] == (
        "joint_score_covariance_not_positive_definite"
    )
    assert result.diagnostics.loc[0, "solve_status"] == "not_attempted"


def test_explicit_condition_limit_can_fail_otherwise_valid_joint_system():
    fit = _fit(score_condition_limit=1e12)
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_mfpca_score_uncertainty(
        fit,
        trajectories,
        condition_limit=4.0,
        failure_action="retain_nan",
    )

    assert result.diagnostics.loc[0, "status_code"] == (
        "joint_score_covariance_ill_conditioned"
    )
    assert result.provenance["condition_limit_source"] == "explicit_override"


def test_restrict_support_reuses_effective_fit_time_point_counts():
    fit = _fit(
        analysis_sample_counts=(2,),
        analysis_support_action="restrict",
    )
    trajectories = _trajectories(([-0.5, 0.0, 1.0, 1.5],))

    result = sparse_mfpca_score_uncertainty(fit, trajectories)

    assert result.diagnostics.loc[0, "n_time_points"] == 2
    assert result.diagnostics.loc[0, "n_planar_observations"] == 4
    assert result.diagnostics.loc[0, "status_code"] == "ok"


def test_frame_and_reporting_helpers_preserve_conditional_scope():
    grid = np.asarray([0.0, 1.0])
    cxx = np.diag([2.0, 0.0])
    cyy = np.diag([0.0, 3.0])
    eigenfunctions = np.zeros((2, 2, 2), dtype=float)
    eigenfunctions[0, 0, 0] = 1.0
    eigenfunctions[1, 1, 1] = 1.0
    fit = _fit(
        grid=grid,
        cxx=cxx,
        cyy=cyy,
        eigenvalues=(2.0, 3.0),
        eigenfunctions=eigenfunctions,
    )
    trajectories = _trajectories(([0.0, 1.0],))

    result = sparse_mfpca_score_uncertainty(fit, trajectories)
    frame = sparse_mfpca_score_uncertainty_frame(result)
    text = sparse_mfpca_score_uncertainty_reporting_text(result)

    assert frame.shape[0] == 2
    assert frame["component"].tolist() == [1, 2]
    assert frame["curve_id"].tolist() == ["c1", "c1"]
    assert set(frame["status_code"]) == {"ok"}
    assert set(frame["method"]) == {
        "conditional_gaussian_given_fitted_joint_population"
    }
    assert "Conditional joint-PACE score uncertainty" in text
    assert "do not include uncertainty" in text
