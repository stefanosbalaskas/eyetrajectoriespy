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


def test_default_symmetric1_preserves_033_raw_cost_contract():
    a = np.array([[0.0], [1.0], [2.0]])
    b = np.array([[0.0], [2.0]])

    result = dynamic_time_warping_distance(a, b, return_path=True)

    assert isinstance(result, DynamicTimeWarpingResult)
    assert result.distance == pytest.approx(1.0)
    assert result.raw_distance == pytest.approx(1.0)
    assert result.normalized_distance is None
    assert result.step_pattern == "symmetric1"
    assert result.normalization_denominator is None
    assert result.path_length == len(result.path)
    assert result.distance == pytest.approx(np.sum(result.local_distances))
    assert result.raw_distance == pytest.approx(
        np.sum(result.weighted_local_costs)
    )
    np.testing.assert_allclose(result.step_weights, 1.0)
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
    assert result.provenance["distance_aggregation"] == "weighted_sum"
    assert result.provenance["step_pattern"] == "symmetric1"
    assert result.provenance["normalizable"] is False
    assert result.provenance["normalization_requested"] is False


def test_symmetric2_raw_and_normalized_costs_are_auditable():
    a = np.array([[0.0], [1.0], [2.0]])
    b = np.array([[0.0], [2.0]])

    result = dynamic_time_warping_distance(
        a,
        b,
        step_pattern="symmetric2",
        return_path=True,
    )

    assert result.step_pattern == "symmetric2"
    assert result.raw_distance == pytest.approx(
        np.sum(result.weighted_local_costs)
    )
    assert result.normalization_denominator == pytest.approx(5.0)
    assert result.normalized_distance == pytest.approx(
        result.raw_distance / 5.0
    )
    assert result.distance == pytest.approx(result.raw_distance)
    assert result.provenance["normalizable"] is True
    assert np.all(np.isin(result.step_weights, [1.0, 2.0]))

    normalized = dynamic_time_warping_distance(
        a,
        b,
        step_pattern="symmetric2",
        normalize=True,
    )
    assert normalized == pytest.approx(result.normalized_distance)


def test_symmetric2_single_pair_normalization_returns_local_distance():
    a = np.array([[0.0, 0.0]])
    b = np.array([[3.0, 4.0]])

    audit = dynamic_time_warping_distance(
        a,
        b,
        step_pattern="symmetric2",
        normalize=True,
        return_path=True,
    )

    assert audit.raw_distance == pytest.approx(10.0)
    assert audit.normalization_denominator == pytest.approx(2.0)
    assert audit.normalized_distance == pytest.approx(5.0)
    assert audit.distance == pytest.approx(5.0)
    np.testing.assert_allclose(audit.step_weights, [2.0])
    np.testing.assert_allclose(audit.weighted_local_costs, [10.0])


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


def test_weighted_euclidean_local_cost_is_not_silently_normalized():
    a = np.array([[0.0, 0.0]])
    b = np.array([[3.0, 4.0]])
    assert dynamic_time_warping_distance(a, b) == pytest.approx(5.0)
    assert dynamic_time_warping_distance(
        a,
        b,
        dimension_weights=np.array([4.0, 1.0]),
    ) == pytest.approx(np.sqrt(52.0))


@pytest.mark.parametrize("step_pattern", ["symmetric1", "symmetric2"])
def test_dtw_is_symmetric_for_supported_symmetric_step_patterns(step_pattern):
    a = np.array([[0.0], [0.5], [2.0], [3.0]])
    b = np.array([[0.0], [1.0], [3.0]])
    assert dynamic_time_warping_distance(
        a,
        b,
        step_pattern=step_pattern,
    ) == pytest.approx(
        dynamic_time_warping_distance(
            b,
            a,
            step_pattern=step_pattern,
        )
    )


def test_pairwise_matrix_respects_dimensions_window_and_normalization():
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
    normalized = pairwise_dynamic_time_warping_distances(
        trajectories,
        dimensions=("x", "y"),
        step_pattern="symmetric2",
        normalize=True,
    )
    all_dimensions = pairwise_dynamic_time_warping_distances(trajectories)

    np.testing.assert_allclose(xy, xy.T)
    np.testing.assert_allclose(np.diag(xy), 0.0)
    np.testing.assert_allclose(normalized, normalized.T)
    np.testing.assert_allclose(np.diag(normalized), 0.0)
    assert xy[0, 1] == pytest.approx(0.0)
    assert normalized[0, 1] == pytest.approx(0.0)
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
    with pytest.raises(TypeError, match="step_pattern must be a string"):
        dynamic_time_warping_distance(valid, valid, step_pattern=1)
    with pytest.raises(ValueError, match="symmetric1.*symmetric2"):
        dynamic_time_warping_distance(valid, valid, step_pattern="bad")
    with pytest.raises(TypeError, match="normalize must be boolean"):
        dynamic_time_warping_distance(valid, valid, normalize=1)
    with pytest.raises(ValueError, match="only.*symmetric2"):
        dynamic_time_warping_distance(valid, valid, normalize=True)
    with pytest.raises(TypeError, match="return_path must be boolean"):
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
    with pytest.raises(ValueError, match="only.*symmetric2"):
        pairwise_dynamic_time_warping_distances(
            trajectories,
            normalize=True,
        )
