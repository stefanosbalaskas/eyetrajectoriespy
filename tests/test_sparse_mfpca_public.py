import inspect

import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et
from eyetrajectoriespy._sparse_multivariate import (
    SparseNativeError,
    estimate_sparse_planar_mean_covariance,
    weighted_planar_covariance_eigendecomposition,
)


def _planar_sparse_dataset(rho=0.6):
    n_curves = 12
    time = np.linspace(0.0, 1.0, 17)
    phase = 2.0 * np.pi * np.arange(n_curves) / n_curves
    z = np.sqrt(2.0) * np.cos(phase)
    w = np.sqrt(2.0) * np.sin(phase)
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
    metadata = pd.DataFrame(
        {
            "participant_id": [
                f"participant-{index}" for index in range(n_curves)
            ]
        }
    )
    trajectories = et.IrregularTrajectorySet(
        time=tuple(time.copy() for _ in range(n_curves)),
        values=values,
        curve_ids=tuple(f"curve-{index}" for index in range(n_curves)),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        metadata=metadata,
        provenance={"source": "public-sparse-mfpca-test"},
    )
    return trajectories, time


def _fit(
    *,
    analysis_support_action="error",
    evaluation_grid=None,
    measurement_error="diagonal",
    measurement_error_variance=(0.05, 0.08),
    measurement_error_covariance=None,
    score_failure_action="error",
):
    trajectories, full_grid = _planar_sparse_dataset()
    grid = full_grid if evaluation_grid is None else evaluation_grid
    return et.fit_sparse_mfpca(
        trajectories,
        dimensions=("x", "y"),
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=0.30,
        covariance_bandwidth=0.35,
        measurement_error=measurement_error,
        measurement_error_variance=measurement_error_variance,
        measurement_error_covariance=measurement_error_covariance,
        analysis_support_action=analysis_support_action,
        psd_action="project",
        score_failure_action=score_failure_action,
        covariance_min_local_pairs=12,
    )


def test_public_sparse_mfpca_shapes_follow_time_before_dimension_convention():
    trajectories, grid = _planar_sparse_dataset()
    result = _fit()

    assert isinstance(result, et.SparseMFPCAResult)
    assert result.mean.shape == (grid.size, 2)
    assert result.eigenfunctions.shape == (2, grid.size, 2)
    assert result.scores.shape == (trajectories.n_curves, 2)
    assert result.mean_support_counts.shape == (grid.size, 2)
    assert result.dimensions == ("x", "y")

    internal = estimate_sparse_planar_mean_covariance(
        trajectories,
        dimensions=("x", "y"),
        evaluation_grid=grid,
        mean_bandwidth=0.30,
        covariance_bandwidth=0.35,
        psd_action="project",
        covariance_min_local_pairs=12,
    )
    eigen = weighted_planar_covariance_eigendecomposition(
        internal.covariance_blocks.matrix,
        grid,
        n_components=2,
    )

    np.testing.assert_allclose(result.mean, internal.mean.T)
    np.testing.assert_allclose(
        result.eigenfunctions,
        np.transpose(eigen.eigenfunctions, (0, 2, 1)),
    )


def test_public_result_contains_arrays_not_private_covariance_types():
    result = _fit()

    for name in (
        "smoothed_cxx",
        "smoothed_cxy",
        "smoothed_cyx",
        "smoothed_cyy",
        "covariance_cxx",
        "covariance_cxy",
        "covariance_cyx",
        "covariance_cyy",
    ):
        value = getattr(result, name)
        assert isinstance(value, np.ndarray)

    np.testing.assert_allclose(
        result.smoothed_cyx,
        result.smoothed_cxy.T,
    )
    np.testing.assert_allclose(
        result.covariance_cyx,
        result.covariance_cxy.T,
    )


def test_public_measurement_error_contract_requires_explicit_values():
    trajectories, grid = _planar_sparse_dataset()

    with pytest.raises(SparseNativeError) as exc:
        et.fit_sparse_mfpca(
            trajectories,
            n_components=1,
            evaluation_grid=grid,
            mean_bandwidth=0.30,
            covariance_bandwidth=0.35,
            measurement_error="diagonal",
            psd_action="project",
            covariance_min_local_pairs=12,
        )
    assert exc.value.code == "invalid_measurement_error_covariance"

    with pytest.raises(SparseNativeError) as exc:
        et.fit_sparse_mfpca(
            trajectories,
            n_components=1,
            evaluation_grid=grid,
            mean_bandwidth=0.30,
            covariance_bandwidth=0.35,
            measurement_error="fixed_matrix",
            psd_action="project",
            covariance_min_local_pairs=12,
        )
    assert exc.value.code == "invalid_measurement_error_covariance"


def test_fixed_measurement_error_matrix_is_retained_exactly():
    matrix = np.array(
        [
            [0.08, 0.02],
            [0.02, 0.12],
        ]
    )
    result = _fit(
        measurement_error="fixed_matrix",
        measurement_error_variance=None,
        measurement_error_covariance=matrix,
    )

    np.testing.assert_array_equal(
        result.measurement_error_covariance,
        matrix,
    )
    np.testing.assert_array_equal(
        result.provenance["sparse_mfpca"][
            "measurement_error_covariance"
        ],
        matrix,
    )
    assert result.provenance["sparse_mfpca"][
        "measurement_error_mode"
    ] == "fixed_matrix"


def test_first_public_api_omits_unimplemented_channel_weights():
    signature = inspect.signature(et.fit_sparse_mfpca)
    assert "channel_weights" not in signature.parameters
    assert "measurement_error" in signature.parameters
    assert signature.parameters["measurement_error"].default is inspect._empty


def test_restrict_scores_exact_same_retained_support_as_covariance_fit():
    trajectories, full_grid = _planar_sparse_dataset()
    grid = full_grid[3:-3]

    result = et.fit_sparse_mfpca(
        trajectories,
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=0.25,
        covariance_bandwidth=0.30,
        measurement_error="diagonal",
        measurement_error_variance=(0.05, 0.08),
        analysis_support_action="restrict",
        psd_action="project",
        covariance_min_local_pairs=12,
    )

    expected = np.array(
        [
            np.count_nonzero(
                (time >= grid[0]) & (time <= grid[-1])
            )
            for time in trajectories.time
        ]
    )
    np.testing.assert_array_equal(
        result.score_diagnostics["n_time_points"].to_numpy(),
        expected,
    )
    np.testing.assert_array_equal(
        np.asarray(
            result.provenance["sparse_mfpca"][
                "analysis_sample_counts"
            ]
        ),
        expected,
    )
    assert result.provenance["sparse_mfpca"][
        "outside_observation_count"
    ] > 0


def test_public_provenance_records_scientific_contract():
    result = _fit()
    provenance = result.provenance["sparse_mfpca"]

    assert provenance["backend"] == "native"
    assert provenance["fit_method"] == "direct_sparse_block_covariance"
    assert provenance["score_method"] == "joint_PACE"
    assert provenance["same_time_covariance_products_excluded"] is True
    assert provenance["yx_estimated_independently"] is False
    assert provenance["cross_covariance_self_symmetrized"] is False
    assert provenance["operator_storage_order"] == "channel_major"
    assert provenance["score_observation_order"] == (
        "time_major_interleaved_xy"
    )
    assert provenance["ordering_permutation_applied"] is True
    assert provenance["score_covariance_source"] == (
        "full_fitted_joint_covariance_plus_measurement_error"
    )
    assert provenance["rank_k_covariance_used_for_scoring"] is False
    assert provenance["raw_sparse_trajectory_interpolation_performed"] is False
    assert provenance["population_function_evaluation_at_native_times"] is True
    assert provenance["automatic_bandwidth_selection_performed"] is False
    assert provenance["cross_channel_covariance_modeled"] is True


def test_sparse_mfpca_score_frame_preserves_metadata():
    result = _fit()
    frame = et.sparse_mfpca_score_frame(result)

    assert list(frame.columns[:2]) == ["curve_id", "participant_id"]
    assert {"SMFPC1", "SMFPC2"} <= set(frame.columns)
    np.testing.assert_allclose(
        frame[["SMFPC1", "SMFPC2"]].to_numpy(),
        result.scores,
    )


def test_sparse_mfpca_reporting_text_states_joint_estimand_and_score_contract():
    result = _fit()
    text = et.sparse_mfpca_reporting_text(result)

    assert "Cxy was fitted directionally" in text
    assert "excluded same-time pairs" in text
    assert "full fitted joint covariance" in text
    assert "never a rank-K covariance reconstruction" in text
    assert "Measurement error used mode" in text
    assert "Raw sparse trajectories were not pre-interpolated" in text


def test_sparse_mfpca_portable_snapshot_is_complete_and_zero_loss(tmp_path):
    result = _fit()
    destination = tmp_path / "sparse-mfpca-portable"

    et.export_portable_result(
        result,
        destination,
        include_environment=False,
    )
    loaded = et.load_portable_result(destination)

    assert loaded.result_type.endswith(".SparseMFPCAResult")
    assert loaded.nonportable_fields == ()
    payload = loaded.payload
    assert payload["__python_type__"].endswith(".SparseMFPCAResult")

    for name in (
        "mean",
        "eigenvalues",
        "eigenfunctions",
        "smoothed_cxx",
        "smoothed_cxy",
        "smoothed_cyx",
        "smoothed_cyy",
        "covariance_cxx",
        "covariance_cxy",
        "covariance_cyx",
        "covariance_cyy",
        "measurement_error_covariance",
        "quadrature_weights",
        "mean_support_counts",
    ):
        np.testing.assert_array_equal(payload[name], getattr(result, name))

    pd.testing.assert_frame_equal(
        payload["score_diagnostics"],
        result.score_diagnostics,
    )
    pd.testing.assert_frame_equal(payload["metadata"], result.metadata)
    assert payload["curve_ids"] == result.curve_ids
    assert payload["dimensions"] == result.dimensions
    assert payload["coordinate_system"] == result.coordinate_system
    assert payload["time_unit"] == result.time_unit
    assert payload["covariance_pair_counts"] == dict(
        result.covariance_pair_counts
    )
    assert payload["provenance"]["sparse_mfpca"]["backend"] == "native"
