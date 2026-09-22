import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import TrajectorySet, validate_no_long_missing_runs, validate_simplex, validate_trajectory_set

def base_set():
    return TrajectorySet(
        time=np.array([0.0, 0.5, 1.0]),
        values=np.arange(12, dtype=float).reshape(2, 3, 2),
        curve_ids=("a", "b"),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": ["p1", "p2"]}),
        coordinate_system="pixels",
        time_unit="s",
    )

def test_trajectory_properties_and_dimension():
    x = base_set()
    assert (x.n_curves, x.n_time, x.n_dimensions) == (2, 3, 2)
    assert x.dimension("x").shape == (2, 3)
    with pytest.raises(KeyError):
        x.dimension("z")

def test_trajectory_rejects_bad_shapes_and_time():
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0, 0]), np.zeros((1, 2, 1)), ("a",), ("x",))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0, 1]), np.zeros((2, 1)), ("a",), ("x",))
    with pytest.raises(ValueError):
        TrajectorySet(np.array([0, 1]), np.zeros((1, 2, 1)), ("a", "b"), ("x",))

def test_subset_and_with_values_preserve_contract():
    x = base_set()
    y = x.subset([1])
    assert y.curve_ids == ("b",)
    z = y.with_values(y.values + 1, provenance_update={"step": "plus_one"})
    assert z.provenance["step"] == "plus_one"
    assert np.allclose(z.values, y.values + 1)

def test_validation_coordinate_and_complete():
    x = base_set()
    validate_trajectory_set(x, require_complete=True, require_dimensions=["x"])
    bad = TrajectorySet(x.time, x.values, x.curve_ids, x.dimension_names, x.metadata.reset_index(drop=True), "weird")
    with pytest.raises(ValueError):
        validate_trajectory_set(bad)
    values = x.values.copy(); values[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        validate_trajectory_set(x.with_values(values), require_complete=True)

def test_simplex_validation():
    validate_simplex(np.array([[[0.2, 0.8], [0.6, 0.4]]]))
    with pytest.raises(ValueError):
        validate_simplex(np.array([[[0.2, 0.9]]]))
    with pytest.raises(ValueError):
        validate_simplex(np.array([[0.2, 0.8]]))

def test_missing_fraction_validation():
    x = base_set()
    values = x.values.copy(); values[0, :2, 0] = np.nan
    missing = x.with_values(values)
    with pytest.raises(ValueError):
        validate_no_long_missing_runs(missing, max_missing_fraction=0.5)
    validate_no_long_missing_runs(missing, max_missing_fraction=0.9)
    with pytest.raises(ValueError):
        validate_no_long_missing_runs(missing, max_missing_fraction=1.0)


def test_rqa_metric_coordinate_system_is_valid():
    x = base_set()
    derived = x.with_values(
        x.values,
        coordinate_system="rqa_metrics",
    )
    validate_trajectory_set(derived, require_complete=True)
