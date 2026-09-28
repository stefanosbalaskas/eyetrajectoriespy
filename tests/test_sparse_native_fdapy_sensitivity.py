import importlib.util

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linear_sum_assignment

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_fpca,
    fit_sparse_fpca_fdapy,
)
from eyetrajectoriespy._sparse_native import local_linear_smooth_1d
from eyetrajectoriespy.fpca import functional_trapezoid_weights


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("FDApy") is None,
    reason="optional FDApy backend not installed",
)


def test_native_local_linear_mean_matches_fdapy_local_polynomial():
    from FDApy.preprocessing.smoothing.local_polynomial import LocalPolynomial

    rng = np.random.default_rng(9001)
    x = np.sort(rng.uniform(0.0, 1.0, size=80))
    y = 0.4 + 0.8 * x + 0.25 * np.sin(2.0 * np.pi * x)
    points = np.linspace(0.10, 0.90, 13)
    bandwidth = 0.24

    native = local_linear_smooth_1d(
        x,
        y,
        points,
        bandwidth=bandwidth,
        min_local_points=5,
    ).values
    reference = LocalPolynomial(
        kernel_name="epanechnikov",
        bandwidth=bandwidth,
        degree=1,
    ).predict(
        y=y,
        x=x,
        x_new=points,
    )

    np.testing.assert_allclose(
        native,
        reference,
        rtol=1e-9,
        atol=1e-10,
    )


def _shared_grid_sparse_sample():
    rng = np.random.default_rng(9002)
    grid = np.linspace(0.0, 1.0, 21)
    eigenvalues = np.array([1.0, 0.35])
    scores = rng.normal(size=(30, 2)) * np.sqrt(eigenvalues)[None, :]

    times = []
    values = []
    for curve in range(30):
        interior_indices = np.array(
            [
                1 + ((3 * curve + offset) % 19)
                for offset in range(7)
            ],
            dtype=int,
        )
        keep = np.unique(np.concatenate([[0], interior_indices, [20]]))
        time = grid[np.sort(keep)]
        mean = 0.3 + 0.4 * time
        phi1 = np.sqrt(2.0) * np.sin(np.pi * time)
        phi2 = np.sqrt(2.0) * np.sin(2.0 * np.pi * time)
        observed = (
            mean
            + scores[curve, 0] * phi1
            + scores[curve, 1] * phi2
            + rng.normal(scale=0.08, size=time.size)
        )
        times.append(time)
        values.append(observed[:, None])

    gaze = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"P{i:03d}|1" for i in range(30)),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {"participant_id": [f"P{i:03d}" for i in range(30)]}
        ),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "fdapy_cross_implementation_sensitivity"},
    )
    pooled = np.unique(np.concatenate(gaze.time))
    assert np.array_equal(pooled, grid)
    return gaze, grid


def _match_components(native, fdapy, grid):
    weights = functional_trapezoid_weights(grid)
    native_phi = np.asarray(native.eigenfunctions, dtype=float)
    fdapy_phi = np.asarray(
        fdapy.backend_object.eigenfunctions.values,
        dtype=float,
    )
    native_norm = np.sqrt(
        np.sum(native_phi**2 * weights[None, :], axis=1)
    )
    fdapy_norm = np.sqrt(
        np.sum(fdapy_phi**2 * weights[None, :], axis=1)
    )
    native_phi = native_phi / native_norm[:, None]
    fdapy_phi = fdapy_phi / fdapy_norm[:, None]
    signed = native_phi @ np.diag(weights) @ fdapy_phi.T
    similarity = np.abs(signed)
    row, column = linear_sum_assignment(-similarity)
    order = np.argsort(row)
    column = column[order]
    signs = np.sign(signed[np.arange(len(column)), column])
    signs[signs == 0] = 1.0

    cross = (
        native_phi.T * np.sqrt(weights)[:, None]
    ).T @ (
        fdapy_phi[column].T * np.sqrt(weights)[:, None]
    )
    # Use QR-based principal cosines rather than individual signs/order.
    native_q, _ = np.linalg.qr(
        native_phi.T * np.sqrt(weights)[:, None]
    )
    fdapy_q, _ = np.linalg.qr(
        fdapy_phi[column].T * np.sqrt(weights)[:, None]
    )
    principal_cosines = np.linalg.svd(
        native_q.T @ fdapy_q,
        compute_uv=False,
    )
    return column, signs, similarity[np.arange(len(column)), column], principal_cosines


def test_fdapy_is_cross_implementation_sensitivity_not_exact_equivalence():
    gaze, grid = _shared_grid_sparse_sample()
    mean_bandwidth = 0.25
    covariance_bandwidth = 0.35

    native = fit_sparse_fpca(
        gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=mean_bandwidth,
        covariance_bandwidth=covariance_bandwidth,
        noise_variance_method="fixed",
        measurement_error_variance=0.08**2,
        psd_action="project",
    )
    fdapy = fit_sparse_fpca_fdapy(
        gaze,
        dimension="x",
        n_components=2,
        fit_smoothing="LP",
        score_smoothing="LP",
        tol=1e-6,
        normalize=False,
        evaluation_grid=grid,
        kwargs_mean={
            "bandwidth": mean_bandwidth,
            "degree": 1,
            "kernel_name": "epanechnikov",
        },
        kwargs_covariance={
            "bandwidth": covariance_bandwidth,
            "degree": 1,
            "kernel_name": "epanechnikov",
        },
    )

    matched, signs, similarities, principal_cosines = _match_components(
        native,
        fdapy,
        grid,
    )
    fdapy_eigenvalues = fdapy.eigenvalues[matched]
    relative_eigenvalue_difference = np.abs(
        native.eigenvalues - fdapy_eigenvalues
    ) / np.maximum(np.abs(fdapy_eigenvalues), 1e-12)

    score_correlations = []
    score_rmse = []
    for component, reference in enumerate(matched):
        native_score = signs[component] * native.scores[:, component]
        fdapy_score = fdapy.scores[:, reference]
        score_correlations.append(
            abs(np.corrcoef(native_score, fdapy_score)[0, 1])
        )
        score_rmse.append(
            np.sqrt(np.mean((native_score - fdapy_score) ** 2))
        )

    # These are broad sensitivity guards, not equivalence tolerances. FDApy
    # uses a radial 2-D covariance kernel, interpolates irregular curves before
    # PACE, and scores against a retained-rank reconstructed covariance.
    assert np.all(np.isfinite(relative_eigenvalue_difference))
    assert np.all(np.isfinite(score_rmse))
    assert np.min(principal_cosines) > 0.60
    assert np.min(similarities) > 0.45
    assert np.min(score_correlations) > 0.35

    assert native.provenance["sparse_fpca"][
        "score_covariance_source"
    ] == "full_fitted_covariance_plus_noise"
    assert fdapy.provenance["sparse_fpca"]["backend"] == "FDApy"
