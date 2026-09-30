import numpy as np
import pytest

from eyetrajectoriespy._sparse_multivariate import (
    PlanarCovarianceBlocks,
    build_joint_score_covariance,
    evaluate_fitted_surface,
    evaluate_planar_covariance,
    joint_pace_scores,
    permute_planar_channel_major_to_time_major,
    planar_channel_major_to_time_major_permutation,
    resolve_measurement_error_covariance,
    stack_planar_eigenfunctions,
    stack_planar_mean,
    stack_planar_observations,
)
from eyetrajectoriespy._sparse_native import SparseNativeError


def _m2_blocks():
    grid = np.array([0.0, 1.0, 2.0])
    cxx = np.array(
        [
            [1.0, 20.0, 2.0],
            [20.0, 21.0, 22.0],
            [2.0, 22.0, 3.0],
        ]
    )
    cxy = np.array(
        [
            [10.0, 30.0, 11.0],
            [31.0, 32.0, 33.0],
            [12.0, 34.0, 13.0],
        ]
    )
    cyy = np.array(
        [
            [4.0, 40.0, 5.0],
            [40.0, 41.0, 42.0],
            [5.0, 42.0, 6.0],
        ]
    )
    return grid, PlanarCovarianceBlocks(
        cxx=cxx,
        cxy=cxy,
        cyx=cxy.T,
        cyy=cyy,
    )


def _score_fixture():
    grid = np.array([0.0, 0.5, 1.0])
    cxx = np.eye(3)
    cxy = np.zeros((3, 3))
    cyy = 0.5 * np.eye(3)
    blocks = PlanarCovarianceBlocks(
        cxx=cxx,
        cxy=cxy,
        cyx=cxy.T,
        cyy=cyy,
    )
    mean = np.zeros((2, 3))
    eigenvalues = np.array([0.8, 0.3])
    eigenfunctions = np.array(
        [
            [
                [1.0, 1.0, 1.0],
                [0.7, 0.7, 0.7],
            ],
            [
                [0.4, 0.4, 0.4],
                [-0.8, -0.8, -0.8],
            ],
        ]
    )
    times = (np.array([0.0, 1.0]),)
    observed = (
        np.array(
            [
                [1.0, -0.2],
                [0.3, 0.8],
            ]
        ),
    )
    return (
        grid,
        blocks,
        mean,
        eigenvalues,
        eigenfunctions,
        times,
        observed,
    )


def test_directional_surface_evaluation_never_self_symmetrizes():
    grid = np.array([0.0, 1.0, 2.0])
    surface = np.array(
        [
            [1.0, 10.0, 2.0],
            [11.0, 12.0, 13.0],
            [3.0, 14.0, 4.0],
        ]
    )
    times = np.array([0.0, 2.0])

    evaluated = evaluate_fitted_surface(
        grid,
        surface,
        times,
        times,
    )

    assert np.array_equal(
        evaluated,
        np.array(
            [
                [1.0, 2.0],
                [3.0, 4.0],
            ]
        ),
    )
    assert not np.allclose(evaluated, evaluated.T)


def test_m2_planar_covariance_has_exact_time_major_layout():
    grid, blocks = _m2_blocks()
    times = np.array([0.0, 2.0])

    channel_major = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="channel_major",
    )
    time_major = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="time_major",
    )

    expected_channel_major = np.array(
        [
            [1.0, 2.0, 10.0, 11.0],
            [2.0, 3.0, 12.0, 13.0],
            [10.0, 12.0, 4.0, 5.0],
            [11.0, 13.0, 5.0, 6.0],
        ]
    )
    expected_time_major = np.array(
        [
            [1.0, 10.0, 2.0, 11.0],
            [10.0, 4.0, 12.0, 5.0],
            [2.0, 12.0, 3.0, 13.0],
            [11.0, 5.0, 13.0, 6.0],
        ]
    )

    assert np.array_equal(channel_major, expected_channel_major)
    assert np.array_equal(time_major, expected_time_major)
    assert np.array_equal(
        blocks.cyx,
        blocks.cxy.T,
    )


def test_named_permutation_matches_exact_channel_to_time_mapping():
    permutation = planar_channel_major_to_time_major_permutation(2)
    assert np.array_equal(permutation, np.array([0, 2, 1, 3]))

    vector = np.array([1.0, 2.0, 10.0, 20.0])
    assert np.array_equal(
        permute_planar_channel_major_to_time_major(
            vector,
            n_time_points=2,
        ),
        np.array([1.0, 10.0, 2.0, 20.0]),
    )

    grid, blocks = _m2_blocks()
    times = np.array([0.0, 2.0])
    channel_major = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="channel_major",
    )
    time_major = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="time_major",
    )
    assert np.array_equal(
        permute_planar_channel_major_to_time_major(
            channel_major,
            n_time_points=2,
        ),
        time_major,
    )


def test_planar_stacking_helpers_are_time_major_interleaved():
    grid = np.array([0.0, 0.5, 1.0])
    times = np.array([0.0, 1.0])
    observed = np.array(
        [
            [1.0, 10.0],
            [2.0, 20.0],
        ]
    )
    mean = np.array(
        [
            [0.1, 0.2, 0.3],
            [1.1, 1.2, 1.3],
        ]
    )
    eigenfunctions = np.array(
        [
            [
                [1.0, 1.5, 2.0],
                [10.0, 15.0, 20.0],
            ]
        ]
    )

    assert np.array_equal(
        stack_planar_observations(observed),
        np.array([1.0, 10.0, 2.0, 20.0]),
    )
    assert np.allclose(
        stack_planar_mean(grid, mean, times),
        np.array([0.1, 1.1, 0.3, 1.3]),
    )
    assert np.allclose(
        stack_planar_eigenfunctions(
            grid,
            eigenfunctions,
            times,
            n_components=1,
        )[:, 0],
        np.array([1.0, 10.0, 2.0, 20.0]),
    )


def test_measurement_error_diagonal_and_fixed_matrix_contracts():
    diagonal = resolve_measurement_error_covariance(
        "diagonal",
        measurement_error_variance=(0.2, 0.4),
    )
    assert np.array_equal(
        diagonal.covariance,
        np.diag([0.2, 0.4]),
    )
    assert diagonal.mode == "diagonal"

    fixed = resolve_measurement_error_covariance(
        "fixed_matrix",
        measurement_error_covariance=np.array(
            [
                [1.0, 0.25],
                [0.25, 2.0],
            ]
        ),
    )
    assert np.array_equal(
        fixed.covariance,
        np.array(
            [
                [1.0, 0.25],
                [0.25, 2.0],
            ]
        ),
    )
    assert np.min(fixed.eigenvalues) > 0


@pytest.mark.parametrize(
    "matrix",
    [
        np.array([[1.0, 2.0], [2.0, 1.0]]),
        np.array([[1.0, 0.1], [0.2, 1.0]]),
        np.array([[1.0, np.nan], [np.nan, 1.0]]),
    ],
)
def test_invalid_measurement_error_covariance_fails_without_projection(
    matrix,
):
    with pytest.raises(SparseNativeError) as exc:
        resolve_measurement_error_covariance(
            "fixed_matrix",
            measurement_error_covariance=matrix,
        )
    assert exc.value.code == "invalid_measurement_error_covariance"


def test_measurement_error_kron_places_cross_term_only_within_time():
    native = np.zeros((4, 4))
    error = np.array(
        [
            [1.0, 0.25],
            [0.25, 2.0],
        ]
    )

    sigma = build_joint_score_covariance(
        native,
        error,
    )

    assert np.array_equal(
        sigma,
        np.array(
            [
                [1.0, 0.25, 0.0, 0.0],
                [0.25, 2.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.25],
                [0.0, 0.0, 0.25, 2.0],
            ]
        ),
    )


def test_diagonal_measurement_error_has_no_cross_channel_terms():
    native = np.zeros((4, 4))
    error = resolve_measurement_error_covariance(
        "diagonal",
        measurement_error_variance=(0.2, 0.4),
    ).covariance

    sigma = build_joint_score_covariance(native, error)

    assert sigma[0, 1] == 0.0
    assert sigma[2, 3] == 0.0
    assert np.array_equal(
        np.diag(sigma),
        np.array([0.2, 0.4, 0.2, 0.4]),
    )


def test_time_major_and_channel_major_systems_are_exactly_equivalent():
    grid, blocks = _m2_blocks()
    times = np.array([0.0, 2.0])
    observed_channel_major = np.array([1.0, 0.3, -0.2, 0.8])
    error = np.array(
        [
            [0.4, 0.1],
            [0.1, 0.5],
        ]
    )

    covariance_cm = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="channel_major",
    )
    covariance_tm = evaluate_planar_covariance(
        grid,
        blocks,
        times,
        order="time_major",
    )
    permutation = planar_channel_major_to_time_major_permutation(2)
    noise_tm = np.kron(np.eye(2), error)
    noise_cm = noise_tm[
        np.ix_(np.argsort(permutation), np.argsort(permutation))
    ]
    sigma_cm = covariance_cm + noise_cm
    sigma_tm = covariance_tm + noise_tm
    observed_tm = observed_channel_major[permutation]

    solved_cm = np.linalg.solve(sigma_cm, observed_channel_major)
    solved_tm = np.linalg.solve(sigma_tm, observed_tm)

    assert np.allclose(solved_tm, solved_cm[permutation])


def test_joint_pace_uses_full_fitted_covariance_not_rank_k_reconstruction():
    (
        grid,
        blocks,
        mean,
        eigenvalues,
        eigenfunctions,
        times,
        observed,
    ) = _score_fixture()
    error = np.array(
        [
            [0.2, 0.05],
            [0.05, 0.3],
        ]
    )

    result = joint_pace_scores(
        ("curve-1",),
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=error,
        n_components=1,
    )

    native_covariance = evaluate_planar_covariance(
        grid,
        blocks,
        times[0],
        order="time_major",
    )
    sigma_full = build_joint_score_covariance(
        native_covariance,
        error,
    )
    centered = (
        stack_planar_observations(observed[0])
        - stack_planar_mean(grid, mean, times[0])
    )
    phi = stack_planar_eigenfunctions(
        grid,
        eigenfunctions,
        times[0],
        n_components=1,
    )
    expected_full = eigenvalues[0] * (
        phi[:, 0] @ np.linalg.solve(sigma_full, centered)
    )

    rank_k_covariance = (
        eigenvalues[0] * np.outer(phi[:, 0], phi[:, 0])
    )
    sigma_rank_k = build_joint_score_covariance(
        rank_k_covariance,
        error,
    )
    rank_k_score = eigenvalues[0] * (
        phi[:, 0] @ np.linalg.solve(sigma_rank_k, centered)
    )

    assert result.scores[0, 0] == pytest.approx(expected_full)
    assert not np.isclose(result.scores[0, 0], rank_k_score)
    assert result.provenance["rank_k_covariance_used_for_scoring"] is False
    assert result.provenance["score_covariance_source"] == (
        "full_fitted_joint_covariance_plus_measurement_error"
    )


def test_nonzero_cross_channel_measurement_error_changes_joint_scores():
    fixture = _score_fixture()
    (
        grid,
        blocks,
        mean,
        eigenvalues,
        eigenfunctions,
        times,
        observed,
    ) = fixture

    diagonal = joint_pace_scores(
        ("curve-1",),
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=np.diag([0.2, 0.3]),
        n_components=2,
    )
    correlated = joint_pace_scores(
        ("curve-1",),
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=np.array(
            [
                [0.2, 0.12],
                [0.12, 0.3],
            ]
        ),
        n_components=2,
    )

    assert not np.allclose(diagonal.scores, correlated.scores)


def test_score_ridge_changes_joint_system_scores_and_is_reported():
    (
        grid,
        blocks,
        mean,
        eigenvalues,
        eigenfunctions,
        times,
        observed,
    ) = _score_fixture()
    error = np.diag([0.1, 0.1])

    no_ridge = joint_pace_scores(
        ("curve-1",),
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=error,
        n_components=2,
        score_ridge=0.0,
    )
    ridge = joint_pace_scores(
        ("curve-1",),
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=error,
        n_components=2,
        score_ridge=0.2,
    )

    assert not np.allclose(no_ridge.scores, ridge.scores)
    assert ridge.diagnostics.loc[0, "score_ridge"] == pytest.approx(0.2)


def test_ill_conditioned_joint_score_system_has_joint_specific_status():
    grid = np.array([0.0, 0.5, 1.0])
    zero = np.zeros((3, 3))
    blocks = PlanarCovarianceBlocks(
        cxx=zero,
        cxy=zero,
        cyx=zero,
        cyy=zero,
    )
    mean = np.zeros((2, 3))
    eigenvalues = np.array([1.0])
    eigenfunctions = np.ones((1, 2, 3))

    result = joint_pace_scores(
        ("ill",),
        (np.array([0.0, 1.0]),),
        (np.array([[1.0, 0.0], [0.5, 0.2]]),),
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=np.diag([1e-10, 1.0]),
        n_components=1,
        condition_limit=1e6,
        failure_action="retain_nan",
    )

    assert result.diagnostics.loc[0, "status_code"] == (
        "joint_score_covariance_ill_conditioned"
    )
    assert result.diagnostics.loc[0, "solve_status"] == "not_attempted"
    assert np.isnan(result.scores[0, 0])


def test_non_positive_definite_joint_score_system_has_specific_status():
    grid = np.array([0.0, 0.5, 1.0])
    negative = -2.0 * np.eye(3)
    zero = np.zeros((3, 3))
    blocks = PlanarCovarianceBlocks(
        cxx=negative,
        cxy=zero,
        cyx=zero,
        cyy=negative,
    )
    result = joint_pace_scores(
        ("bad",),
        (np.array([0.0, 1.0]),),
        (np.ones((2, 2)),),
        evaluation_grid=grid,
        fitted_mean=np.zeros((2, 3)),
        covariance_blocks=blocks,
        eigenvalues=np.array([1.0]),
        eigenfunctions=np.ones((1, 2, 3)),
        measurement_error_covariance=np.eye(2),
        n_components=1,
        failure_action="retain_nan",
    )

    assert result.diagnostics.loc[0, "status_code"] == (
        "joint_score_covariance_not_positive_definite"
    )
    assert np.isnan(result.scores[0, 0])


def test_native_time_outside_support_is_retained_when_requested():
    (
        grid,
        blocks,
        mean,
        eigenvalues,
        eigenfunctions,
        _,
        observed,
    ) = _score_fixture()

    result = joint_pace_scores(
        ("outside",),
        (np.array([-0.1, 0.5]),),
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=np.eye(2),
        n_components=1,
        failure_action="retain_nan",
    )

    assert result.diagnostics.loc[0, "status_code"] == (
        "native_time_outside_fitted_support"
    )
    assert np.isnan(result.scores[0, 0])


def test_retain_nan_preserves_too_sparse_curves_and_diagnostic_rows():
    (
        grid,
        blocks,
        mean,
        eigenvalues,
        eigenfunctions,
        _,
        _,
    ) = _score_fixture()
    times = (
        np.array([0.5]),
        np.array([0.0, 1.0]),
    )
    observed = (
        np.array([[1.0, 0.5]]),
        np.array([[1.0, -0.2], [0.3, 0.8]]),
    )

    result = joint_pace_scores(
        ("too-sparse", "ok"),
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=np.diag([0.2, 0.3]),
        n_components=1,
        failure_action="retain_nan",
    )

    assert result.scores.shape == (2, 1)
    assert np.isnan(result.scores[0, 0])
    assert np.isfinite(result.scores[1, 0])
    assert result.diagnostics["curve_id"].tolist() == [
        "too-sparse",
        "ok",
    ]
    assert result.diagnostics["status_code"].tolist() == [
        "curve_too_sparse_for_joint_score_system",
        "ok",
    ]
    assert result.diagnostics["n_planar_observations"].tolist() == [2, 4]
    assert result.provenance["operator_storage_order"] == "channel_major"
    assert result.provenance["score_observation_order"] == (
        "time_major_interleaved_xy"
    )
    assert result.provenance["ordering_permutation_applied"] is True
