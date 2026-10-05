import numpy as np
import pytest

from eyetrajectoriespy._sparse_multivariate import PlanarCovarianceBlocks
from eyetrajectoriespy._sparse_multivariate_async import (
    async_joint_pace_scores,
    build_async_measurement_error_covariance,
    build_async_observation_layout,
    evaluate_async_planar_covariance,
    prepare_async_planar_views,
    raw_async_planar_covariance_pairs,
)
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.types import IrregularTrajectorySet


def _async_trajectories() -> IrregularTrajectorySet:
    times = tuple(
        np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0], dtype=float)
        for _ in range(3)
    )
    values = []
    for offset in (0.0, 0.1, -0.1):
        values.append(
            np.array(
                [
                    [0.0 + offset, 0.2 + offset],
                    [np.nan, 0.3 + offset],
                    [0.4 + offset, np.nan],
                    [0.6 + offset, 0.7 + offset],
                    [0.8 + offset, np.nan],
                    [1.0 + offset, 1.1 + offset],
                ],
                dtype=float,
            )
        )
    return IrregularTrajectorySet(
        time=times,
        values=tuple(values),
        curve_ids=("a", "b", "c"),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )


def test_prepare_async_views_recovers_coordinate_specific_native_grids():
    trajectories = _async_trajectories()
    grid = np.linspace(0.0, 1.0, 6)

    tx, xv, ty, yv, diagnostics = prepare_async_planar_views(
        trajectories,
        evaluation_grid=grid,
    )

    np.testing.assert_allclose(tx[0], [0.0, 0.4, 0.6, 0.8, 1.0])
    np.testing.assert_allclose(ty[0], [0.0, 0.2, 0.6, 1.0])
    np.testing.assert_allclose(xv[0], [0.0, 0.4, 0.6, 0.8, 1.0])
    np.testing.assert_allclose(yv[0], [0.2, 0.3, 0.7, 1.1])
    assert diagnostics["original_union_sample_counts"] == [6, 6, 6]
    assert diagnostics["original_x_sample_counts"] == [5, 5, 5]
    assert diagnostics["original_y_sample_counts"] == [4, 4, 4]
    assert diagnostics["simultaneous_sample_counts"] == [3, 3, 3]
    assert diagnostics["x_only_sample_counts"] == [2, 2, 2]
    assert diagnostics["y_only_sample_counts"] == [1, 1, 1]


def test_prepare_async_views_rejects_union_row_with_no_coordinate():
    trajectories = _async_trajectories()
    bad_values = list(trajectories.values)
    bad_values[1] = bad_values[1].copy()
    bad_values[1][2, :] = np.nan
    bad = IrregularTrajectorySet(
        time=trajectories.time,
        values=tuple(bad_values),
        curve_ids=trajectories.curve_ids,
        dimension_names=trajectories.dimension_names,
    )

    with pytest.raises(SparseNativeError) as exc:
        prepare_async_planar_views(
            bad,
            evaluation_grid=np.linspace(0.0, 1.0, 6),
        )

    assert exc.value.code == "empty_async_timestamp_row"
    assert exc.value.details["curve_id"] == "b"
    assert exc.value.details["sample_indices"] == [2]


def test_async_raw_pairs_use_coordinate_times_and_exclude_same_time_cross_products():
    tx = (
        np.array([0.0, 0.4]),
        np.array([0.1, 0.5]),
    )
    rx = (
        np.array([1.0, 2.0]),
        np.array([1.5, 2.5]),
    )
    ty = (
        np.array([0.2, 0.4]),
        np.array([0.3, 0.5]),
    )
    ry = (
        np.array([3.0, 4.0]),
        np.array([3.5, 4.5]),
    )

    pairs, diagnostics = raw_async_planar_covariance_pairs(
        tx,
        rx,
        ty,
        ry,
    )

    assert diagnostics["cross_candidate_pair_count"] == 8
    assert diagnostics["cross_same_time_pair_count_excluded"] == 2
    assert diagnostics["cross_retained_pair_count"] == 6
    assert pairs.xy.n_pairs == 6
    assert not np.any(np.isclose(pairs.xy.s, pairs.xy.t))
    assert np.any(np.isclose(pairs.xy.s, 0.0) & np.isclose(pairs.xy.t, 0.2))
    assert np.any(np.isclose(pairs.xy.s, 0.4) & np.isclose(pairs.xy.t, 0.2))


def test_async_observation_order_is_time_major_x_before_y_for_ties():
    layout = build_async_observation_layout(
        np.array([0.0, 0.5]),
        np.array([10.0, 11.0]),
        np.array([0.0, 0.25, 0.5]),
        np.array([20.0, 21.0, 22.0]),
    )

    np.testing.assert_allclose(layout.times, [0.0, 0.0, 0.25, 0.5, 0.5])
    np.testing.assert_array_equal(layout.channels, [0, 1, 1, 0, 1])
    np.testing.assert_allclose(layout.values, [10.0, 20.0, 21.0, 11.0, 22.0])
    assert layout.n_simultaneous_pairs == 2
    assert layout.order == "time_major_x_before_y_for_ties"


def test_fully_paired_layout_reduces_to_existing_interleaved_order():
    layout = build_async_observation_layout(
        np.array([0.0, 0.5, 1.0]),
        np.array([1.0, 2.0, 3.0]),
        np.array([0.0, 0.5, 1.0]),
        np.array([4.0, 5.0, 6.0]),
    )

    np.testing.assert_allclose(layout.times, [0.0, 0.0, 0.5, 0.5, 1.0, 1.0])
    np.testing.assert_array_equal(layout.channels, [0, 1, 0, 1, 0, 1])
    np.testing.assert_allclose(layout.values, [1.0, 4.0, 2.0, 5.0, 3.0, 6.0])


def test_async_covariance_uses_the_block_matching_each_observation_channel():
    grid = np.array([0.0, 0.5, 1.0])
    blocks = PlanarCovarianceBlocks(
        cxx=np.full((3, 3), 2.0),
        cxy=np.full((3, 3), 0.5),
        cyx=np.full((3, 3), 0.5),
        cyy=np.full((3, 3), 3.0),
    )
    layout = build_async_observation_layout(
        np.array([0.0, 0.75]),
        np.array([1.0, 2.0]),
        np.array([0.25]),
        np.array([3.0]),
    )

    covariance = evaluate_async_planar_covariance(grid, blocks, layout)
    expected = np.array(
        [
            [2.0, 0.5, 2.0],
            [0.5, 3.0, 0.5],
            [2.0, 0.5, 2.0],
        ]
    )
    np.testing.assert_allclose(covariance, expected)


def test_async_measurement_error_cross_covariance_only_links_simultaneous_xy():
    layout = build_async_observation_layout(
        np.array([0.0, 0.5]),
        np.array([1.0, 2.0]),
        np.array([0.0, 0.25, 0.5]),
        np.array([3.0, 4.0, 5.0]),
    )
    error = np.array([[0.1, 0.03], [0.03, 0.2]])

    noise, links = build_async_measurement_error_covariance(layout, error)

    assert links == 2
    np.testing.assert_allclose(np.diag(noise), [0.1, 0.2, 0.2, 0.1, 0.2])
    assert noise[0, 1] == pytest.approx(0.03)
    assert noise[3, 4] == pytest.approx(0.03)
    assert noise[0, 2] == pytest.approx(0.0)
    assert noise[2, 3] == pytest.approx(0.0)


def test_async_joint_pace_matches_direct_matrix_calculation():
    grid = np.array([0.0, 0.5, 1.0])
    # Full fitted covariance deliberately contains more variation than the one
    # retained score component, so the score system cannot be reconstructed
    # from rank K without changing the answer.
    blocks = PlanarCovarianceBlocks(
        cxx=np.full((3, 3), 1.4),
        cxy=np.full((3, 3), 0.4),
        cyx=np.full((3, 3), 0.4),
        cyy=np.full((3, 3), 0.9),
    )
    fitted_mean = np.zeros((2, 3))
    eigenvalues = np.array([1.25])
    eigenfunctions = np.array([[[1.0, 1.0, 1.0], [0.5, 0.5, 0.5]]])
    error = np.array([[0.2, 0.04], [0.04, 0.3]])
    tx = np.array([0.0, 0.8])
    xv = np.array([1.2, -0.3])
    ty = np.array([0.0, 0.4, 1.0])
    yv = np.array([0.7, -0.2, 0.5])

    result = async_joint_pace_scores(
        ("curve",),
        (tx,),
        (xv,),
        (ty,),
        (yv,),
        evaluation_grid=grid,
        fitted_mean=fitted_mean,
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=error,
        n_components=1,
    )

    layout = build_async_observation_layout(tx, xv, ty, yv)
    latent = evaluate_async_planar_covariance(grid, blocks, layout)
    noise, _ = build_async_measurement_error_covariance(layout, error)
    sigma = latent + noise
    phi = np.where(layout.channels[:, None] == 0, 1.0, 0.5)
    expected = eigenvalues[0] * float(phi[:, 0] @ np.linalg.solve(sigma, layout.values))

    assert result.scores[0, 0] == pytest.approx(expected)
    assert result.diagnostics.loc[0, "status_code"] == "ok"
    assert result.diagnostics.loc[0, "measurement_error_cross_links"] == 1
    assert result.provenance["rank_k_covariance_used_for_scoring"] is False
    assert result.provenance["raw_sparse_trajectory_interpolation_performed"] is False


def test_x_only_and_y_only_observations_can_contribute_to_joint_score():
    grid = np.array([0.0, 0.5, 1.0])
    blocks = PlanarCovarianceBlocks(
        cxx=np.eye(3),
        cxy=np.zeros((3, 3)),
        cyx=np.zeros((3, 3)),
        cyy=np.eye(3),
    )
    eigenvalues = np.array([1.0])
    eigenfunctions = np.array([[[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]])

    result = async_joint_pace_scores(
        ("curve",),
        (np.array([0.0, 0.5]),),
        (np.array([1.0, 2.0]),),
        (np.array([0.25, 1.0]),),
        (np.array([3.0, 4.0]),),
        evaluation_grid=grid,
        fitted_mean=np.zeros((2, 3)),
        covariance_blocks=blocks,
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        measurement_error_covariance=np.diag([0.5, 0.5]),
        n_components=1,
    )

    assert np.isfinite(result.scores[0, 0])
    assert result.diagnostics.loc[0, "n_x_observations"] == 2
    assert result.diagnostics.loc[0, "n_y_observations"] == 2
    assert result.diagnostics.loc[0, "n_simultaneous_pairs"] == 0


def test_async_score_failure_can_be_retained_visibly():
    grid = np.array([0.0, 0.5, 1.0])
    blocks = PlanarCovarianceBlocks(
        cxx=np.ones((3, 3)),
        cxy=np.zeros((3, 3)),
        cyx=np.zeros((3, 3)),
        cyy=np.ones((3, 3)),
    )
    result = async_joint_pace_scores(
        ("too_sparse",),
        (np.array([0.0]),),
        (np.array([1.0]),),
        (np.array([], dtype=float),),
        (np.array([], dtype=float),),
        evaluation_grid=grid,
        fitted_mean=np.zeros((2, 3)),
        covariance_blocks=blocks,
        eigenvalues=np.array([1.0]),
        eigenfunctions=np.array([[[1.0, 1.0, 1.0], [0.0, 0.0, 0.0]]]),
        measurement_error_covariance=np.eye(2),
        n_components=1,
        min_score_observations=2,
        failure_action="retain_nan",
    )

    assert np.isnan(result.scores[0, 0])
    assert (
        result.diagnostics.loc[0, "status_code"]
        == "curve_too_sparse_for_async_joint_score_system"
    )
