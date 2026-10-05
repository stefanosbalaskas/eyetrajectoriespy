import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca
from eyetrajectoriespy.sparse_multivariate_async import (
    SparseAsyncMFPCAResult,
    fit_sparse_mfpca_async,
    sparse_mfpca_async_reporting_text,
    sparse_mfpca_async_score_frame,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def _dataset(n_curves: int = 18) -> IrregularTrajectorySet:
    union = np.linspace(0.0, 1.0, 9)
    x_mask = np.array([True, False, True, True, False, True, True, False, True])
    y_mask = np.array([True, True, False, True, True, False, True, True, True])
    times = []
    values = []
    participants = []
    for index in range(n_curves):
        z1 = -1.5 + 3.0 * index / max(1, n_curves - 1)
        z2 = np.cos(0.7 * (index + 1))
        x_truth = (
            0.1
            + 0.2 * union
            + z1 * np.sin(np.pi * union)
            + 0.22 * z2 * np.cos(2.0 * np.pi * union)
        )
        y_truth = (
            -0.05
            + 0.1 * union
            + 0.70 * z1 * np.cos(np.pi * union)
            + 0.18 * z2 * np.sin(2.0 * np.pi * union)
        )
        observed = np.full((union.size, 2), np.nan, dtype=float)
        observed[x_mask, 0] = x_truth[x_mask]
        observed[y_mask, 1] = y_truth[y_mask]
        times.append(union.copy())
        values.append(observed)
        participants.append(f"P{index // 3:02d}")
    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"curve_{index:02d}" for index in range(n_curves)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "deterministic_async_test"},
    )


def _fit(trajectories: IrregularTrajectorySet) -> SparseAsyncMFPCAResult:
    return fit_sparse_mfpca_async(
        trajectories,
        dimensions=("x", "y"),
        n_components=1,
        evaluation_grid=np.linspace(0.0, 1.0, 7),
        mean_bandwidth=0.45,
        covariance_bandwidth=0.55,
        measurement_error="fixed_matrix",
        measurement_error_covariance=np.array([[0.02, 0.004], [0.004, 0.025]]),
        psd_action="project",
        score_failure_action="retain_nan",
    )


def test_async_public_fitter_returns_auditable_coordinate_specific_result():
    result = _fit(_dataset())

    assert isinstance(result, SparseAsyncMFPCAResult)
    assert result.n_curves == 18
    assert result.n_components == 1
    assert result.scores.shape == (18, 1)
    assert result.eigenfunctions.shape == (1, 7, 2)
    assert result.mean.shape == (7, 2)
    assert result.mean_support_counts.shape == (7, 2)
    assert result.covariance_cxx.shape == (7, 7)
    assert result.covariance_cxy.shape == (7, 7)
    np.testing.assert_allclose(result.covariance_cyx, result.covariance_cxy.T)
    assert np.all(np.isfinite(result.scores))
    assert set(result.score_diagnostics["status_code"]) == {"ok"}
    assert result.support_diagnostics["cross_same_time_pair_count_excluded"] > 0

    provenance = result.provenance["sparse_mfpca_async"]
    assert provenance["coordinate_specific_missingness_supported"] is True
    assert provenance["raw_sparse_trajectory_interpolation_performed"] is False
    assert provenance["nearest_neighbour_synchronization_performed"] is False
    assert provenance["time_binning_performed"] is False
    assert provenance["rank_k_covariance_used_for_scoring"] is False
    assert provenance["measurement_error_cross_covariance_scope"] == "simultaneous_xy_only"
    assert provenance["score_observation_order"] == "time_major_x_before_y_for_ties"


def test_async_score_frame_preserves_ids_metadata_and_component_names():
    result = _fit(_dataset())
    frame = sparse_mfpca_async_score_frame(result)

    assert list(frame.columns) == ["curve_id", "participant", "ASMFPC1"]
    assert tuple(frame["curve_id"]) == result.curve_ids
    np.testing.assert_allclose(frame["ASMFPC1"], result.scores[:, 0])


def test_async_reporting_text_states_noninterpolation_and_same_time_error_contract():
    result = _fit(_dataset())
    text = sparse_mfpca_async_reporting_text(result)

    assert "asynchronous sparse planar MFPCA" in text
    assert "without interpolation" in text
    assert "nearest-neighbour synchronization" in text
    assert "excluded" in text
    assert "simultaneous x/y observations" in text
    assert "never a rank-K covariance reconstruction" in text


def test_existing_synchronous_fitter_keeps_coordinate_specific_missingness_failure():
    trajectories = _dataset()

    with pytest.raises(SparseNativeError) as exc:
        fit_sparse_mfpca(
            trajectories,
            n_components=1,
            evaluation_grid=np.linspace(0.0, 1.0, 7),
            mean_bandwidth=0.45,
            covariance_bandwidth=0.55,
            measurement_error="diagonal",
            measurement_error_variance=(0.02, 0.025),
            psd_action="project",
        )

    assert exc.value.code == "coordinate_specific_missingness_unsupported"


def test_async_public_fitter_is_deterministic():
    trajectories = _dataset()
    first = _fit(trajectories)
    second = _fit(trajectories)

    np.testing.assert_allclose(first.eigenvalues, second.eigenvalues)
    np.testing.assert_allclose(first.eigenfunctions, second.eigenfunctions)
    np.testing.assert_allclose(first.scores, second.scores)
    np.testing.assert_allclose(first.covariance_cxy, second.covariance_cxy)
    pd.testing.assert_frame_equal(first.score_diagnostics, second.score_diagnostics)
