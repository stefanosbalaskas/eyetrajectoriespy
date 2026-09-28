import numpy as np
import pytest

from eyetrajectoriespy._sparse_native import (
    SparseNativeError,
    estimate_noise_variance_diagonal_difference,
    evaluate_fitted_covariance,
    evaluate_fitted_function,
    local_linear_covariance_surface,
    local_linear_smooth_1d,
    pace_scores,
    raw_offdiagonal_covariance_pairs,
    repair_covariance_psd,
    weighted_covariance_eigendecomposition,
)
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy.fpca import functional_trapezoid_weights


def _weighted_orthonormal_truth(grid):
    weights = functional_trapezoid_weights(grid)
    basis = np.column_stack(
        [
            np.sin(np.pi * grid),
            np.sin(2.0 * np.pi * grid),
        ]
    )
    weighted = np.sqrt(weights)[:, None] * basis
    q, _ = np.linalg.qr(weighted)
    eigenfunctions = (q / np.sqrt(weights)[:, None]).T
    return eigenfunctions, weights


def test_weighted_eigensolver_recovers_known_operator():
    grid = np.linspace(0.0, 1.0, 41)
    truth, weights = _weighted_orthonormal_truth(grid)
    eigenvalues = np.array([1.4, 0.45])
    covariance = (
        eigenvalues[0] * np.outer(truth[0], truth[0])
        + eigenvalues[1] * np.outer(truth[1], truth[1])
    )

    result = weighted_covariance_eigendecomposition(
        covariance,
        grid,
        n_components=2,
    )

    assert np.allclose(result.eigenvalues, eigenvalues, rtol=1e-10, atol=1e-12)
    similarity = np.abs(
        result.eigenfunctions @ np.diag(weights) @ truth.T
    )
    assert np.allclose(np.diag(similarity), 1.0, atol=1e-10)
    assert np.allclose(
        result.eigenfunctions
        @ np.diag(weights)
        @ result.eigenfunctions.T,
        np.eye(2),
        atol=1e-10,
    )


def test_psd_policy_distinguishes_failure_from_projection():
    grid = np.linspace(0.0, 1.0, 7)
    covariance = np.eye(grid.size)
    covariance[3, 3] = -0.5

    with pytest.raises(SparseNativeError) as exc:
        repair_covariance_psd(
            covariance,
            grid,
            action="error",
            tolerance=1e-10,
        )
    assert exc.value.code == "covariance_psd_failure"
    assert exc.value.details["substantial_negative_eigenvalue_count"] >= 1

    projected = repair_covariance_psd(
        covariance,
        grid,
        action="project",
        tolerance=1e-10,
    )
    audit = projected.audit
    assert audit.requested_action == "project"
    assert audit.applied_action == "project"
    assert audit.negative_eigenvalue_count >= 1
    assert audit.most_negative_eigenvalue < 0
    assert audit.correction_frobenius_norm > 0
    assert audit.relative_correction_frobenius_norm > 0
    assert audit.operator_correction_frobenius_norm > 0
    assert audit.relative_operator_correction_frobenius_norm > 0

    weights = functional_trapezoid_weights(grid)
    operator = (
        np.sqrt(weights)[:, None]
        * projected.covariance
        * np.sqrt(weights)[None, :]
    )
    assert np.min(np.linalg.eigvalsh(operator)) >= -1e-12


def test_tiny_negative_psd_error_path_records_numerical_stabilization():
    grid = np.linspace(0.0, 1.0, 5)
    covariance = np.eye(grid.size)
    covariance[-1, -1] = -1e-12

    repaired = repair_covariance_psd(
        covariance,
        grid,
        action="error",
        tolerance=1e-10,
    )

    assert repaired.audit.applied_action == "numerical_clip_within_tolerance"
    assert repaired.audit.substantial_negative_eigenvalue_count == 0
    assert repaired.audit.negative_eigenvalue_count == 1


def test_pace_uses_full_fitted_covariance_not_rank_k_reconstruction():
    grid = np.array([0.0, 0.5, 1.0])
    mean = np.zeros(3)
    phi1 = np.array([0.4, 1.0, 0.2])
    phi2 = np.array([1.0, -0.2, 0.6])
    full_covariance = (
        1.2 * np.outer(phi1, phi1)
        + 0.7 * np.outer(phi2, phi2)
        + 0.15 * np.eye(3)
    )
    observed = np.array([0.8, -0.1, 0.5])
    noise_variance = 0.08

    result = pace_scores(
        ("curve-1",),
        (grid,),
        (observed,),
        evaluation_grid=grid,
        fitted_mean=mean,
        fitted_covariance=full_covariance,
        eigenvalues=np.array([1.2]),
        eigenfunctions=phi1[None, :],
        noise_variance=noise_variance,
        n_components=1,
    )

    sigma = full_covariance + noise_variance * np.eye(3)
    expected = 1.2 * phi1 @ np.linalg.solve(sigma, observed)
    rank_one_sigma = (
        1.2 * np.outer(phi1, phi1)
        + noise_variance * np.eye(3)
    )
    rank_one_score = 1.2 * phi1 @ np.linalg.solve(
        rank_one_sigma,
        observed,
    )

    assert result.covariance_source == "full_fitted_covariance_plus_noise"
    assert result.scores[0, 0] == pytest.approx(expected)
    assert not np.isclose(result.scores[0, 0], rank_one_score)
    assert result.diagnostics.loc[0, "status_code"] == "ok"
    assert result.diagnostics.loc[0, "solve_status"] == "solved"


def test_pace_ridge_is_explicit_and_changes_estimator():
    grid = np.array([0.0, 0.5, 1.0])
    covariance = np.array(
        [
            [1.0, 0.6, 0.2],
            [0.6, 1.0, 0.6],
            [0.2, 0.6, 1.0],
        ]
    )
    phi = np.array([[0.5, 1.0, 0.5]])
    observed = np.array([0.2, 0.4, 0.7])

    base = pace_scores(
        ("curve-1",),
        (grid,),
        (observed,),
        evaluation_grid=grid,
        fitted_mean=np.zeros(3),
        fitted_covariance=covariance,
        eigenvalues=np.array([0.8]),
        eigenfunctions=phi,
        noise_variance=0.05,
        n_components=1,
        score_ridge=0.0,
    )
    ridge = pace_scores(
        ("curve-1",),
        (grid,),
        (observed,),
        evaluation_grid=grid,
        fitted_mean=np.zeros(3),
        fitted_covariance=covariance,
        eigenvalues=np.array([0.8]),
        eigenfunctions=phi,
        noise_variance=0.05,
        n_components=1,
        score_ridge=0.2,
    )

    assert not np.isclose(base.scores[0, 0], ridge.scores[0, 0])
    assert base.diagnostics.loc[0, "score_ridge"] == 0.0
    assert ridge.diagnostics.loc[0, "score_ridge"] == 0.2


def test_pace_structured_status_codes_retain_failed_curves_when_requested():
    grid = np.array([0.0, 0.5, 1.0])
    result = pace_scores(
        ("too-sparse", "ok"),
        (np.array([0.5]), grid),
        (np.array([0.2]), np.array([0.1, 0.3, 0.2])),
        evaluation_grid=grid,
        fitted_mean=np.zeros(3),
        fitted_covariance=np.eye(3),
        eigenvalues=np.array([1.0]),
        eigenfunctions=np.array([[0.5, 1.0, 0.5]]),
        noise_variance=0.1,
        n_components=1,
        min_score_samples=2,
        failure_action="retain_nan",
    )

    assert np.isnan(result.scores[0, 0])
    assert np.isfinite(result.scores[1, 0])
    assert (
        result.diagnostics.loc[0, "status_code"]
        == "curve_too_sparse_for_score_system"
    )
    assert result.diagnostics.loc[1, "status_code"] == "ok"

    with pytest.raises(SparseNativeError) as exc:
        pace_scores(
            ("too-sparse",),
            (np.array([0.5]),),
            (np.array([0.2]),),
            evaluation_grid=grid,
            fitted_mean=np.zeros(3),
            fitted_covariance=np.eye(3),
            eigenvalues=np.array([1.0]),
            eigenfunctions=np.array([[0.5, 1.0, 0.5]]),
            noise_variance=0.1,
            n_components=1,
            min_score_samples=2,
            failure_action="error",
        )
    assert exc.value.code == "curve_too_sparse_for_score_system"
    assert "all_curve_diagnostics" in exc.value.details


def test_model_evaluation_does_not_interpolate_raw_sparse_observations():
    grid = np.array([0.0, 0.5, 1.0])
    mean = np.array([0.0, 1.0, 0.0])
    covariance = np.array(
        [
            [1.0, 0.5, 0.0],
            [0.5, 1.0, 0.5],
            [0.0, 0.5, 1.0],
        ]
    )
    native_times = np.array([0.25, 0.75])

    evaluated_mean = evaluate_fitted_function(
        grid,
        mean,
        native_times,
    )
    evaluated_covariance = evaluate_fitted_covariance(
        grid,
        covariance,
        native_times,
    )

    assert np.allclose(evaluated_mean, [0.5, 0.5])
    assert evaluated_covariance.shape == (2, 2)
    assert np.allclose(evaluated_covariance, evaluated_covariance.T)

    with pytest.raises(SparseNativeError) as exc:
        evaluate_fitted_function(
            grid,
            mean,
            np.array([-0.1, 0.5]),
        )
    assert exc.value.code == "native_time_outside_fitted_support"


def test_local_support_failures_have_specific_codes():
    with pytest.raises(SparseNativeError) as exc:
        local_linear_smooth_1d(
            np.array([0.0, 1.0]),
            np.array([0.0, 1.0]),
            np.array([0.5]),
            bandwidth=0.05,
        )
    assert exc.value.code == "insufficient_mean_local_support"

    with pytest.raises(SparseNativeError) as exc:
        raw_offdiagonal_covariance_pairs(
            (np.array([0.0]), np.array([1.0])),
            (np.array([0.1]), np.array([0.2])),
        )
    assert exc.value.code == "insufficient_within_curve_covariance_pairs"


def test_private_sparse_truth_recovers_latent_eigenspace():
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=48,
        samples_per_curve=12,
        noise_sd=0.12,
        random_state=202610,
    )
    grid = np.linspace(0.0, 1.0, 25)
    pooled_time = np.concatenate(times)
    pooled_value = np.concatenate(values)

    mean_fit = local_linear_smooth_1d(
        pooled_time,
        pooled_value,
        grid,
        bandwidth=0.20,
        noise_support=(0.15, 0.85),
        min_local_points=8,
    )

    residuals = []
    for time, observed in zip(times, values, strict=True):
        mean_at_native = local_linear_smooth_1d(
            pooled_time,
            pooled_value,
            time,
            bandwidth=0.20,
            min_local_points=8,
        ).values
        residuals.append(observed - mean_at_native)

    pairs = raw_offdiagonal_covariance_pairs(
        times,
        tuple(residuals),
        include_mirror=True,
    )
    covariance_fit = local_linear_covariance_surface(
        pairs,
        grid,
        bandwidth=0.28,
        min_local_pairs=20,
    )
    psd = repair_covariance_psd(
        covariance_fit.values,
        grid,
        action="project",
        tolerance=1e-8,
    )
    eigen = weighted_covariance_eigendecomposition(
        psd.covariance,
        grid,
        n_components=2,
    )

    true_mean = truth.mean(grid)
    mean_rmse = float(
        np.sqrt(np.mean((mean_fit.values - true_mean) ** 2))
    )
    true_phi = np.vstack(
        [function(grid) for function in truth.eigenfunctions]
    )
    weights = eigen.quadrature_weights
    similarity = np.abs(
        eigen.eigenfunctions @ np.diag(weights) @ true_phi.T
    )

    assert mean_rmse < 0.35
    assert similarity[0, 0] > 0.80
    assert similarity[1, 1] > 0.80
    assert eigen.eigenvalues[0] > eigen.eigenvalues[1] > 0
    assert psd.audit.negative_eigenvalue_count >= 0

    noise = estimate_noise_variance_diagonal_difference(
        times,
        tuple(residuals),
        grid,
        covariance_fit.values,
        bandwidth=0.20,
        min_local_points=8,
    )
    assert np.isfinite(noise.variance)
    assert noise.status_code in {"ok", "noise_variance_invalid"}


def test_covariance_surface_is_symmetric_and_tracks_local_support():
    times, values, _ = simulate_sparse_functional_truth(
        n_curves=12,
        samples_per_curve=8,
        random_state=7,
    )
    pooled_time = np.concatenate(times)
    pooled_value = np.concatenate(values)
    residuals = []
    for time, observed in zip(times, values, strict=True):
        mean_at_native = local_linear_smooth_1d(
            pooled_time,
            pooled_value,
            time,
            bandwidth=0.30,
            min_local_points=5,
        ).values
        residuals.append(observed - mean_at_native)
    pairs = raw_offdiagonal_covariance_pairs(times, tuple(residuals))
    grid = np.linspace(0.0, 1.0, 11)

    result = local_linear_covariance_surface(
        pairs,
        grid,
        bandwidth=0.40,
        min_local_pairs=6,
    )

    assert result.values.shape == (11, 11)
    assert result.support_counts.shape == (11, 11)
    assert np.allclose(result.values, result.values.T)
    assert np.min(result.support_counts) >= 6
