import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    discrete_frechet_distance,
    pairwise_discrete_frechet_distances,
)


def _set(values, *, names=("x", "y")):
    array = np.asarray(values, dtype=float)
    if array.ndim == 2:
        array = array[None, :, :]
    return TrajectorySet(
        time=np.arange(array.shape[1], dtype=float),
        values=array,
        curve_ids=tuple(f"c{i}" for i in range(array.shape[0])),
        dimension_names=names,
        time_unit="samples",
        coordinate_system="normalized",
    )


def test_discrete_frechet_zero_for_identical_curve_and_symmetric():
    a = np.asarray([[0.0, 0.0], [1.0, 0.2], [2.0, 0.0]])
    assert discrete_frechet_distance(a, a) == pytest.approx(0.0)

    b = np.asarray([[0.0, 1.0], [1.0, 1.2], [2.0, 1.0]])
    ab = discrete_frechet_distance(a, b)
    ba = discrete_frechet_distance(b, a)
    assert ab == pytest.approx(ba)
    assert ab == pytest.approx(1.0)


def test_discrete_frechet_preserves_order_but_allows_monotone_progression():
    dense = np.asarray([[0.0], [1.0], [2.0]])
    sparse = np.asarray([[0.0], [2.0]])
    reversed_path = np.asarray([[2.0], [1.0], [0.0]])

    assert discrete_frechet_distance(dense, sparse) == pytest.approx(1.0)
    assert discrete_frechet_distance(dense, reversed_path) == pytest.approx(2.0)


def test_discrete_frechet_uses_explicit_weighted_euclidean_point_metric():
    a = np.asarray([[0.0, 0.0]])
    b = np.asarray([[3.0, 4.0]])

    assert discrete_frechet_distance(a, b) == pytest.approx(5.0)
    assert discrete_frechet_distance(
        a,
        b,
        dimension_weights=(4.0, 1.0),
    ) == pytest.approx(np.sqrt(52.0))


def test_discrete_frechet_validates_shape_finiteness_and_weights():
    a = np.asarray([[0.0, 0.0], [1.0, 1.0]])

    with pytest.raises(ValueError, match="shape"):
        discrete_frechet_distance(np.asarray([0.0, 1.0]), a)
    with pytest.raises(ValueError, match="same number of dimensions"):
        discrete_frechet_distance(a, np.zeros((2, 3)))
    with pytest.raises(ValueError, match="finite"):
        bad = a.copy()
        bad[0, 0] = np.nan
        discrete_frechet_distance(bad, a)
    with pytest.raises(ValueError, match="one value per compared dimension"):
        discrete_frechet_distance(a, a, dimension_weights=(1.0,))
    with pytest.raises(ValueError, match="strictly positive"):
        discrete_frechet_distance(a, a, dimension_weights=(1.0, 0.0))
    with pytest.raises(ValueError, match="strictly positive"):
        discrete_frechet_distance(a, a, dimension_weights=(1.0, np.inf))


def test_pairwise_discrete_frechet_is_symmetric_with_zero_diagonal():
    source = _set(
        np.asarray(
            [
                [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
                [[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]],
                [[0.0, 0.0], [1.0, 0.5], [2.0, 0.0]],
            ]
        )
    )
    matrix = pairwise_discrete_frechet_distances(source)

    assert matrix.shape == (3, 3)
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), 0.0)
    assert matrix[0, 1] == pytest.approx(1.0)


def test_pairwise_discrete_frechet_dimension_selection_is_explicit():
    source = _set(
        np.asarray(
            [
                [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
                [[0.0, 5.0], [1.0, 5.0], [2.0, 5.0]],
            ]
        )
    )

    all_dimensions = pairwise_discrete_frechet_distances(source)
    x_only = pairwise_discrete_frechet_distances(source, dimensions=("x",))

    assert all_dimensions[0, 1] == pytest.approx(5.0)
    assert x_only[0, 1] == pytest.approx(0.0)

    with pytest.raises(TypeError, match="non-string"):
        pairwise_discrete_frechet_distances(source, dimensions="x")
    with pytest.raises(ValueError, match="at least one"):
        pairwise_discrete_frechet_distances(source, dimensions=())
    with pytest.raises(ValueError, match="duplicates"):
        pairwise_discrete_frechet_distances(source, dimensions=("x", "x"))
    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        pairwise_discrete_frechet_distances(source, dimensions=("z",))


def test_pairwise_discrete_frechet_requires_complete_trajectories():
    source = _set(
        np.asarray(
            [
                [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
                [[0.0, 1.0], [np.nan, 1.0], [2.0, 1.0]],
            ]
        )
    )
    with pytest.raises(ValueError, match="missing values"):
        pairwise_discrete_frechet_distances(source)
