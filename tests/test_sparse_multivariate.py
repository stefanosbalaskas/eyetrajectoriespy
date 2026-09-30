import numpy as np
import pandas as pd

from eyetrajectoriespy._sparse_multivariate import (
    block_quadrature_weights,
    covariance_blocks_to_matrix,
    covariance_matrix_to_blocks,
    raw_cross_covariance_pairs,
    repair_block_covariance_psd,
    weighted_block_covariance_eigendecomposition,
)
from eyetrajectoriespy.fpca import functional_trapezoid_weights
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca
from eyetrajectoriespy._sparse_multivariate_truth import (
    simulate_sparse_multivariate_truth,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def _weighted_joint_modes(grid):
    weights = block_quadrature_weights(grid, n_dimensions=2)
    raw = np.column_stack(
        [
            np.array([1.0, 0.7, 0.2, -0.2, -0.6, -1.0]),
            np.array([0.1, 0.8, 0.3, 1.0, 0.2, -0.5]),
        ]
    )
    q, _ = np.linalg.qr(np.sqrt(weights)[:, None] * raw)
    return (q / np.sqrt(weights)[:, None]).T


def _synthetic_irregular_planar():
    rng = np.random.default_rng(812)
    curve_ids = tuple(f"curve-{i:02d}" for i in range(18))
    times = []
    values = []
    for index, curve_id in enumerate(curve_ids):
        del curve_id
        base = np.linspace(0.0, 1.0, 10)
        keep = np.sort(
            rng.choice(np.arange(1, 9), size=5, replace=False)
        )
        time = np.concatenate([[0.0], base[keep], [1.0]])
        score1 = rng.normal(scale=0.8)
        score2 = rng.normal(scale=0.45)
        phi1 = np.sin(np.pi * time)
        phi2 = np.cos(2.0 * np.pi * time)
        x = (
            0.15
            + score1 * phi1
            + 0.30 * score2 * phi2
            + rng.normal(scale=0.04, size=time.size)
        )
        y = (
            -0.10
            + 0.65 * score1 * phi1
            - 0.55 * score2 * phi2
            + rng.normal(scale=0.05, size=time.size)
        )
        times.append(time)
        values.append(np.column_stack([x, y]))

    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=curve_ids,
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"condition": ["a"] * len(curve_ids)}),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"fixture": "sparse_joint_test"},
    )


def test_cross_covariance_pairs_keep_equal_time_products():
    times = (np.array([0.0, 0.5, 1.0]),)
    left = (np.array([1.0, 2.0, 3.0]),)
    right = (np.array([4.0, 5.0, 6.0]),)

    pairs = raw_cross_covariance_pairs(times, left, right)

    assert pairs.n_pairs == 9
    assert not pairs.mirrored
    diagonal = (pairs.s == pairs.t)
    np.testing.assert_allclose(
        pairs.products[diagonal],
        np.array([4.0, 10.0, 18.0]),
    )


def test_block_covariance_eigendecomposition_uses_repeated_quadrature():
    grid = np.array([0.0, 0.5, 1.0])
    modes = _weighted_joint_modes(grid)
    eigenvalues = np.array([1.7, 0.6])
    covariance = (
        modes.T
        @ np.diag(eigenvalues)
        @ modes
    )
    blocks = covariance.reshape(2, 3, 2, 3)

    repaired = repair_block_covariance_psd(
        blocks,
        grid,
        action="error",
    )
    result = weighted_block_covariance_eigendecomposition(
        repaired.covariance,
        grid,
        n_dimensions=2,
        n_components=2,
    )

    np.testing.assert_allclose(
        result.eigenvalues,
        eigenvalues,
        rtol=1e-10,
        atol=1e-10,
    )
    gram = (
        result.eigenfunctions
        * result.quadrature_weights[None, :]
    ) @ result.eigenfunctions.T
    np.testing.assert_allclose(gram, np.eye(2), atol=1e-10)

    restored = covariance_matrix_to_blocks(
        covariance_blocks_to_matrix(blocks),
        n_dimensions=2,
        n_grid=3,
    )
    np.testing.assert_allclose(restored, blocks)


def test_sparse_mfpca_returns_joint_operator_and_scores():
    gaze = _synthetic_irregular_planar()
    grid = np.linspace(0.0, 1.0, 9)

    result = fit_sparse_mfpca(
        gaze,
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=0.45,
        covariance_bandwidth=0.55,
        cross_covariance_bandwidth=0.55,
        noise_variance_method="fixed",
        measurement_error_variances={"x": 0.0016, "y": 0.0025},
        psd_action="project",
        score_ridge=1e-8,
        covariance_min_local_pairs=6,
        cross_covariance_min_local_pairs=6,
    )

    assert result.dimension_names == ("x", "y")
    assert result.mean.shape == (9, 2)
    assert result.covariance.shape == (2, 9, 2, 9)
    assert result.eigenfunctions.shape == (2, 9, 2)
    assert result.scores.shape == (18, 2)
    assert np.all(np.isfinite(result.scores))
    np.testing.assert_allclose(
        result.covariance[1, :, 0, :],
        result.covariance[0, :, 1, :].T,
        atol=1e-12,
    )

    weights = functional_trapezoid_weights(grid)
    gram = np.einsum(
        "ktd,t,ltd->kl",
        result.eigenfunctions,
        weights,
        result.eigenfunctions,
    )
    np.testing.assert_allclose(gram, np.eye(2), atol=1e-8)
    np.testing.assert_allclose(
        result.noise_variances,
        np.array([0.0016, 0.0025]),
    )
    assert np.all(result.explained_variance_ratio > 0)
    assert np.sum(result.explained_variance_ratio) <= 1.0 + 1e-10
    assert set(result.score_diagnostics["status_code"]) == {"ok"}

    provenance = result.provenance["sparse_mfpca"]
    assert provenance["cross_channel_covariance_modeled"] is True
    assert (
        provenance["cross_channel_measurement_error"]
        == "independent"
    )
    assert (
        provenance["raw_sparse_trajectory_interpolation_performed"]
        is False
    )
    assert provenance["score_covariance_source"] == (
        "full_fitted_block_covariance_plus_dimension_noise"
    )


def test_sparse_mfpca_requires_explicit_cross_channel_noise_contract():
    gaze = _synthetic_irregular_planar()

    try:
        fit_sparse_mfpca(
            gaze,
            n_components=1,
            evaluation_grid=np.linspace(0.0, 1.0, 7),
            mean_bandwidth=0.5,
            covariance_bandwidth=0.6,
            noise_variance_method="fixed",
            measurement_error_variances={"x": 0.0, "y": 0.0},
            cross_channel_measurement_error="estimated",
        )
    except ValueError as exc:
        assert "cross_channel_measurement_error" in str(exc)
    else:
        raise AssertionError("unsupported cross-channel noise must fail")



def test_sparse_multivariate_truth_holds_marginals_fixed_across_rho():
    grid = np.linspace(0.0, 1.0, 17)
    _, _, truth_zero = simulate_sparse_multivariate_truth(
        n_curves=8,
        samples_per_curve=6,
        channel_correlation=0.0,
        random_state=9021,
    )
    _, _, truth_six = simulate_sparse_multivariate_truth(
        n_curves=8,
        samples_per_curve=6,
        channel_correlation=0.6,
        random_state=9021,
    )

    zero = truth_zero.covariance_blocks(grid)
    six = truth_six.covariance_blocks(grid)

    np.testing.assert_allclose(
        zero[0, :, 0, :],
        six[0, :, 0, :],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        zero[1, :, 1, :],
        six[1, :, 1, :],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        zero[0, :, 1, :],
        0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        six[0, :, 1, :],
        0.6 * six[0, :, 0, :],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        six[1, :, 0, :],
        six[0, :, 1, :].T,
        atol=1e-12,
    )
