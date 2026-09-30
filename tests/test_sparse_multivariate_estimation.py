import numpy as np
import pytest

from eyetrajectoriespy._sparse_multivariate import (
    RawPlanarCovariancePairs,
    audit_repair_planar_covariance,
    estimate_sparse_planar_mean_covariance,
    raw_planar_covariance_pairs,
    smooth_planar_covariance_pairs,
)
from eyetrajectoriespy._sparse_native import (
    RawCovariancePairs,
    SparseNativeError,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def _orthogonal_scores(n_curves=12):
    phase = 2.0 * np.pi * np.arange(n_curves) / n_curves
    z = np.sqrt(2.0) * np.cos(phase)
    w = np.sqrt(2.0) * np.sin(phase)
    assert abs(float(np.mean(z))) < 1e-12
    assert abs(float(np.mean(w))) < 1e-12
    assert abs(float(np.mean(z * w))) < 1e-12
    return z, w


def _coupled_planar_data(rho):
    n_curves = 12
    time = np.linspace(0.0, 1.0, 17)
    z, w = _orthogonal_scores(n_curves)
    y_score = rho * z + np.sqrt(1.0 - rho**2) * w
    mode = np.sin(np.pi * time)
    mean_x = 0.15 + 0.2 * time
    mean_y = -0.1 + 0.1 * time

    values = tuple(
        np.column_stack(
            [
                mean_x + z[index] * mode,
                mean_y + y_score[index] * mode,
            ]
        )
        for index in range(n_curves)
    )
    trajectories = IrregularTrajectorySet(
        time=tuple(time.copy() for _ in range(n_curves)),
        values=values,
        curve_ids=tuple(f"curve-{index}" for index in range(n_curves)),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
    )
    return trajectories, time, mean_x, mean_y


def _asymmetric_residual_pairs():
    time = np.linspace(0.0, 1.0, 13)
    z, _ = _orthogonal_scores(12)
    fx = 0.2 + time
    gy = 0.1 + time**2
    residual_x = tuple(score * fx for score in z)
    residual_y = tuple(score * gy for score in z)
    curve_times = tuple(time.copy() for _ in z)
    return raw_planar_covariance_pairs(
        curve_times,
        residual_x,
        residual_y,
    )


def test_raw_planar_cross_pairs_are_off_diagonal_and_directional():
    time = (np.array([0.0, 1.0, 2.0]),)
    residual_x = (np.array([1.0, 2.0, 4.0]),)
    residual_y = (np.array([7.0, 11.0, 13.0]),)

    pairs = raw_planar_covariance_pairs(
        time,
        residual_x,
        residual_y,
    )

    assert pairs.same_time_pairs_excluded is True
    assert pairs.yx_estimated_independently is False
    assert pairs.xy.n_pairs == 6
    assert not np.any(np.isclose(pairs.xy.s, pairs.xy.t))

    forward = (
        np.isclose(pairs.xy.s, 0.0)
        & np.isclose(pairs.xy.t, 1.0)
    )
    reverse = (
        np.isclose(pairs.xy.s, 1.0)
        & np.isclose(pairs.xy.t, 0.0)
    )
    assert pairs.xy.products[forward].item() == pytest.approx(11.0)
    assert pairs.xy.products[reverse].item() == pytest.approx(14.0)


def test_cross_surface_is_not_self_symmetrized():
    pairs = _asymmetric_residual_pairs()
    grid = np.linspace(0.2, 0.8, 7)

    blocks, support = smooth_planar_covariance_pairs(
        pairs,
        grid,
        bandwidth=0.35,
        min_local_pairs=12,
    )

    assert np.max(np.abs(blocks.cxy - blocks.cxy.T)) > 1e-2
    assert np.allclose(blocks.cyx, blocks.cxy.T)
    assert np.array_equal(support.cxx, support.cxy)
    assert np.array_equal(support.cxy, support.cyy)


def test_cross_surface_is_stable_at_shared_grid_points_under_refinement():
    pairs = _asymmetric_residual_pairs()
    coarse = np.linspace(0.2, 0.8, 4)
    fine = np.linspace(0.2, 0.8, 7)

    coarse_blocks, _ = smooth_planar_covariance_pairs(
        pairs,
        coarse,
        bandwidth=0.35,
        min_local_pairs=12,
    )
    fine_blocks, _ = smooth_planar_covariance_pairs(
        pairs,
        fine,
        bandwidth=0.35,
        min_local_pairs=12,
    )

    assert np.allclose(
        coarse_blocks.cxy,
        fine_blocks.cxy[::2, ::2],
        rtol=1e-12,
        atol=1e-12,
    )


@pytest.mark.parametrize(
    ("rho", "expected_sign"),
    [
        (0.0, 0),
        (0.3, 1),
        (0.6, 1),
        (0.9, 1),
        (-0.6, -1),
    ],
)
def test_direct_sparse_cross_covariance_recovers_coupling_sign(
    rho,
    expected_sign,
):
    trajectories, grid, mean_x, mean_y = _coupled_planar_data(rho)

    result = estimate_sparse_planar_mean_covariance(
        trajectories,
        evaluation_grid=grid,
        mean_bandwidth=0.3,
        covariance_bandwidth=0.35,
        psd_action="project",
        covariance_min_local_pairs=12,
    )

    assert np.allclose(result.mean[0], mean_x, atol=1e-10)
    assert np.allclose(result.mean[1], mean_y, atol=1e-10)
    assert result.provenance[
        "cross_covariance_same_time_products_excluded"
    ] is True
    assert result.provenance["yx_estimated_independently"] is False
    assert result.provenance["cross_covariance_self_symmetrized"] is False
    assert np.allclose(
        result.smoothed_covariance_blocks.cyx,
        result.smoothed_covariance_blocks.cxy.T,
    )

    cross = result.smoothed_covariance_blocks.cxy
    interior = cross[2:-2, 2:-2]
    if expected_sign == 0:
        assert np.max(np.abs(interior)) < 1e-10
    elif expected_sign > 0:
        assert float(np.mean(interior)) > 0.05
    else:
        assert float(np.mean(interior)) < -0.05


def test_coordinate_specific_missingness_fails_without_interpolation():
    time = np.linspace(0.0, 1.0, 7)
    values = []
    for index in range(3):
        current = np.column_stack(
            [
                time + 0.1 * index,
                1.0 - time + 0.2 * index,
            ]
        )
        values.append(current)
    values[1] = values[1].copy()
    values[1][3, 0] = np.nan

    trajectories = IrregularTrajectorySet(
        time=tuple(time.copy() for _ in range(3)),
        values=tuple(values),
        curve_ids=("a", "b", "c"),
        dimension_names=("x", "y"),
    )

    with pytest.raises(SparseNativeError) as exc:
        estimate_sparse_planar_mean_covariance(
            trajectories,
            evaluation_grid=time,
            mean_bandwidth=0.4,
            covariance_bandwidth=0.4,
        )

    assert exc.value.code == "coordinate_specific_missingness_unsupported"
    assert exc.value.details["curve_id"] == "b"
    assert exc.value.details["n_coordinate_specific_missing"] == 1


def test_cross_block_support_failure_has_specific_status():
    grid = np.array([0.0, 0.5, 1.0])
    dense_axis = np.linspace(0.0, 1.0, 11)
    s, t = np.meshgrid(dense_axis, dense_axis, indexing="ij")
    dense = RawCovariancePairs(
        s=s.ravel(),
        t=t.ravel(),
        products=(1.0 + s + t).ravel(),
        curve_index=np.zeros(s.size, dtype=int),
        mirrored=False,
    )
    sparse_xy = RawCovariancePairs(
        s=np.array([0.45, 0.5, 0.55]),
        t=np.array([0.45, 0.55, 0.5]),
        products=np.array([1.0, 1.1, 0.9]),
        curve_index=np.zeros(3, dtype=int),
        mirrored=False,
    )
    pairs = RawPlanarCovariancePairs(
        xx=dense,
        xy=sparse_xy,
        yy=dense,
    )

    with pytest.raises(SparseNativeError) as exc:
        smooth_planar_covariance_pairs(
            pairs,
            grid,
            bandwidth=0.25,
            min_local_pairs=3,
        )

    assert exc.value.code == "insufficient_cross_covariance_local_support"
    assert exc.value.details["block"] == "xy"


def test_operator_retains_smoothed_blocks_before_joint_psd_projection():
    grid = np.linspace(0.0, 1.0, 7)
    marginal = np.eye(grid.size)
    cross = 1.2 * np.eye(grid.size)

    result = audit_repair_planar_covariance(
        marginal,
        cross,
        marginal,
        grid,
        action="project",
        tolerance=1e-12,
    )

    assert np.allclose(result.smoothed_cxx, marginal)
    assert np.allclose(result.smoothed_cxy, cross)
    assert np.allclose(result.smoothed_cyx, cross.T)
    assert np.allclose(result.smoothed_cyy, marginal)
    assert np.allclose(
        result.smoothed_covariance_blocks.matrix,
        result.smoothed_covariance_matrix,
    )
    assert result.audit.applied_action == "project"
    assert not np.allclose(result.cxy, result.smoothed_cxy)
    assert not np.allclose(
        result.covariance_blocks.matrix,
        result.smoothed_covariance_matrix,
    )
