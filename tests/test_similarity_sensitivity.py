import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectoryDistanceSensitivityResult,
    TrajectorySet,
    discrete_frechet_distance,
    dynamic_time_warping_distance,
    functional_l2_distance,
    plot_trajectory_distance_rank_correlations,
    trajectory_distance_comparison_frame,
    trajectory_distance_neighbor_frame,
    trajectory_distance_sensitivity,
    trajectory_distance_sensitivity_reporting_text,
)


def _trajectory_set():
    time = np.linspace(0.0, 1.0, 7)
    curves = np.array(
        [
            [0.0, 0.1, 0.4, 0.9, 1.5, 2.2, 3.0],
            [0.0, 0.0, 0.1, 0.4, 0.9, 1.5, 2.2],
            [0.0, 0.2, 0.8, 1.4, 1.9, 2.4, 2.8],
            [3.0, 2.4, 1.8, 1.1, 0.6, 0.2, 0.0],
        ],
        dtype=float,
    )
    values = np.stack(
        [
            np.column_stack([curve, 0.35 * curve**2])
            for curve in curves
        ]
    )
    return TrajectorySet(
        time=time,
        values=values,
        curve_ids=("A", "B", "C", "D"),
        dimension_names=("x", "y"),
        coordinate_system="unknown",
        time_unit="s",
    )


def _specifications():
    return (
        {"name": "l2", "method": "functional_l2"},
        {"name": "frechet", "method": "discrete_frechet"},
        {
            "name": "dtw_norm",
            "method": "dtw",
            "step_pattern": "symmetric2",
            "normalize": True,
            "window_radius": None,
        },
    )


def test_distance_sensitivity_retains_all_native_distance_contracts():
    trajectories = _trajectory_set()
    result = trajectory_distance_sensitivity(
        trajectories,
        _specifications(),
        dimensions=("x", "y"),
        dimension_weights=(1.0, 0.5),
        neighbor_k=2,
    )

    assert isinstance(result, TrajectoryDistanceSensitivityResult)
    assert result.n_specifications == 3
    assert result.n_curves == 4
    assert result.distance_matrices.shape == (3, 4, 4)
    assert result.neighbor_orders.shape == (3, 4, 2)
    assert result.neighbor_cutoff_ties.shape == (3, 4)
    assert result.specification_names == ("l2", "frechet", "dtw_norm")
    assert result.dimensions == ("x", "y")
    np.testing.assert_allclose(result.dimension_weights, [1.0, 0.5])

    for matrix in result.distance_matrices:
        np.testing.assert_allclose(matrix, matrix.T)
        np.testing.assert_allclose(np.diag(matrix), 0.0)
        assert np.all(np.isfinite(matrix))

    a = trajectories.values[0]
    b = trajectories.values[1]
    expected_l2 = functional_l2_distance(
        a,
        b,
        time=trajectories.time,
        dimension_weights=np.array([1.0, 0.5]),
    )
    expected_frechet = discrete_frechet_distance(
        a,
        b,
        dimension_weights=np.array([1.0, 0.5]),
    )
    expected_dtw = dynamic_time_warping_distance(
        a,
        b,
        dimension_weights=np.array([1.0, 0.5]),
        step_pattern="symmetric2",
        normalize=True,
    )
    assert result.distance_matrices[0, 0, 1] == pytest.approx(expected_l2)
    assert result.distance_matrices[1, 0, 1] == pytest.approx(expected_frechet)
    assert result.distance_matrices[2, 0, 1] == pytest.approx(expected_dtw)

    assert len(result.pairwise_distance_table) == 3 * 6
    assert len(result.comparison_table) == 3
    assert len(result.neighbor_overlap_table) == 3 * 4

    assert set(
        [
            "spearman_rank_correlation",
            "pearson_raw_distance_correlation",
            "mean_absolute_rank_difference",
            "mean_top_k_neighbor_jaccard",
            "nearest_neighbor_identity_agreement_fraction",
            "any_neighbor_cutoff_tie",
        ]
    ) <= set(result.comparison_table.columns)
    assert np.all(
        result.comparison_table["mean_top_k_neighbor_jaccard"]
        .between(0.0, 1.0)
    )
    assert np.all(
        result.comparison_table[
            "nearest_neighbor_identity_agreement_fraction"
        ].between(0.0, 1.0)
    )

    contract = result.provenance["trajectory_distance_sensitivity"]
    assert contract["distance_matrix_standardization"] is False
    assert contract["distance_matrix_rescaling"] is False
    assert contract["consensus_distance_constructed"] is False
    assert contract["preferred_metric_selected"] is False
    assert contract["correlation_p_values_computed"] is False
    assert contract["pairwise_distances_treated_as_independent"] is False


def test_distance_sensitivity_detects_local_neighbor_cutoff_ties():
    time = np.array([0.0, 1.0, 2.0])
    values = np.array(
        [
            [[0.0], [0.0], [0.0]],
            [[1.0], [1.0], [1.0]],
            [[-1.0], [-1.0], [-1.0]],
        ]
    )
    trajectories = TrajectorySet(
        time=time,
        values=values,
        curve_ids=("center", "positive", "negative"),
        dimension_names=("x",),
        coordinate_system="unknown",
        time_unit="s",
    )
    result = trajectory_distance_sensitivity(
        trajectories,
        (
            {"name": "l2", "method": "functional_l2"},
            {"name": "frechet", "method": "discrete_frechet"},
        ),
        neighbor_k=1,
    )

    assert bool(result.neighbor_cutoff_ties[0, 0])
    assert bool(result.neighbor_cutoff_ties[1, 0])
    assert bool(result.comparison_table.loc[0, "any_neighbor_cutoff_tie"])


def test_distance_sensitivity_frames_plot_and_reporting():
    result = trajectory_distance_sensitivity(
        _trajectory_set(),
        _specifications(),
        neighbor_k=2,
    )

    comparison = trajectory_distance_comparison_frame(result)
    neighbors = trajectory_distance_neighbor_frame(result)
    assert comparison.equals(result.comparison_table)
    assert neighbors.equals(result.neighbor_overlap_table)

    ax = plot_trajectory_distance_rank_correlations(result)
    assert "rank agreement" in ax.get_title()
    assert len(ax.images) == 1
    plt.close(ax.figure)

    text = trajectory_distance_sensitivity_reporting_text(result)
    assert "Trajectory-similarity robustness" in text
    assert "no standardization" in text
    assert "not p-values" in text
    assert "best" in text


def test_distance_sensitivity_rejects_implicit_or_invalid_choices():
    trajectories = _trajectory_set()

    with pytest.raises(ValueError, match="at least two"):
        trajectory_distance_sensitivity(
            trajectories,
            ({"name": "l2", "method": "functional_l2"},),
        )

    with pytest.raises(ValueError, match="unique"):
        trajectory_distance_sensitivity(
            trajectories,
            (
                {"name": "same", "method": "functional_l2"},
                {"name": "same", "method": "discrete_frechet"},
            ),
        )

    with pytest.raises(ValueError, match="unsupported DTW options"):
        trajectory_distance_sensitivity(
            trajectories,
            (
                {"name": "l2", "method": "functional_l2"},
                {
                    "name": "dtw",
                    "method": "dtw",
                    "automatic_window": True,
                },
            ),
        )

    with pytest.raises(ValueError, match="not supported"):
        trajectory_distance_sensitivity(
            trajectories,
            (
                {
                    "name": "l2",
                    "method": "functional_l2",
                    "normalize": True,
                },
                {"name": "frechet", "method": "discrete_frechet"},
            ),
        )

    with pytest.raises(ValueError, match="neighbor_k"):
        trajectory_distance_sensitivity(
            trajectories,
            _specifications(),
            neighbor_k=trajectories.n_curves,
        )

    with pytest.raises(ValueError, match="one value per selected dimension"):
        trajectory_distance_sensitivity(
            trajectories,
            _specifications(),
            dimensions=("x", "y"),
            dimension_weights=(1.0,),
        )

    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        trajectory_distance_sensitivity(
            trajectories,
            _specifications(),
            dimensions=("x", "z"),
        )


def test_distance_sensitivity_helpers_validate_result_type():
    with pytest.raises(TypeError, match="TrajectoryDistanceSensitivityResult"):
        trajectory_distance_comparison_frame(object())
    with pytest.raises(TypeError, match="TrajectoryDistanceSensitivityResult"):
        trajectory_distance_neighbor_frame(object())
    with pytest.raises(TypeError, match="TrajectoryDistanceSensitivityResult"):
        plot_trajectory_distance_rank_correlations(object())
    with pytest.raises(TypeError, match="TrajectoryDistanceSensitivityResult"):
        trajectory_distance_sensitivity_reporting_text(object())
