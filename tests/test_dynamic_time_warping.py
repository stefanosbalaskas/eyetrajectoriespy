import numpy as np
import pytest

from eyetrajectoriespy import (
    DynamicTimeWarpingResult,
    TrajectorySet,
    dynamic_time_warping_distance,
    pairwise_dynamic_time_warping_distances,
)


def test_identical_sequences_have_zero_dtw():
    path = np.array([[0.0, 0.0], [1.0, 0.5], [2.0, 1.0]])
    assert dynamic_time_warping_distance(path, path) == pytest.approx(0.0)


def test_hand_counted_unequal_length_path_and_cost():
    a = np.array([[0.0], [1.0], [2.0]])
    b = np.array([[0.0], [2.0]])

    result = dynamic_time_warping_distance(a, b, return_path=True)

    assert isinstance(result, DynamicTimeWarpingResult)
    assert result.distance == pytest.approx(1.0)
    assert result.path_length == len(result.path)
    assert result.distance == pytest.approx(np.sum(result.local_distances))
    assert result.mean_local_distance == pytest.approx(
        np.mean(result.local_distances)
    )
    np.testing.assert_array_equal(result.path[0], [0, 0])
    np.testing.assert_array_equal(result.path[-1], [2, 1])
    assert np.all(np.diff(result.path[:, 0]) >= 0)
    assert np.all(np.diff(result.path[:, 1]) >= 0)
    assert np.all(np.diff(result.path[:, 0]) <= 1)
    assert np.all(np.diff(result.path[:, 1]) <= 1)
    assert np.all(np.diff(result.path, axis=0).sum(axis=1) >= 1)
    assert result.provenance["recorded_time_used"] is False
    assert result.provenance["distance_aggregation"] == "sum"
    assert result.provenance["normalized_distance"] is False


def test_unconstrained_dtw_can_remove_index_shift_but_zero_window_cannot():
    a = np.array([[0.0], [0.0], [1.0]])
    b = np.array([[0.0], [1.0], [1.0]])

    assert dynamic_time_warping_distance(a, b) == pytest.approx(0.0)
    assert dynamic_time_warping_distance(
        a,
        b,
        window_radius=0,
    ) == pytest.approx(1.0)


def test_sakoe_chiba_window_requires_reachable_endpoint():
    a = np.zeros((5, 1))
    b = np.zeros((2, 1))
    with pytest.raises(ValueError, match="too small to connect"):
        dynamic_time_warping_distance(a, b, window_radius=2)


def test_weighted_euclidean_local_cost_is_not_normalized():
    a = np.array([[0.0, 0.0]])
    b = np.array([[3.0, 4.0]])
    assert dynamic_time_warping_distance(a, b) == pytest.approx(5.0)
    assert dynamic_time_warping_distance(
        a,
        b,
        dimension_weights=np.array([4.0, 1.0]),
    ) == pytest.approx(np.sqrt(52.0))


def test_dtw_is_symmetric_for_symmetric_step_pattern():
    a = np.array([[0.0], [0.5], [2.0], [3.0]])
    b = np.array([[0.0], [1.0], [3.0]])
    assert dynamic_time_warping_distance(a, b) == pytest.approx(
        dynamic_time_warping_distance(b, a)
    )


def test_pairwise_matrix_respects_dimensions_and_window():
    time = np.array([0.0, 1.0, 2.0])
    values = np.array(
        [
            [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            [[0.0, 0.0, 100.0], [1.0, 0.0, 100.0], [1.0, 0.0, 100.0]],
            [[0.0, 0.0, 0.0], [0.0, 2.0, 0.0], [1.0, 0.0, 0.0]],
        ]
    )
    trajectories = TrajectorySet(
        time=time,
        values=values,
        curve_ids=("a", "b", "c"),
        dimension_names=("x", "y", "z"),
        coordinate_system="normalized",
        time_unit="s",
    )

    xy = pairwise_dynamic_time_warping_distances(
        trajectories,
        dimensions=("x", "y"),
    )
    diagonal_only = pairwise_dynamic_time_warping_distances(
        trajectories,
        dimensions=("x", "y"),
        window_radius=0,
    )
    all_dimensions = pairwise_dynamic_time_warping_distances(trajectories)

    np.testing.assert_allclose(xy, xy.T)
    np.testing.assert_allclose(np.diag(xy), 0.0)
    assert xy[0, 1] == pytest.approx(0.0)
    assert diagonal_only[0, 1] == pytest.approx(1.0)
    assert all_dimensions[0, 1] > xy[0, 1]


def test_input_contracts_fail_closed():
    valid = np.array([[0.0, 0.0], [1.0, 1.0]])

    with pytest.raises(ValueError, match="shape"):
        dynamic_time_warping_distance(np.array([0.0, 1.0]), valid)
    with pytest.raises(ValueError, match="same number of dimensions"):
        dynamic_time_warping_distance(valid, np.ones((2, 3)))
    with pytest.raises(ValueError, match="finite complete"):
        dynamic_time_warping_distance(valid, np.array([[0.0, np.nan]]))
    with pytest.raises(ValueError, match="one value per dimension"):
        dynamic_time_warping_distance(
            valid,
            valid,
            dimension_weights=np.array([1.0]),
        )
    with pytest.raises(ValueError, match="non-negative"):
        dynamic_time_warping_distance(
            valid,
            valid,
            dimension_weights=np.array([1.0, -1.0]),
        )
    with pytest.raises(ValueError, match="at least one positive"):
        dynamic_time_warping_distance(
            valid,
            valid,
            dimension_weights=np.array([0.0, 0.0]),
        )
    with pytest.raises(TypeError, match="integer or None"):
        dynamic_time_warping_distance(valid, valid, window_radius=1.5)
    with pytest.raises(TypeError, match="integer or None"):
        dynamic_time_warping_distance(valid, valid, window_radius=True)
    with pytest.raises(ValueError, match="non-negative"):
        dynamic_time_warping_distance(valid, valid, window_radius=-1)
    with pytest.raises(TypeError, match="boolean"):
        dynamic_time_warping_distance(valid, valid, return_path=1)


def test_pairwise_contracts_fail_closed_even_with_one_curve():
    trajectories = TrajectorySet(
        time=np.array([0.0, 1.0]),
        values=np.zeros((1, 2, 2)),
        curve_ids=("a",),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )

    with pytest.raises(ValueError, match="one value per dimension"):
        pairwise_dynamic_time_warping_distances(
            trajectories,
            dimension_weights=np.array([1.0]),
        )
    with pytest.raises(TypeError, match="non-string sequence"):
        pairwise_dynamic_time_warping_distances(
            trajectories,
            dimensions="x",
        )
    with pytest.raises(ValueError, match="at least one dimension"):
        pairwise_dynamic_time_warping_distances(
            trajectories,
            dimensions=(),
        )
    with pytest.raises(ValueError, match="duplicates"):
        pairwise_dynamic_time_warping_distances(
            trajectories,
            dimensions=("x", "x"),
        )
    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        pairwise_dynamic_time_warping_distances(
            trajectories,
            dimensions=("missing",),
        )
