import numpy as np
import pytest

from eyetrajectoriespy import (
    DiscreteFrechetResult,
    TrajectorySet,
    discrete_frechet_distance,
    pairwise_discrete_frechet_distances,
)


def test_identical_sequences_have_zero_distance():
    path = np.array([[0.0, 0.0], [1.0, 0.5], [2.0, 1.0]])
    assert discrete_frechet_distance(path, path) == pytest.approx(0.0)


def test_unequal_length_hand_counted_distance_and_coupling():
    a = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    b = np.array([[0.0, 0.0], [2.0, 0.0]])

    result = discrete_frechet_distance(a, b, return_coupling=True)

    assert isinstance(result, DiscreteFrechetResult)
    assert result.distance == pytest.approx(1.0)
    np.testing.assert_array_equal(result.coupling[0], [0, 0])
    np.testing.assert_array_equal(result.coupling[-1], [2, 1])
    assert np.all(np.diff(result.coupling[:, 0]) >= 0)
    assert np.all(np.diff(result.coupling[:, 1]) >= 0)
    assert np.all(np.diff(result.coupling[:, 0]) <= 1)
    assert np.all(np.diff(result.coupling[:, 1]) <= 1)
    assert np.all(np.diff(result.coupling, axis=0).sum(axis=1) >= 1)
    assert result.distance == pytest.approx(np.max(result.local_distances))
    assert result.provenance["elapsed_time_used"] is False
    assert result.provenance["sample_order_preserved"] is True
    assert result.provenance["continuous_frechet"] is False


def test_distance_is_symmetric_even_if_coupling_is_not_unique():
    a = np.array([[0.0], [1.0], [2.0], [3.0]])
    b = np.array([[0.0], [1.5], [3.0]])
    assert discrete_frechet_distance(a, b) == pytest.approx(
        discrete_frechet_distance(b, a)
    )


def test_local_outlier_controls_discrete_frechet_bottleneck():
    a = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    b = np.array([[0.0, 0.0], [1.0, 5.0], [2.0, 0.0]])
    assert discrete_frechet_distance(a, b) == pytest.approx(5.0)


def test_dimension_weights_are_explicit_and_not_normalized():
    a = np.array([[0.0, 0.0]])
    b = np.array([[3.0, 4.0]])
    assert discrete_frechet_distance(a, b) == pytest.approx(5.0)
    assert discrete_frechet_distance(
        a,
        b,
        dimension_weights=np.array([4.0, 1.0]),
    ) == pytest.approx(np.sqrt(52.0))


def test_pairwise_matrix_respects_selected_dimensions():
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

    xy = pairwise_discrete_frechet_distances(
        trajectories,
        dimensions=("x", "y"),
    )
    all_dimensions = pairwise_discrete_frechet_distances(trajectories)

    assert xy.shape == (3, 3)
    np.testing.assert_allclose(xy, xy.T)
    np.testing.assert_allclose(np.diag(xy), 0.0)
    assert xy[0, 1] == pytest.approx(1.0)
    assert xy[0, 2] == pytest.approx(2.0)
    assert all_dimensions[0, 1] > xy[0, 1]


def test_input_contracts_fail_closed():
    valid = np.array([[0.0, 0.0], [1.0, 1.0]])

    with pytest.raises(ValueError, match="shape"):
        discrete_frechet_distance(np.array([0.0, 1.0]), valid)
    with pytest.raises(ValueError, match="same number of dimensions"):
        discrete_frechet_distance(valid, np.ones((2, 3)))
    with pytest.raises(ValueError, match="finite complete"):
        discrete_frechet_distance(valid, np.array([[0.0, np.nan]]))
    with pytest.raises(ValueError, match="one value per dimension"):
        discrete_frechet_distance(
            valid,
            valid,
            dimension_weights=np.array([1.0]),
        )
    with pytest.raises(ValueError, match="non-negative"):
        discrete_frechet_distance(
            valid,
            valid,
            dimension_weights=np.array([1.0, -1.0]),
        )
    with pytest.raises(ValueError, match="at least one positive"):
        discrete_frechet_distance(
            valid,
            valid,
            dimension_weights=np.array([0.0, 0.0]),
        )
    with pytest.raises(TypeError, match="boolean"):
        discrete_frechet_distance(valid, valid, return_coupling=1)


def test_pairwise_weights_are_validated_with_single_curve():
    trajectories = TrajectorySet(
        time=np.array([0.0, 1.0]),
        values=np.zeros((1, 2, 2)),
        curve_ids=("a",),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )
    with pytest.raises(ValueError, match="one value per dimension"):
        pairwise_discrete_frechet_distances(
            trajectories,
            dimension_weights=np.array([1.0]),
        )


def test_pairwise_dimension_contracts_fail_closed():
    trajectories = TrajectorySet(
        time=np.array([0.0, 1.0]),
        values=np.zeros((2, 2, 2)),
        curve_ids=("a", "b"),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )
    with pytest.raises(TypeError, match="non-string sequence"):
        pairwise_discrete_frechet_distances(trajectories, dimensions="x")
    with pytest.raises(ValueError, match="at least one dimension"):
        pairwise_discrete_frechet_distances(trajectories, dimensions=())
    with pytest.raises(ValueError, match="duplicates"):
        pairwise_discrete_frechet_distances(
            trajectories,
            dimensions=("x", "x"),
        )
    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        pairwise_discrete_frechet_distances(
            trajectories,
            dimensions=("x", "missing"),
        )
