import numpy as np
import pytest

from eyetrajectoriespy import (
    DynamicTimeWarpingResult,
    TrajectorySet,
    discrete_frechet_distance,
    dynamic_time_warping_cost,
    pairwise_dynamic_time_warping_costs,
)


def test_identical_sequences_have_zero_dtw_cost():
    path = np.array([[0.0, 0.0], [1.0, 0.5], [2.0, 1.0]])
    assert dynamic_time_warping_cost(path, path) == pytest.approx(0.0)


def test_hand_counted_unequal_length_dtw_and_path():
    a = np.array([[0.0], [1.0], [2.0]])
    b = np.array([[0.0], [2.0]])

    result = dynamic_time_warping_cost(a, b, return_path=True)

    assert isinstance(result, DynamicTimeWarpingResult)
    assert result.cost == pytest.approx(1.0)
    np.testing.assert_array_equal(result.warping_path[0], [0, 0])
    np.testing.assert_array_equal(result.warping_path[-1], [2, 1])
    assert np.all(np.diff(result.warping_path[:, 0]) >= 0)
    assert np.all(np.diff(result.warping_path[:, 1]) >= 0)
    assert np.all(np.diff(result.warping_path[:, 0]) <= 1)
    assert np.all(np.diff(result.warping_path[:, 1]) <= 1)
    assert np.all(np.diff(result.warping_path, axis=0).sum(axis=1) >= 1)
    assert result.cost == pytest.approx(np.sum(result.local_distances))
    assert result.provenance["path_length_normalization"] is False
    assert result.provenance["elapsed_time_used"] is False
    assert result.provenance["global_window"] is None
    assert result.provenance["metric_claim"] is False


def test_dtw_and_frechet_have_distinct_estimands():
    a = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    b = np.array([[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])

    assert discrete_frechet_distance(a, b) == pytest.approx(1.0)
    assert dynamic_time_warping_cost(a, b) == pytest.approx(3.0)


def test_symmetric_recurrence_gives_symmetric_raw_cost():
    a = np.array([[0.0], [1.0], [2.0], [3.0]])
    b = np.array([[0.0], [1.5], [3.0]])
    assert dynamic_time_warping_cost(a, b) == pytest.approx(
        dynamic_time_warping_cost(b, a)
    )


def test_dimension_weights_are_explicit_and_not_normalized():
    a = np.array([[0.0, 0.0]])
    b = np.array([[3.0, 4.0]])
    assert dynamic_time_warping_cost(a, b) == pytest.approx(5.0)
    assert dynamic_time_warping_cost(
        a,
        b,
        dimension_weights=np.array([4.0, 1.0]),
    ) == pytest.approx(np.sqrt(52.0))


def test_pairwise_dtw_cost_matrix_respects_selected_dimensions():
    time = np.array([0.0, 1.0, 2.0])
    values = np.array(
        [
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
            [[0.0, 0.0, 100.0], [1.0, 1.0, 100.0], [2.0, 0.0, 100.0]],
            [[0.0, 0.0, 0.0], [1.0, 2.0, 0.0], [2.0, 0.0, 0.0]],
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

    xy = pairwise_dynamic_time_warping_costs(
        trajectories,
        dimensions=("x", "y"),
    )
    all_dimensions = pairwise_dynamic_time_warping_costs(trajectories)

    assert xy.shape == (3, 3)
    np.testing.assert_allclose(xy, xy.T)
    np.testing.assert_allclose(np.diag(xy), 0.0)
    assert xy[0, 1] == pytest.approx(1.0)
    assert xy[0, 2] == pytest.approx(2.0)
    assert all_dimensions[0, 1] > xy[0, 1]


def test_dtw_input_contracts_fail_closed():
    valid = np.array([[0.0, 0.0], [1.0, 1.0]])

    with pytest.raises(ValueError, match="shape"):
        dynamic_time_warping_cost(np.array([0.0, 1.0]), valid)
    with pytest.raises(ValueError, match="same number of dimensions"):
        dynamic_time_warping_cost(valid, np.ones((2, 3)))
    with pytest.raises(ValueError, match="finite complete"):
        dynamic_time_warping_cost(valid, np.array([[0.0, np.nan]]))
    with pytest.raises(ValueError, match="one value per dimension"):
        dynamic_time_warping_cost(
            valid,
            valid,
            dimension_weights=np.array([1.0]),
        )
    with pytest.raises(ValueError, match="non-negative"):
        dynamic_time_warping_cost(
            valid,
            valid,
            dimension_weights=np.array([1.0, -1.0]),
        )
    with pytest.raises(ValueError, match="at least one positive"):
        dynamic_time_warping_cost(
            valid,
            valid,
            dimension_weights=np.array([0.0, 0.0]),
        )
    with pytest.raises(TypeError, match="boolean"):
        dynamic_time_warping_cost(valid, valid, return_path=1)


def test_pairwise_dtw_contracts_fail_closed():
    trajectories = TrajectorySet(
        time=np.array([0.0, 1.0]),
        values=np.zeros((1, 2, 2)),
        curve_ids=("a",),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )

    with pytest.raises(ValueError, match="one value per dimension"):
        pairwise_dynamic_time_warping_costs(
            trajectories,
            dimension_weights=np.array([1.0]),
        )
    with pytest.raises(TypeError, match="non-string sequence"):
        pairwise_dynamic_time_warping_costs(
            trajectories,
            dimensions="x",
        )
    with pytest.raises(ValueError, match="at least one dimension"):
        pairwise_dynamic_time_warping_costs(
            trajectories,
            dimensions=(),
        )
    with pytest.raises(ValueError, match="duplicates"):
        pairwise_dynamic_time_warping_costs(
            trajectories,
            dimensions=("x", "x"),
        )
    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        pairwise_dynamic_time_warping_costs(
            trajectories,
            dimensions=("x", "missing"),
        )
